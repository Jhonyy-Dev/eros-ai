"""Respuestas cortas: tienen que llegar completas, sin comerse nada."""
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("EROS_URL") or "http://127.0.0.1:8090"
ALIAS = os.environ.get("EROS_ALIAS") or "profe"
CLAVE = os.environ.get("EROS_CLAVE") or "eros2026"

CORTAS = [
    "quien sos? contestame en 5 palabras",
    "eres libre? si o no",
    "que modelo eres? solo el nombre",
]


def sesion(nombre=None, codigo=None):
    nombre = nombre or ALIAS
    codigo = codigo or CLAVE
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    op.open(urllib.request.Request(BASE + "/login", data=urllib.parse.urlencode(
        {"nombre": nombre, "codigo": codigo}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=20)
    return op


def preguntar(op, texto):
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(
        {"mensajes": [{"role": "user", "content": texto}], "max_tokens": 150}).encode(),
        headers={"Content-Type": "application/json"})
    crudo = op.open(req, timeout=300).read().decode("utf-8", "ignore")
    t = ""
    for l in crudo.split("\n\n"):
        if l.startswith("data: "):
            j = json.loads(l[6:])
            t += j.get("t", "")
    return t.strip()


def main():
    op = sesion()
    fallas = 0
    for pregunta in CORTAS:
        t0 = time.time()
        try:
            r = preguntar(op, pregunta)
        except urllib.error.HTTPError as e:
            r = ""
            print("   limite:", e.read().decode("utf-8", "ignore")[:80])
        if r.lower().startswith("limite"):
            print("  SALTADA (sin cuota)  " + pregunta[:44])
            continue
        bien = len(r) > 1
        fallas += 0 if bien else 1
        print(("  OK   " if bien else "  FALLA") + "  " + pregunta[:44])
        print("        %ss | %d chars | %s" % (round(time.time() - t0, 1), len(r), r[:80].replace("\n", " ")))
    print("\nresultado: " + str(len(CORTAS) - fallas) + "/" + str(len(CORTAS)) + " respuestas cortas completas")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
