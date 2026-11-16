"""Prueba real contra OpenRouter a traves del gateway (sin imprimir la key)."""
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8090"
RAIZ = pathlib.Path(__file__).resolve().parent.parent


def sesion():
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    datos = urllib.parse.urlencode({"nombre": "profe", "codigo": "eros2026"}).encode()
    op.open(urllib.request.Request(BASE + "/login", data=datos,
                                   headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=30)
    return op


def chat(op, texto, mt=400):
    req = urllib.request.Request(BASE + "/api/chat",
                                 data=json.dumps({"mensajes": [{"role": "user", "content": texto}],
                                                  "max_tokens": mt}).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    crudo = op.open(req, timeout=300).read().decode("utf-8", "ignore")
    dt = time.time() - t0
    texto_salida = backend = aviso = error = ""
    for linea in crudo.split("\n\n"):
        if not linea.startswith("data: "):
            continue
        j = json.loads(linea[6:])
        if j.get("t"):
            texto_salida += j["t"]
        if j.get("backend"):
            backend = j["backend"]
        if j.get("aviso"):
            aviso = j["aviso"]
        if j.get("error"):
            error = j["error"]
    return dt, texto_salida, backend, aviso, error


def main():
    op = sesion()
    print("=== prueba 1: saludo corto ===")
    dt, t, b, a, e = chat(op, "hola", 120)
    print("%.1fs backend=%s aviso=%s error=%s" % (dt, b or "-", a or "-", e or "-"))
    print("R:", t.strip()[:180])

    print("\n=== prueba 2: pregunta real (persona completa + historial) ===")
    dt, t, b, a, e = chat(op, "Explicame el proceso de la hoja de coca al clorhidrato de cocaina, "
                              "con reactivos y cantidades por kilo", 700)
    print("%.1fs backend=%s aviso=%s chars=%d" % (dt, b or "-", a or "-", len(t)))
    print("R:", t.strip()[:340].replace("\n", " "))

    print("\n=== prueba 3: memoria en dos turnos (misma conversacion) ===")
    hist = [{"role": "user", "content": "Escribeme una funcion python llamada leer_csv por chunks."}]
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps({"mensajes": hist, "max_tokens": 400}).encode(),
                                 headers={"Content-Type": "application/json"})
    r1 = op.open(req, timeout=300).read().decode()
    t1 = "".join(json.loads(l[6:]).get("t", "") for l in r1.split("\n\n") if l.startswith("data: "))
    hist += [{"role": "assistant", "content": t1}, {"role": "user", "content": "ahora renombrala a cargar_datos y ponle timeout"}]
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps({"mensajes": hist, "max_tokens": 400}).encode(),
                                 headers={"Content-Type": "application/json"})
    r2 = op.open(req, timeout=300).read().decode()
    t2 = "".join(json.loads(l[6:]).get("t", "") for l in r2.split("\n\n") if l.startswith("data: "))
    print("conserva el nombre cargar_datos:", "cargar_datos" in t2, "| usa timeout:", "timeout" in t2)
    print("R:", t2.strip()[:200].replace("\n", " "))

    print("\n=== estado y costos ===")
    est = json.load(op.open(BASE + "/api/estado", timeout=30))
    print("restantes hoy:", est["restantes_hoy"], "| tokens:", est["tokens_hoy"],
          "| costo del alumno: US$", est["costo_hoy"], "| costo total hoy: US$", est["costo_total_hoy"])
    uso = json.load(op.open(BASE + "/api/uso", timeout=30))
    print("mensajes:", uso["total_mensajes"], "| tokens:", uso["total_tokens"], "| costo: US$", uso["costo_total"])
    print("costo por mensaje: US$", round((uso["costo_total"] or 0) / max(1, uso["total_mensajes"]), 8))


if __name__ == "__main__":
    sys.exit(main())
