"""Eros - gateway web. La key de OpenRouter vive SOLO aca.

- El navegador nunca habla con OpenRouter: habla con /api/chat de este servidor.
- La API_KEY se lee del .env y no viaja al cliente.
- Login simple por codigo de invitacion + cookie firmada (HMAC).
- Limites por alumno: mensajes por dia y por minuto.
"""
import base64
import datetime
import hashlib
import hmac
import json
import pathlib
import sys
import time

import httpx
import uvicorn
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from urllib.parse import parse_qs

RAIZ = pathlib.Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from config import models          # noqa: E402
from motor import llm              # noqa: E402

ARCHIVO_USO = RAIZ / "datos" / "uso.json"
ARCHIVO_TUNEL = RAIZ / "logs" / "tunnel.log"
PERSONA = (RAIZ / "config" / "personas" / "eros.txt").read_text(encoding="utf-8").strip()


def cargar_env() -> dict:
    cfg = {}
    archivo = RAIZ / ".env"
    if not archivo.exists():
        return cfg
    for linea in archivo.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        k, v = linea.split("=", 1)
        cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


CFG = cargar_env()
SECRETO = (CFG.get("SESSION_SECRET") or "eros-secreto").encode()
COOKIE = "eros_sesion"

app = FastAPI(title="Eros")

MENSAJES_AMABLES = {
    402: "El servicio está en mantenimiento, intenta más tarde.",
    429: "Espera un momento antes de enviar otro mensaje.",
    401: "La clave del servicio venció, avísale al profe.",
}


def alumnos() -> dict:
    """nombre -> codigo"""
    d = {}
    for par in (CFG.get("ALUMNOS") or "").split(","):
        par = par.strip()
        if not par or ":" not in par:
            continue
        nombre, codigo = par.split(":", 1)
        d[nombre.strip()] = codigo.strip()
    return d


def firmar(nombre: str) -> str:
    return hmac.new(SECRETO, nombre.encode(), hashlib.sha256).hexdigest()[:32]


def sesion(req: Request):
    galleta = req.cookies.get(COOKIE)
    if not galleta or "." not in galleta:
        return None
    try:
        b64, firma = galleta.rsplit(".", 1)
        nombre = base64.urlsafe_b64decode(b64.encode()).decode()
    except Exception:
        return None
    return nombre if hmac.compare_digest(firma, firmar(nombre)) else None


def hoy() -> str:
    return datetime.date.today().isoformat()


def ahora_min() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def leer_uso() -> dict:
    if ARCHIVO_USO.exists():
        try:
            d = json.loads(ARCHIVO_USO.read_text(encoding="utf-8"))
        except Exception:
            d = {}
    else:
        d = {}
    if d.get("fecha") != hoy():
        d = {"fecha": hoy(), "alumnos": {}, "minuto": {}, "historico": d.get("historico", [])[-60:]}
        if d["historico"] is not None and ARCHIVO_USO.exists():
            pass
    d.setdefault("alumnos", {})
    d.setdefault("minuto", {})
    d.setdefault("historico", [])
    return d


def guardar_uso(u: dict) -> None:
    ARCHIVO_USO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ARCHIVO_USO.with_suffix(".tmp")
    tmp.write_text(json.dumps(u, ensure_ascii=False), encoding="utf-8")
    tmp.replace(ARCHIVO_USO)


def url_publica() -> str:
    if ARCHIVO_TUNEL.exists():
        try:
            for linea in reversed(ARCHIVO_TUNEL.read_text(encoding="utf-8", errors="ignore").splitlines()[-400:]):
                if "trycloudflare.com" in linea:
                    for parte in linea.replace("|", " ").split():
                        if parte.startswith("https://") and "trycloudflare.com" in parte:
                            return parte
        except Exception:
            pass
    return ""


def recortar_historial(mensajes: list) -> list:
    tope_msj = int(CFG.get("MAX_MENSAJES_CONTEXTO") or 20)
    tope_tok = int(CFG.get("MAX_TOKENS_CONTEXTO") or 32000)
    limpios = [{"role": m.get("role"), "content": str(m.get("content") or "")[:12000]}
               for m in mensajes if m.get("role") in ("user", "assistant") and str(m.get("content") or "").strip()]
    limpios = limpios[-tope_msj:]
    total = 0
    salida = []
    for m in reversed(limpios):
        total += len(m["content"]) // 4
        if total > tope_tok and salida:
            break
        salida.append(m)
    return list(reversed(salida))


