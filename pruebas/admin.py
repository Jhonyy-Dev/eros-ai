"""Prueba del panel secreto: que sea privado, y crear/rotar/borrar alumnos."""
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8090"
RAIZ = pathlib.Path(__file__).resolve().parent.parent


def clave_admin():
    for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if l.startswith("ADMIN_CLAVE="):
            return l.split("=", 1)[1].strip()
    return ""


def sesion_alumno(nombre, codigo):
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    datos = urllib.parse.urlencode({"nombre": nombre, "codigo": codigo}).encode()
    op.open(urllib.request.Request(BASE + "/login", data=datos,
                                   headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=30)
    return op


def estado(op):
    return json.load(op.open(BASE + "/api/estado", timeout=20))


def cuerpo(op, ruta):
    return op.open(BASE + ruta, timeout=20).read().decode("utf-8", "ignore")


def ok(n, c, d=""):
    print(("  OK   " if c else "  FALLA") + "  " + n + (("  -> " + str(d)) if d else ""))
    return c


def main():
    ex = []
    vacio = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())

    print("1) el panel es privado")
    texto = cuerpo(vacio, "/panel")
    ex.append(ok("sin admin, /panel muestra el login de admin", "clave de admin" in texto))
    try:
        vacio.open(BASE + "/api/uso", timeout=20)
        ex.append(ok("/api/uso sin admin corta", False))
    except urllib.error.HTTPError as e:
        ex.append(ok("/api/uso sin admin corta", e.code == 401, e.code))

    print("2) login de admin")
    malo = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    malo.open(urllib.request.Request(BASE + "/admin/entrar", data=urllib.parse.urlencode({"clave": "mala"}).encode(),
                                     headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=20)
    ex.append(ok("clave mala no abre el panel", "rotar" not in cuerpo(malo, "/panel")))

    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    op.open(urllib.request.Request(BASE + "/admin/entrar", data=urllib.parse.urlencode({"clave": clave_admin()}).encode(),
                                   headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=20)
    texto = cuerpo(op, "/panel")
    ex.append(ok("clave correcta abre el panel", "Panel secreto de Eros" in texto and "rotar código" in texto))

    def admin_post(ruta, cuerpo_json):
        r = op.open(urllib.request.Request(BASE + ruta, data=json.dumps(cuerpo_json).encode(),
                                           headers={"Content-Type": "application/json"}), timeout=30)
        return json.load(r)

    print("3) crear alumno con codigo random desde el panel")
    lista = json.load(op.open(BASE + "/api/admin/alumnos", timeout=20))
    ex.append(ok("el panel lista alumnos (o ninguno)", isinstance(lista["alumnos"], list)))
    ex.append(ok("el panel no muestra la API key", "sk-or-" not in json.dumps(lista)))
    j = admin_post("/api/admin/alumno", {"nombre": "sofia"})
    ex.append(ok("alumno creado con codigo de 6", len(j["codigo"]) == 6, j["codigo"]))

    print("4) el alumno entra con ese codigo y ve su cuota")
    a1 = sesion_alumno("sofia", j["codigo"])
    est = estado(a1)
    ex.append(ok("sesion de sofia activa", est.get("sesion") is True and est.get("nombre") == "sofia"))
    ex.append(ok("cuota de 10 por dia", est.get("limite_dia") == 10, est.get("limite_dia")))

    print("5) rotar el codigo")
    j2 = admin_post("/api/admin/rotar", {"nombre": "sofia"})
    ex.append(ok("codigo nuevo distinto", j2["codigo"] != j["codigo"], j2["codigo"]))
    ex.append(ok("entra con el codigo nuevo", estado(sesion_alumno("sofia", j2["codigo"])).get("sesion") is True))
    ex.append(ok("el codigo viejo muere", estado(sesion_alumno("sofia", j["codigo"])).get("sesion") != True))

    print("6) borrar alumno")
    admin_post("/api/admin/borrar", {"nombre": "sofia"})
    ex.append(ok("borrado no entra", estado(sesion_alumno("sofia", j2["codigo"])).get("sesion") is False))
    linea = [l for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines() if l.startswith("ALUMNOS=")][0]
    ex.append(ok("no quedo en el .env", "sofia" not in linea, linea[:90]))
    ex.append(ok("el .env sigue bien formado", linea.count("=") == 1 and ":" in linea))

    print("7) lote de 10")
    lote = admin_post("/api/admin/lote", {"cuantos": 3, "prefijo": "prueba"})
    ex.append(ok("creo 3 de golpe", len(lote["creados"]) == 3, [c["nombre"] for c in lote["creados"]]))
    ex.append(ok("el primero puede entrar", estado(sesion_alumno(lote["creados"][0]["nombre"], lote["creados"][0]["codigo"])).get("sesion") is True))
    for c in lote["creados"]:
        admin_post("/api/admin/borrar", {"nombre": c["nombre"]})

    print("\nresultado: " + str(sum(ex)) + "/" + str(len(ex)) + " pruebas OK")
    return 0 if all(ex) else 1


if __name__ == "__main__":
    sys.exit(main())
