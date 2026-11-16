import json, time, datetime, pathlib

import httpx
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Header, Body
from fastapi.responses import HTMLResponse, StreamingResponse

BASE   = pathlib.Path(r"D:\LocalAI\web")
CONF   = BASE / "config.json"
USO    = BASE / "uso.json"
TUNNEL = pathlib.Path(r"D:\LocalAI\logs\tunnel.log")

conf_default = {
    "clave_acceso": "cambiar-esta-clave",
    "limite_diario_por_ip": 20,
    "tope_global_diario": 400,
    "fecha_fin": "2026-11-20T23:59:59",
    "max_tokens_defecto": 500,
    "max_tokens_tope": 800,
    "max_peticiones_en_vuelo_por_ip": 2,
    "max_mensajes_contexto": 10,
    "temperatura": 0.5,
    "upstream": "http://127.0.0.1:8099",
    "upstream_api_key": "",
}
if not CONF.exists():
    CONF.write_text(json.dumps(conf_default, indent=2, ensure_ascii=False), encoding="utf-8")
conf = json.loads(CONF.read_text(encoding="utf-8"))
for k, v in conf_default.items():
    conf.setdefault(k, v)

app = FastAPI(title="LocalAI 9B sin filtros")
en_vuelo: dict[str, int] = {}


def hoy() -> str:
    return datetime.date.today().isoformat()


def leer_uso() -> dict:
    if USO.exists():
        try:
            d = json.loads(USO.read_text(encoding="utf-8"))
        except Exception:
            d = {}
        if d.get("fecha") == hoy():
            d.setdefault("log", [])
            d.setdefault("historico", [])
            return d
        historico = d.get("historico", [])
        historico.append({"fecha": d.get("fecha"), "total": d.get("total", 0), "por_ip": d.get("por_ip", {})})
        return {"fecha": hoy(), "por_ip": {}, "total": 0, "tokens": 0, "log": [], "historico": historico[-40:]}
    return {"fecha": hoy(), "por_ip": {}, "total": 0, "tokens": 0, "log": [], "historico": []}


def guardar_uso(u: dict) -> None:
    tmp = USO.with_suffix(".tmp")
    tmp.write_text(json.dumps(u, ensure_ascii=False), encoding="utf-8")
    tmp.replace(USO)


def ip_de(req: Request) -> str:
    for h in ("cf-connecting-ip", "x-forwarded-for", "x-real-ip"):
        v = req.headers.get(h)
        if v:
            return v.split(",")[0].strip()
    return req.client.host if req.client else "?"


def clave_ok(cabecera, body) -> bool:
    esperada = conf["clave_acceso"]
    if not esperada:
        return True
    if cabecera and cabecera.strip() == esperada:
        return True
    if body and str(body.get("clave", "")).strip() == esperada:
        return True
    return False


def esta_vigente():
    fin = datetime.datetime.fromisoformat(conf["fecha_fin"])
    ahora = datetime.datetime.now()
    return (ahora <= fin), fin.strftime("%d/%m/%Y %H:%M")


def url_tunel() -> str:
    if TUNNEL.exists():
        try:
            lineas = TUNNEL.read_text(encoding="utf-8", errors="ignore").splitlines()[-500:]
            for linea in reversed(lineas):
                if "trycloudflare.com" in linea:
                    for parte in linea.replace("|", " ").split():
                        if parte.startswith("https://") and "trycloudflare.com" in parte:
                            return parte
        except Exception:
            pass
    return ""


@app.get("/", response_class=HTMLResponse)
def index():
    html = (BASE / "index.html").read_text(encoding="utf-8")
    return html.replace("__CLAVE__", conf["clave_acceso"]).replace("__URL_PUBLICA__", url_tunel())


@app.get("/panel", response_class=HTMLResponse)
def panel():
    return (BASE / "panel.html").read_text(encoding="utf-8")


@app.get("/api/estado")
def estado(req: Request):
    u = leer_uso()
    ip = ip_de(req)
    usado = u["por_ip"].get(ip, {}).get("peticiones", 0)
    vigente, fin = esta_vigente()
    return {
        "vigente": vigente, "fecha_fin": fin,
        "limite_por_ip": conf["limite_diario_por_ip"], "usado_por_ip": usado,
        "restantes_por_ip": max(0, conf["limite_diario_por_ip"] - usado),
        "total_hoy": u["total"], "tope_global": conf["tope_global_diario"],
        "restantes_global": max(0, conf["tope_global_diario"] - u["total"]),
        "tokens_hoy": u["tokens"], "en_vuelo": en_vuelo.get(ip, 0), "ip": ip,
        "clave_en_pagina": True, "upstream": conf["upstream"],
        "max_tokens_tope": conf["max_tokens_tope"], "max_tokens_defecto": conf["max_tokens_defecto"],
        "url_publica": url_tunel(),
    }