def comprobar_limites(u: dict, nombre: str):
    tope_dia = int(CFG.get("LIMITE_MENSAJES_DIA") or 100)
    tope_min = int(CFG.get("LIMITE_MENSAJES_MINUTO") or 10)
    usado_dia = u["alumnos"].get(nombre, {}).get("mensajes", 0)
    if usado_dia >= tope_dia:
        raise HTTPException(429, "Llegaste a tus " + str(tope_dia) + " mensajes de hoy. Se reinician a medianoche.")
    m = u["minuto"].get(nombre) or {}
    if m.get("minuto") == ahora_min() and m.get("n", 0) >= tope_min:
        raise HTTPException(429, "Vas muy rápido: máximo " + str(tope_min) + " mensajes por minuto. Espera unos segundos.")
    return tope_dia


def anotar(u: dict, nombre: str) -> None:
    reg = u["alumnos"].setdefault(nombre, {"mensajes": 0, "tokens": 0})
    reg["mensajes"] += 1
    reg["ultima"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reg.setdefault("primera", reg["ultima"])
    m = u["minuto"].setdefault(nombre, {"minuto": ahora_min(), "n": 0})
    if m.get("minuto") != ahora_min():
        m["minuto"] = ahora_min()
        m["n"] = 0
    m["n"] += 1
    guardar_uso(u)


def sumar_tokens(nombre: str, entrada: int, salida: int) -> None:
    u = leer_uso()
    reg = u["alumnos"].setdefault(nombre, {"mensajes": 0, "tokens": 0})
    reg["tokens"] = reg.get("tokens", 0) + int(entrada) + int(salida)
    reg["tokens_salida"] = reg.get("tokens_salida", 0) + int(salida)
    u["log"] = (u.get("log") or [])[-200:]
    u["log"].append({"hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     "alumno": nombre, "entrada": entrada, "salida": salida})
    guardar_uso(u)


# ---------------------------------------------------------------- paginas

@app.get("/login", response_class=HTMLResponse)
def vista_login():
    return (RAIZ / "server" / "login.html").read_text(encoding="utf-8")


@app.post("/login")
async def entrar(req: Request):
    datos = parse_qs((await req.body()).decode("utf-8", "ignore"))
    nombre = (datos.get("nombre") or [""])[0].strip()
    codigo = (datos.get("codigo") or [""])[0].strip()
    tabla = alumnos()
    encontrado = None
    for n, c in tabla.items():
        if n.lower() == nombre.lower() and c == codigo:
            encontrado = n
            break
    if not encontrado:
        return RedirectResponse("/login?error=1", status_code=303)
    r = RedirectResponse("/", status_code=303)
    galleta = base64.urlsafe_b64encode(encontrado.encode()).decode() + "." + firmar(encontrado)
    r.set_cookie(COOKIE, galleta, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return r


@app.get("/logout")
def salir():
    r = RedirectResponse("/login", status_code=303)
    r.delete_cookie(COOKIE)
    return r


@app.get("/", response_class=HTMLResponse)
def index(req: Request):
    if not sesion(req):
        return RedirectResponse("/login", status_code=303)
    html = (RAIZ / "server" / "index.html").read_text(encoding="utf-8")
    return html.replace("__URL_PUBLICA__", url_publica())


@app.get("/panel", response_class=HTMLResponse)
def panel(req: Request):
    if not sesion(req):
        return RedirectResponse("/login", status_code=303)
    return (RAIZ / "server" / "panel.html").read_text(encoding="utf-8")


# ---------------------------------------------------------------- api

@app.get("/api/estado")
def estado(req: Request):
    nombre = sesion(req)
    u = leer_uso()
    modelo = models.activo(CFG)
    tope_dia = int(CFG.get("LIMITE_MENSAJES_DIA") or 100)
    reg = u["alumnos"].get(nombre or "", {"mensajes": 0, "tokens": 0})
    return {
        "sesion": bool(nombre),
        "nombre": nombre,
        "modelo_visible": modelo["visible"],
        "backend": CFG.get("BACKEND") or "openrouter",
        "respaldo_local": (CFG.get("FALLBACK_LOCAL", "true").lower() == "true"),
        "usados_hoy": reg.get("mensajes", 0),
        "restantes_hoy": max(0, tope_dia - reg.get("mensajes", 0)),
        "limite_dia": tope_dia,
        "limite_minuto": int(CFG.get("LIMITE_MENSAJES_MINUTO") or 10),
        "tokens_hoy": reg.get("tokens", 0),
        "url_publica": url_publica(),
        "alumnos_configurados": len(alumnos()),
        "fase_api_keys": (CFG.get("ENABLE_STUDENT_API_KEYS", "false").lower() == "true"),
    }


@app.get("/api/uso")
def uso(req: Request):
    if not sesion(req):
        raise HTTPException(401, "sin sesion")
    u = leer_uso()
    orden = sorted(u["alumnos"].items(), key=lambda x: x[1].get("mensajes", 0), reverse=True)
    return {"fecha": u["fecha"], "total_mensajes": sum(v.get("mensajes", 0) for v in u["alumnos"].values()),
            "total_tokens": sum(v.get("tokens", 0) for v in u["alumnos"].values()),
            "alumnos": [{"nombre": n, **v} for n, v in orden],
            "ultimas": list(reversed((u.get("log") or [])[-60:])), "modelo": models.activo(CFG)["visible"]}


@app.get("/api/diagnostico")
def diagnostico(req: Request):
    if not sesion(req):
        raise HTTPException(401, "sin sesion")
    key = CFG.get("API_KEY") or ""
    return {
        "modelo_activo": models.activo(CFG)["id"],
        "backend": CFG.get("BACKEND"),
        "key_presente": bool(key),
        "key_largo": len(key),
        "key_prefijo": key[:14] if key else "",
        "vencido_empaquetado": False,
    }


@app.post("/api/chat")
async def chat(req: Request, body: dict = Body(...)):
    nombre = sesion(req)
    if not nombre:
        raise HTTPException(401, "sesion vencida, volvé a entrar")
    mensajes = recortar_historial(body.get("mensajes") or [])
    if not mensajes or mensajes[-1]["role"] != "user":
        raise HTTPException(400, "falta el mensaje del alumno")

    u = leer_uso()
    comprobar_limites(u, nombre)
    anotar(u, nombre)

    max_tokens = int(body.get("max_tokens") or CFG.get("MAX_TOKENS") or 4096)
    max_tokens = max(64, min(max_tokens, int(CFG.get("MAX_TOKENS") or 4096)))
    conversacion = [{"role": "system", "content": PERSONA}] + mensajes

    async def generador():
        entrada = salida = 0
        modelo_usado = ""
        try:
            async for ev in llm.stream_con_respaldo(conversacion, CFG, max_tokens=max_tokens):
                if "t" in ev:
                    yield "data: " + json.dumps({"t": ev["t"]}) + "\n\n"
                elif "backend" in ev:
                    modelo_usado = ev.get("modelo", "")
                    yield "data: " + json.dumps({"modelo": ev.get("modelo"), "backend": ev.get("backend")}) + "\n\n"
                elif "aviso" in ev:
                    yield "data: " + json.dumps({"aviso": ev["aviso"]}) + "\n\n"
                elif "uso" in ev:
                    entrada += ev["uso"].get("entrada", 0)
                    salida += ev["uso"].get("salida", 0)
                elif "error" in ev:
                    amable = MENSAJES_AMABLES.get(ev.get("codigo"), "Hubo un problema con el modelo. Intenta otra vez.")
                    yield "data: " + json.dumps({"error": amable, "detalle": ev["error"]}) + "\n\n"
            yield "data: " + json.dumps({"fin": True, "modelo": modelo_usado}) + "\n\n"
        except llm.ErrorModelo as e:
            amable = MENSAJES_AMABLES.get(e.codigo, "Hubo un problema con el modelo. Intenta otra vez.")
            yield "data: " + json.dumps({"error": amable, "detalle": e.mensaje}) + "\n\n"
        except httpx.TransportError:
            yield "data: " + json.dumps({"error": "Problema de red. Intenta otra vez."}) + "\n\n"
        finally:
            if salida or entrada:
                sumar_tokens(nombre, entrada, salida)

    return StreamingResponse(generador(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(CFG.get("PUERTO") or 8090), log_level="warning")
