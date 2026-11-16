"""Mayusculas, clave maestra del admin y llaves: el login tiene que ser claro y tolerante."""
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8090"
RAIZ = pathlib.Path(__file__).resolve().parent.parent


def env(clave, por_defecto=""):
    for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if l.startswith(clave + "="):
            return l.split("=", 1)[1].strip()
    return por_defecto


def alumnos():
    d = {}
    for p in env("ALUMNOS").split(","):
        if ":" in p:
            n, c = p.split(":", 1)
            d[n.strip()] = c.strip()
    return d


def llaves():
    return json.loads((RAIZ / "datos" / "llaves.json").read_text(encoding="utf-8"))


def entra(alias, codigo):
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    op.open(urllib.request.Request(BASE + "/login", data=urllib.parse.urlencode({"nombre": alias, "codigo": codigo}).encode(),
                                   headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=20)
    return json.load(op.open(BASE + "/api/estado", timeout=20)).get("nombre")


def admin_op():
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    op.open(urllib.request.Request(BASE + "/admin/entrar", data=urllib.parse.urlencode(
        {"usuario": env("ADMIN_USER"), "clave": env("ADMIN_CLAVE")}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=20)
    return op


def ok(n, c, d=""):
    print(("  OK   " if c else "  FALLA") + "  " + n + (("  -> " + str(d)) if d else ""))
    return c


def main():
    ex = []
    admin = admin_op()
    tabla = alumnos()
    nombre, llave = next((k, v) for k, v in tabla.items() if k.lower() != "profe")

    print("1) alumno registrado con su llave y con el alias en mayusculas")
    ex.append(ok("entra normal", entra(nombre, llave) == nombre))
    ex.append(ok("entra con el alias en MAYUSCULAS", entra(nombre.upper(), llave) == nombre))
    ex.append(ok("entra con la llave en MAYUSCULAS", entra(nombre, llave.upper()) == nombre))
    ex.append(ok("entra todo en mayusculas", entra(nombre.upper(), llave.upper()) == nombre))

    print("2) la clave maestra del admin sirve para entrar al chat")
    usuario = env("ADMIN_USER")
    clave = env("ADMIN_CLAVE")
    ex.append(ok("admin entra con su clave", entra(usuario, clave) == usuario))
    ex.append(ok("y tambien en minusculas", entra(usuario.lower(), clave.lower()) == usuario))
    ex.append(ok("con un alias nuevo registra y entra", entra("maestro_test", clave) == "maestro_test"))

    print("3) llave libre nueva, con mayusculas")
    libre = next((c for c, v in llaves().items() if v.get("alumno") is None), None)
    ex.append(ok("hay al menos una llave libre", bool(libre), libre))
    ex.append(ok("registra alias nuevo con la llave en MAYUSCULAS", entra("nuevo_test", libre.upper()) == "nuevo_test"))
    ex.append(ok("la misma llave no sirve para otro alias", entra("otro_test", libre) is None))
    ex.append(ok("el dueno vuelve a entrar", entra("nuevo_test", libre) == "nuevo_test"))

    print("4) un codigo inventado no entra")
    ex.append(ok("codigo trucho corta", entra("nuevo_test", "zzzzzz") is None))

    print("5) limpieza")
    for n in ("maestro_test", "nuevo_test"):
        try:
            admin.open(urllib.request.Request(BASE + "/api/admin/borrar", data=json.dumps({"nombre": n}).encode(),
                                              headers={"Content-Type": "application/json"}), timeout=20)
        except urllib.error.HTTPError:
            pass
    ex.append(ok("quedaron solo los reales", set(alumnos()) <= set(tabla) | {"profe"}, sorted(alumnos())))

    print("\nresultado: " + str(sum(ex)) + "/" + str(len(ex)) + " pruebas OK")
    return 0 if all(ex) else 1


if __name__ == "__main__":
    sys.exit(main())
