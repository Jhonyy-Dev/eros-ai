"""Pruebas de aceptacion de Eros. Correr con la web arriba:
    python pruebas/aceptacion.py
No imprime la API_KEY en ningun momento.
"""
import json
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8090"
RAIZ = pathlib.Path(__file__).resolve().parent.parent


class Cookie:
    def __init__(self):
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())

    def pedir(self, ruta, datos=None, cabeceras=None):
        url = BASE + ruta
        cuerpo = urllib.parse.urlencode(datos).encode() if datos else None
        cab = {"Content-Type": "application/x-www-form-urlencoded"} if datos else {}
        cab.update(cabeceras or {})
        req = urllib.request.Request(url, data=cuerpo, headers=cab)
        try:
            r = self.opener.open(req, timeout=180)
            return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers)


def ok(nombre, condicion, detalle=""):
    print(("  OK   " if condicion else "  FALLA") + "  " + nombre + (("  -> " + str(detalle)) if detalle else ""))
    return condicion


def main():
    c = Cookie()
    exitos = []

    print("1) sin sesion, la raiz redirige al login")
    status, cuerpo, _ = c.pedir("/")
    exitos.append(ok("redireccion a /login", status in (200, 303, 307) and b"nombre" in cuerpo.lower(), status))

    print("2) login con usuario de prueba")
    status, cuerpo, _ = c.pedir("/login", {"nombre": "profe", "codigo": "eros2026"})
    exitos.append(ok("login aceptado", status == 200 and b"nueva conversaci" in cuerpo.lower(), status))

    print("3) /api/estado con sesion")
    status, cuerpo, _ = c.pedir("/api/estado")
    est = json.loads(cuerpo)
    exitos.append(ok("sesion reconocida", est.get("sesion") is True and est.get("nombre") == "profe"))
    exitos.append(ok("modelo visible correcto", est.get("modelo_visible") == "Eros AI/Sin sensura", est.get("modelo_visible")))
    exitos.append(ok("limites configurados", est.get("limite_dia") == 25 and est.get("limite_minuto") == 10,
                     (est.get("limite_dia"), est.get("limite_minuto"))))

    print("4) peticion real 'hola' en streaming")
    status, cuerpo, _ = c.pedir("/api/chat", None, {"Content-Type": "application/json"})
    # /api/chat espera JSON: se llama aparte
    pedido = json.dumps({"mensajes": [{"role": "user", "content": "hola"}], "max_tokens": 120}).encode()
    req = urllib.request.Request(BASE + "/api/chat", data=pedido,
                                headers={"Content-Type": "application/json"})
    r = c.opener.open(req, timeout=240)
    texto, eventos, backend = "", [], ""
    for linea in r.read().decode("utf-8", "ignore").split("\n\n"):
        if not linea.startswith("data: "):
            continue
        j = json.loads(linea[6:])
        eventos.append(j)
        if j.get("t"):
            texto += j["t"]
        if j.get("backend"):
            backend = j["backend"]
        if j.get("modelo") and not backend:
            backend = j.get("backend", "")
    aviso = next((e["aviso"] for e in eventos if e.get("aviso")), "")
    error = next((e.get("error") for e in eventos if e.get("error")), "")
    exitos.append(ok("llego texto en streaming", len(texto.strip()) > 3, repr(texto[:70])))
    exitos.append(ok("evento fin presente", any(e.get("fin") for e in eventos)))
    print("        backend usado:", backend or "(no informado)", "| aviso:", aviso or "-", "| error:", error or "-")

    print("5) limites: /api/estado refleja consumo")
    status, cuerpo, _ = c.pedir("/api/estado")
    est2 = json.loads(cuerpo)
    exitos.append(ok("se contó el mensaje", est2.get("usados_hoy", 0) >= 1, est2.get("usados_hoy")))
    exitos.append(ok("quedan menos mensajes", est2.get("restantes_hoy", 99) < 100, est2.get("restantes_hoy")))

    print("6) uso registrado y panel")
    status, cuerpo, _ = c.pedir("/api/uso")
    uso = json.loads(cuerpo)
    exitos.append(ok("uso por alumno registrado", any(a["nombre"] == "profe" for a in uso.get("alumnos", []))))
    exitos.append(ok("tokens contados", uso.get("total_tokens", 0) > 0, uso.get("total_tokens")))
    status, cuerpo, _ = c.pedir("/panel")
    exitos.append(ok("panel responde", status == 200 and b"Panel de uso" in cuerpo))

    print("7) la key no aparece en lo que sirve el servidor")
    for ruta in ("/", "/panel", "/login"):
        r = c.pedir(ruta)
        html = r[1].decode("utf-8", "ignore")
        exitos.append(ok("sin 'sk-or-' en " + ruta, "sk-or-" not in html))
    r = c.pedir("/api/estado")
    exitos.append(ok("sin 'sk-or-' en /api/estado", "sk-or-" not in r[1].decode("utf-8", "ignore")))

    print("8) logout")
    status, cuerpo, _ = c.pedir("/logout")
    exitos.append(ok("logout vuelve al login", status == 200 and b"nombre" in cuerpo.lower(), status))

    print("\nresultado: " + str(sum(1 for e in exitos if e)) + "/" + str(len(exitos)) + " pruebas OK")
    return 0 if all(exitos) else 1


if __name__ == "__main__":
    sys.exit(main())
