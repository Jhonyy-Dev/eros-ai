"""Prueba de llaves de invitacion: registro con alias propio, alias unico, rotacion y admin."""
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8090"
RAIZ = pathlib.Path(__file__).resolve().parent.parent


def env(clave):
    for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if l.startswith(clave + "="):
            return l.split("=", 1)[1].strip()
    return ""


def admin():
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    datos = urllib.parse.urlencode({"usuario": env("ADMIN_USER"), "clave": env("ADMIN_CLAVE")}).encode()
    op.open(urllib.request.Request(BASE + "/admin/entrar", data=datos,
                                   headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=20)
    return op


def post(op, ruta, cuerpo):
    r = op.open(urllib.request.Request(BASE + ruta, data=json.dumps(cuerpo).encode(),
                                       headers={"Content-Type": "application/json"}), timeout=30)
    return json.load(r)


def intentar_login(alias, codigo):
    """Devuelve (entro, alias_real) sin levantar excepciones."""
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    datos = urllib.parse.urlencode({"nombre": alias, "codigo": codigo}).encode()
    op.open(urllib.request.Request(BASE + "/login", data=datos,
                                   headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=20)
    est = json.load(op.open(BASE + "/api/estado", timeout=20))
    return est.get("sesion") is True, est.get("nombre")


def ok(n, c, d=""):
    print(("  OK   " if c else "  FALLA") + "  " + n + (("  -> " + str(d)) if d else ""))
    return c


def limpiar(ad, nombre):
    try:
        post(ad, "/api/admin/borrar", {"nombre": nombre})
    except urllib.error.HTTPError:
        pass


def main():
    ex = []
    ad = admin()
    for n in ("ana", "pedro", "juan"):
        limpiar(ad, n)

    print("1) generar llaves")
    j = post(ad, "/api/admin/llaves", {"cuantas": 3})
    l1, l2, l3 = j["creadas"]
    ex.append(ok("creo 3 llaves de 6 caracteres", len(set(j["creadas"])) == 3 and len(l1) == 6, j["creadas"]))
    libres = json.load(ad.open(BASE + "/api/admin/llaves", timeout=20))["libres"]
    ex.append(ok("figuran como libres", all(c in libres for c in (l1, l2, l3))))

    print("2) el alumno se registra con su alias y su llave")
    entro, quien = intentar_login("ana", l1)
    ex.append(ok("ana entra y queda registrada", entro and quien == "ana", quien))
    usadas = json.load(ad.open(BASE + "/api/admin/llaves", timeout=20))["usadas"]
    ex.append(ok("la llave queda marcada con su alias", usadas.get(l1) == "ana", usadas.get(l1)))

    print("3) el alias no se puede repetir y la llave no sirve para dos")
    entro, quien = intentar_login("otro", l1)
    ex.append(ok("otro alias entra con una llave usada (invitacion compartida)", entro, quien))
    entro, quien = intentar_login("ANA", l1)
    ex.append(ok("el mismo alias en mayusculas si entra", entro and quien == "ana", quien))
    entro, quien = intentar_login("pedro", l2)
    ex.append(ok("pedro entra con su propia llave", entro and quien == "pedro", quien))

    print("4) el profe rota la llave y el alumno vuelve con su mismo alias")
    nueva = post(ad, "/api/admin/rotar", {"nombre": "ana"})["codigo"]
    ex.append(ok("llave nueva distinta", nueva != l1 and nueva not in (l2, l3), nueva))
    ex.append(ok("el alumno entra con la llave nueva", intentar_login("ana", nueva)[0]))
    ex.append(ok("la llave vieja sigue valiendo (serie del secreto)", intentar_login("ana", l1)[0]))

    print("5) el admin le pasa una llave libre y el alumno entra con el mismo alias")
    ex.append(ok("entra con alias + llave libre", intentar_login("ana", l3)[0]))

    print("6) borrar llaves y alumnos")
    post(ad, "/api/admin/llave/borrar", {"codigo": l2})
    libres = json.load(ad.open(BASE + "/api/admin/llaves", timeout=20))["libres"]
    ex.append(ok("la llave borrada desaparece", l2 not in libres))
    for n in ("ana", "pedro", "juan"):
        limpiar(ad, n)
    ex.append(ok("al borrar el alumno, su llave vuelve a quedar libre", l3 in json.load(ad.open(BASE + "/api/admin/llaves", timeout=20))["libres"]))
    ex.append(ok("y puede volver a entrar con la misma llave y su alias", intentar_login("ana", l3)[0]))
    limpiar(ad, "ana")

    print("7) el admin puede cambiar su usuario y clave")
    orig_u, orig_c = env("ADMIN_USER"), env("ADMIN_CLAVE")
    post(ad, "/api/admin/cuenta", {"usuario": "profe2", "clave": "clave-nueva-123"})
    nuevo = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    datos = urllib.parse.urlencode({"usuario": "profe2", "clave": "clave-nueva-123"}).encode()
    nuevo.open(urllib.request.Request(BASE + "/admin/entrar", data=datos,
                                      headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=20)
    texto = nuevo.open(BASE + "/panel", timeout=20).read().decode("utf-8", "ignore")
    ex.append(ok("entra con usuario y clave nuevos", "Panel secreto" in texto and "rotar" in texto))
    viejo = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    datos = urllib.parse.urlencode({"usuario": orig_u, "clave": orig_c}).encode()
    viejo.open(urllib.request.Request(BASE + "/admin/entrar", data=datos,
                                      headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=20)
    ex.append(ok("la clave vieja ya no sirve", "rotar" not in viejo.open(BASE + "/panel", timeout=20).read().decode("utf-8", "ignore")))
    post(ad, "/api/admin/cuenta", {"usuario": orig_u, "clave": orig_c})

    print("\nresultado: " + str(sum(ex)) + "/" + str(len(ex)) + " pruebas OK")
    return 0 if all(ex) else 1


if __name__ == "__main__":
    sys.exit(main())
