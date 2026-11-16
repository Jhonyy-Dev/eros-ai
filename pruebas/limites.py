"""Prueba de limites: minuto y dia. Deja el .env como estaba al terminar."""
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8090"
RAIZ = pathlib.Path(__file__).resolve().parent.parent
ENV = RAIZ / ".env"
WEB = RAIZ / "scripts" / "start-web.ps1"


def set_env(clave, valor):
    lineas = ENV.read_text(encoding="utf-8").splitlines()
    salida = []
    visto = False
    for l in lineas:
        if l.strip().startswith(clave + "="):
            salida.append(clave + "=" + str(valor))
            visto = True
        else:
            salida.append(l)
    if not visto:
        salida.append(clave + "=" + str(valor))
    ENV.write_text("\n".join(salida) + "\n", encoding="utf-8")


def reiniciar_web():
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(WEB)],
                   capture_output=True, text=True, timeout=180)


def sesion():
    galletas = urllib.request.HTTPCookieProcessor()
    return urllib.request.build_opener(galletas)


def login(op):
    datos = urllib.parse.urlencode({"nombre": "profe", "codigo": "eros2026"}).encode()
    r = op.open(urllib.request.Request(BASE + "/login", data=datos,
                                       headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=60)
    return r.status


def mandar(op, texto="hola"):
    cuerpo = json.dumps({"mensajes": [{"role": "user", "content": texto}], "max_tokens": 60}).encode()
    req = urllib.request.Request(BASE + "/api/chat", data=cuerpo, headers={"Content-Type": "application/json"})
    try:
        r = op.open(req, timeout=180)
        return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


def ok(nombre, cond, detalle=""):
    print(("  OK   " if cond else "  FALLA") + "  " + nombre + (("  -> " + str(detalle)) if detalle else ""))
    return cond


def main():
    exitos = []
    uso = RAIZ / "datos" / "uso.json"
    if uso.exists():
        uso.unlink()

    print("A) limite por minuto (1 por minuto)")
    set_env("LIMITE_MENSAJES_MINUTO", 1)
    set_env("LIMITE_MENSAJES_DIA", 5)
    reiniciar_web()
    op = sesion()
    login(op)
    s1, c1 = mandar(op, "hola uno")
    s2, c2 = mandar(op, "hola dos")
    exitos.append(ok("primero pasa", s1 == 200, s1))
    exitos.append(ok("segundo corta por minuto", s2 == 429 and "rápido" in c2, (s2, c2[:90])))

    print("B) limite por dia (1 por dia, con minuto alto)")
    uso.unlink(missing_ok=True)
    set_env("LIMITE_MENSAJES_MINUTO", 9)
    set_env("LIMITE_MENSAJES_DIA", 1)
    reiniciar_web()
    op = sesion()
    login(op)
    s1, c1 = mandar(op, "hola uno")
    s2, c2 = mandar(op, "hola dos")
    exitos.append(ok("primero pasa", s1 == 200, s1))
    exitos.append(ok("segundo corta por dia", s2 == 429 and "medianoche" in c2, (s2, c2[:90])))

    print("C) restauro los valores y reinicio")
    set_env("LIMITE_MENSAJES_MINUTO", 5)
    set_env("LIMITE_MENSAJES_DIA", 10)
    reiniciar_web()
    op = sesion()
    login(op)
    s, _ = mandar(op, "hola final")
    exitos.append(ok("vuelve a funcionar", s == 200, s))

    print("\nresultado: " + str(sum(1 for e in exitos if e)) + "/" + str(len(exitos)) + " pruebas OK")
    return 0 if all(exitos) else 1


if __name__ == "__main__":
    sys.exit(main())
