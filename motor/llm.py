"""Unico lugar donde se habla con el modelo. Cambiar de proveedor no toca el chat.

Uso:
    async for ev in stream_con_respaldo(mensajes, cfg, max_tokens=4096):
        ev puede ser {"t": texto}, {"uso": {...}}, {"backend": "..."} o {"error": "..."}
"""
import asyncio
import json
import pathlib
import sys

import httpx

RAIZ = pathlib.Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from config import models  # noqa: E402


class ErrorModelo(Exception):
    def __init__(self, mensaje: str, codigo: int = 0):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


def _url_openrouter(cfg: dict) -> str:
    return cfg.get("OPENROUTER_URL") or "https://openrouter.ai/api/v1/chat/completions"


async def _pedir(cliente: httpx.AsyncClient, url: str, cabeceras: dict, cuerpo: dict):
    respuesta = await cliente.send(
        cliente.build_request("POST", url, json=cuerpo, headers=cabeceras), stream=True
    )
    if respuesta.status_code != 200:
        detalle = (await respuesta.aread()).decode("utf-8", "ignore")[:400]
        try:
            mensaje = json.loads(detalle)["error"]["message"]
        except Exception:
            mensaje = detalle or ("HTTP " + str(respuesta.status_code))
        raise ErrorModelo(mensaje, respuesta.status_code)
    return respuesta


async def _leer_sse(respuesta, con_uso: bool):
    async for linea in respuesta.aiter_lines():
        if not linea or not linea.startswith("data: "):
            continue
        dato = linea[6:]
        if dato == "[DONE]":
            break
        try:
            j = json.loads(dato)
        except Exception:
            continue
        if con_uso and j.get("usage"):
            u = j["usage"]
            yield {"uso": {"entrada": u.get("prompt_tokens", 0), "salida": u.get("completion_tokens", 0)}}
        trozo = (j.get("choices") or [{}])[0].get("delta", {}).get("content") or ""
        if trozo:
            yield {"t": trozo}


async def _stream_openrouter(cfg: dict, modelo: dict, mensajes: list, max_tokens: int):
    cabeceras = {
        "Authorization": "Bearer " + cfg["API_KEY"],
        "Content-Type": "application/json",
        "HTTP-Referer": cfg.get("HTTP_REFERER") or "https://eros.local",
        "X-Title": "Eros",
    }
    cuerpo = {
        "model": modelo["modelo_openrouter"],
        "messages": mensajes,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
        "temperature": 0.6,
    }
    if modelo.get("provider"):
        cuerpo["provider"] = modelo["provider"]
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=15.0)) as cliente:
        respuesta = await _pedir(cliente, _url_openrouter(cfg), cabeceras, cuerpo)
        async for ev in _leer_sse(respuesta, True):
            yield ev


async def _stream_local(cfg: dict, modelo: dict, mensajes: list, max_tokens: int):
    cabeceras = {"Content-Type": "application/json"}
    if cfg.get("LOCAL_KEY"):
        cabeceras["Authorization"] = "Bearer " + cfg["LOCAL_KEY"]
    cuerpo = {"messages": mensajes, "max_tokens": max_tokens, "stream": True,
              "stream_options": {"include_usage": True}, "temperature": 0.5}
    url = (cfg.get("LOCAL_URL") or "http://127.0.0.1:8099").rstrip("/") + "/v1/chat/completions"
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=8.0)) as cliente:
        respuesta = await _pedir(cliente, url, cabeceras, cuerpo)
        async for ev in _leer_sse(respuesta, True):
            yield ev


async def stream(mensajes: list, cfg: dict, modelo_id: str | None = None, max_tokens: int | None = None):
    """Stream de UN backend concreto, con un reintento ante fallo de red o 5xx."""
    modelo = models.por_id(modelo_id or cfg.get("MODELO_ACTIVO") or "deepseek-v4.1-flash")
    tope = int(max_tokens or modelo.get("max_tokens") or cfg.get("MAX_TOKENS") or 4096)
    intentos = 0
    while True:
        intentos += 1
        try:
            yield {"backend": modelo["backend"], "modelo": modelo["visible"]}
            motor = _stream_openrouter if modelo["backend"] == "openrouter" else _stream_local
            async for ev in motor(cfg, modelo, mensajes, tope):
                yield ev
            return
        except ErrorModelo as e:
            reintentable = e.codigo in (429, 500, 502, 503, 504, 524) or e.codigo == 0
            if intentos < 2 and reintentable:
                await asyncio.sleep(1.2)
                continue
            raise
        except (httpx.TransportError, httpx.TimeoutException) as e:
            if intentos < 2:
                await asyncio.sleep(1.2)
                continue
            raise ErrorModelo("sin conexión con el proveedor: " + str(e), 0)


async def stream_con_respaldo(mensajes: list, cfg: dict, modelo_id: str | None = None, max_tokens: int | None = None):
    """Igual que stream(), pero si OpenRouter falla y el respaldo esta activo, usa el modelo local."""
    modelo = models.por_id(modelo_id or cfg.get("MODELO_ACTIVO") or "deepseek-v4.1-flash")
    try:
        async for ev in stream(mensajes, cfg, modelo["id"], max_tokens):
            yield ev
        return
    except ErrorModelo as e:
        if not (cfg.get("FALLBACK_LOCAL", "true").lower() == "true" and modelo["backend"] == "openrouter"):
            yield {"error": e.mensaje, "codigo": e.codigo}
            return
        yield {"aviso": "respaldo local activo: " + e.mensaje, "codigo": e.codigo}
        try:
            async for ev in stream(mensajes, cfg, "eros-local", None):
                yield ev
        except ErrorModelo as e2:
            yield {"error": e2.mensaje, "codigo": e2.codigo}