@app.get("/api/uso")
def uso():
    u = leer_uso()
    vigente, fin = esta_vigente()
    return {"fecha": u["fecha"], "total": u["total"], "tokens": u["tokens"],
            "tope_global": conf["tope_global_diario"], "vigente": vigente, "fecha_fin": fin,
            "por_ip": u["por_ip"], "ultimas": u["log"][-40:][::-1], "historico": u.get("historico", [])}


@app.post("/api/chat")
async def chat(req: Request, body: dict = Body(...), x_clave: str = Header(default="")):
    if not clave_ok(x_clave, body):
        raise HTTPException(401, "clave incorrecta")

    vigente, fin = esta_vigente()
    if not vigente:
        raise HTTPException(403, "prueba cerrada el " + fin)

    ip = ip_de(req)
    tope_ip = conf["limite_diario_por_ip"]
    en_memoria = en_vuelo.get(ip, 0)

    u = leer_uso()
    usado_ip = u["por_ip"].get(ip, {}).get("peticiones", 0)
    if usado_ip >= tope_ip:
        raise HTTPException(429, "Agotaste tus " + str(tope_ip) + " peticiones de hoy. Se reinician a medianoche.")
    if u["total"] >= conf["tope_global_diario"]:
        raise HTTPException(429, "Tope global del dia agotado. Vuelve manana.")
    if en_memoria >= conf["max_peticiones_en_vuelo_por_ip"]:
        raise HTTPException(429, "Ya tienes una respuesta en curso, espera a que termine.")

    historial = body.get("mensajes") or body.get("messages") or []
    historial = [m for m in historial if m.get("role") in ("user", "assistant") and str(m.get("content", "")).strip()]
    historial = [{"role": m["role"], "content": str(m["content"])[:6000]} for m in historial[-conf["max_mensajes_contexto"]:]]
    if not historial or historial[-1]["role"] != "user":
        raise HTTPException(400, "falta el mensaje del usuario")

    mt = int(body.get("max_tokens") or conf["max_tokens_defecto"])
    mt = max(32, min(mt, conf["max_tokens_tope"]))
    payload = {"messages": historial, "max_tokens": mt,
               "temperature": float(body.get("temperatura") or conf["temperatura"]),
               "stream": True, "stream_options": {"include_usage": True}}
    cabeceras = {"Content-Type": "application/json"}
    if conf["upstream_api_key"]:
        cabeceras["Authorization"] = "Bearer " + conf["upstream_api_key"]

    registro = u["por_ip"].setdefault(ip, {"peticiones": 0, "tokens": 0})
    registro["peticiones"] = registro.get("peticiones", 0) + 1
    registro["ultima"] = time.strftime("%Y-%m-%d %H:%M:%S")
    registro.setdefault("primera", registro["ultima"])
    u["total"] += 1
    guardar_uso(u)
    en_vuelo[ip] = en_memoria + 1

    async def generador():
        tokens = 0
        cliente = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0))
        try:
            async with cliente.stream("POST", conf["upstream"] + "/v1/chat/completions",
                                      json=payload, headers=cabeceras) as r:
                if r.status_code != 200:
                    detalle = (await r.aread()).decode("utf-8", "ignore")[:500]
                    yield "data: " + json.dumps({"error": detalle}) + "\n\n"
                    return
                async for linea in r.aiter_lines():
                    if not linea or not linea.startswith("data: "):
                        continue
                    dato = linea[6:]
                    if dato == "[DONE]":
                        break
                    try:
                        j = json.loads(dato)
                    except Exception:
                        continue
                    if j.get("usage"):
                        tokens = int(j["usage"].get("completion_tokens") or 0)
                    delta = (j.get("choices") or [{}])[0].get("delta", {}) or {}
                    trozo = delta.get("content") or ""
                    if trozo:
                        yield "data: " + json.dumps({"t": trozo}) + "\n\n"
            yield "data: {\"fin\": true}\n\n"
        except Exception as e:
            yield "data: " + json.dumps({"error": str(e)}) + "\n\n"
        finally:
            en_vuelo[ip] = max(0, en_vuelo.get(ip, 1) - 1)
            await cliente.aclose()
            if tokens:
                u2 = leer_uso()
                u2["tokens"] = u2.get("tokens", 0) + tokens
                if ip in u2["por_ip"]:
                    u2["por_ip"][ip]["tokens"] = u2["por_ip"][ip].get("tokens", 0) + tokens
                u2["log"].append({"hora": time.strftime("%Y-%m-%d %H:%M:%S"), "ip": ip, "tokens": tokens})
                guardar_uso(u2)

    return StreamingResponse(generador(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8090, log_level="warning")
