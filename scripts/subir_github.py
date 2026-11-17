"""Crea el repo privado en GitHub y sube Eros. Usa las credenciales de git ya guardadas.

    python scripts\subir_github.py
"""
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
REPO = "eros-ai"


def credencial():
    r = subprocess.run(["git", "credential", "fill"], cwd=str(RAIZ),
                       input="url=https://github.com\n", capture_output=True, text=True, timeout=60)
    usuario = token = ""
    for l in r.stdout.splitlines():
        if l.startswith("username="):
            usuario = l.split("=", 1)[1].strip()
        if l.startswith("password="):
            token = l.split("=", 1)[1].strip()
    return usuario, token


def api(ruta, token, datos=None, metodo="POST"):
    req = urllib.request.Request("https://api.github.com" + ruta,
                                 data=json.dumps(datos).encode() if datos else None,
                                 headers={"Authorization": "token " + token, "User-Agent": "eros",
                                          "Accept": "application/vnd.github+json",
                                          "Content-Type": "application/json"},
                                 method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read().decode("utf-8", "ignore") or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8", "ignore")[:200]}


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=str(RAIZ), capture_output=True, text=True, timeout=900)
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    usuario, token = credencial()
    if not usuario or not token:
        print("no encontre credenciales de GitHub")
        return 1
    print("usuario GitHub:", usuario, "| token de", len(token), "caracteres")

    estado, datos = api("/repos/" + usuario + "/" + REPO, token, metodo="GET")
    if estado == 200:
        print("el repo ya existe:", datos["html_url"])
    else:
        estado, datos = api("/user/repos", token,
                            {"name": REPO, "private": True, "description": "Eros AI - chat para el curso",
                             "has_issues": False, "has_wiki": False})
        print("creando repo:", estado, datos.get("html_url") or datos.get("error"))

    remoto = "https://" + usuario + ":" + token + "@github.com/" + usuario + "/" + REPO + ".git"
    git("remote", "remove", "gh")
    git("remote", "add", "gh", remoto)
    git("add", "-A")
    git("add", "-f", "datos/llaves.json")
    git("-c", "user.email=eros@local", "-c", "user.name=Eros", "commit", "-m", "deploy eros", "--allow-empty")
    print("subiendo a GitHub...")
    codigo, salida = git("push", "gh", "HEAD:main", "--force")
    print(salida[-300:])
    if codigo != 0:
        return 1
    print("")
    print("LISTO. Repo:", "https://github.com/" + usuario + "/" + REPO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
