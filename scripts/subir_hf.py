# subir_hf.py - crea el Space en Hugging Face y sube el proyecto por git
#
#   python scripts\subir_hf.py <token> [usuario] [nombre-del-space]
#
# El token se saca de https://huggingface.co/settings/tokens (rol write).
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def api(ruta, token, datos=None, metodo="POST"):
    req = urllib.request.Request("https://huggingface.co/api" + ruta,
                                 data=json.dumps(datos).encode() if datos else None,
                                 headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
                                 method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=str(RAIZ), capture_output=True, text=True, timeout=600)
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    token = sys.argv[1].strip()
    usuario = sys.argv[2].strip() if len(sys.argv) > 2 else ""
    espacio = sys.argv[3].strip() if len(sys.argv) > 3 else "eros-ai"

    if not usuario:
        codigo, cuerpo = api("/whoami-v2", token, metodo="GET")
        if codigo != 200:
            print("token invalido:", codigo, cuerpo[:200])
            return 1
        usuario = json.loads(cuerpo).get("name", "")
        print("usuario del token:", usuario)

    print("creando Space", usuario + "/" + espacio, "...")
    codigo, cuerpo = api("/repos/create", token,
                         {"name": espacio, "type": "space", "sdk": "docker", "private": False})
    print("  respuesta:", codigo, cuerpo[:160])

    remoto = "https://" + usuario + ":" + token + "@huggingface.co/spaces/" + usuario + "/" + espacio
    git("remote", "remove", "hf")
    git("remote", "add", "hf", remoto)
    git("add", "-A")
    git("-c", "user.email=eros@local", "-c", "user.name=Eros", "commit", "-m",
        "deploy a Hugging Face Spaces", "--allow-empty")
    print("subiendo (puede tardar por el video)...")
    codigo, salida = git("push", "hf", "HEAD:main", "--force")
    print(salida[-600:])
    if codigo != 0:
        print("FALLO el push")
        return 1
    print("")
    print("LISTO. En 1 o 2 minutos queda online en:")
    print("  https://" + usuario.lower() + "-" + espacio + ".hf.space")
    print("Despues cargá las variables en Settings -> Variables and secrets:")
    print("  API_KEY, SESSION_SECRET, ADMIN_USER, ADMIN_CLAVE, ALUMNOS,")
    print("  LIMITE_MENSAJES_DIA=10, MAX_TOKENS=20000, BACKEND=openrouter, FALLBACK_LOCAL=false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
