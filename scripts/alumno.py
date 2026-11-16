"""Administra alumnos de Eros: agrega, lista y borra usuarios del .env.

    python scripts/alumno.py ana                # agrega a ana con codigo nuevo
    python scripts/alumno.py ana clave123       # agrega con codigo elegido
    python scripts/alumno.py --lista            # lista los alumnos
    python scripts/alumno.py --borrar ana       # lo saca
    python scripts/alumno.py --reiniciar        # reinicia la web para aplicar cambios

Al agregar, imprime la linea lista para pegar en el grupo de WhatsApp/Telegram.
"""
import pathlib
import secrets
import string
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ENV = RAIZ / ".env"
CLAVE = "ALUMNOS"


def leer_env() -> list:
    return ENV.read_text(encoding="utf-8").splitlines()


def escribir_env(lineas: list) -> None:
    ENV.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def alumnos() -> list:
    for l in leer_env():
        if l.startswith(CLAVE + "="):
            valor = l.split("=", 1)[1].strip()
            return [p for p in valor.split(",") if p.strip()]
    return []


def guardar_alumnos(lista: list) -> None:
    lineas = leer_env()
    salida, visto = [], False
    for l in lineas:
        if l.startswith(CLAVE + "="):
            salida.append(CLAVE + "=" + ",".join(lista))
            visto = True
        else:
            salida.append(l)
    if not visto:
        salida.append(CLAVE + "=" + ",".join(lista))
    escribir_env(salida)
    reiniciar()


def reiniciar() -> None:
    script = RAIZ / "scripts" / "start-web.ps1"
    print("reiniciando la web para aplicar...")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                   capture_output=True, text=True, timeout=180)


def codigo_nuevo() -> str:
    abc = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(abc) for _ in range(6))


def enlace() -> str:
    archivo = RAIZ / "url_publica.txt"
    if archivo.exists():
        for l in archivo.read_text(encoding="utf-8").splitlines():
            if l.strip().startswith("https://"):
                return l.strip()
    return "http://127.0.0.1:8090"


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0

    if args[0] == "--lista":
        lista = alumnos()
        print("alumnos configurados:", len(lista))
        for p in lista:
            nombre, _, codigo = p.partition(":")
            print("  " + nombre.ljust(16) + " codigo: " + codigo)
        print("\nenlace del chat:", enlace())
        return 0

    if args[0] == "--borrar":
        if len(args) < 2:
            print("falta el nombre")
            return 1
        objetivo = args[1].strip().lower()
        lista = [p for p in alumnos() if p.split(":")[0].strip().lower() != objetivo]
        guardar_alumnos(lista)
        print("borrado:", args[1])
        return 0

    if args[0] == "--reiniciar":
        reiniciar()
        print("web reiniciada")
        return 0

    nombre = args[0].strip()
    codigo = args[1].strip() if len(args) > 1 else codigo_nuevo()
    lista = [p for p in alumnos() if p.split(":")[0].strip().lower() != nombre.lower()]
    lista.append(nombre + ":" + codigo)
    guardar_alumnos(lista)

    print("")
    print("alumno creado: " + nombre)
    print("codigo:        " + codigo)
    print("")
    print("mensaje para pasarle:")
    print("  Eros, el asistente del curso: " + enlace())
    print("  Entra con tu nombre (" + nombre + ") y este codigo: " + codigo)
    print("")
    print("panel de uso (solo para vos): " + enlace() + "/panel")
    return 0


if __name__ == "__main__":
    sys.exit(main())
