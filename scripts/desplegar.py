"""Despliegue de Eros AI a Hugging Face Spaces, con secretos y verificacion.

    python scripts\desplegar.py <token> [usuario] [nombre]

Crea el Space, carga secretos y variables, sube el repo y verifica que responda.
No deja el token escrito en ningun archivo del repo.
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ESPACIO = "eros-ai"

SECRETOS = {
    "API_KEY": "",            # se completa abajo desde el .env
    "SESSION_SECRET": "",
    "ADMIN_CLAVE": "",
}
VARIABLES = {
    "ADMIN_USER": "Yoka",
    "ALUMNOS": "Yoka:uv53wc",
    "LIMITE_MENSAJES_DIA": "10",
    "LIMITE_MENSAJES_MINUTO": "8",
    "MAX_TOKENS": "20000",
    "BACKEND": "openrouter",
    "FALLBACK_LOCAL": "false",
    "MODELO_ACTIVO": "deepseek-v4.1-flash",
    "PUERTO": "7860",
    "DATOS_DIR": "/app/datos",
}


def env_local(clave, por_defecto=""):
    for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if l.startswith(clave + "="):
            return l.split("=", 1)[1].strip()
    return por_defecto


def api(ruta, token, datos=None, metodo="POST"):
    req = urllib.request.Request("https://huggingface.co/api" + ruta,
                                 data=json.dumps(datos).encode() if datos else None,
                                 headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
                                 method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


def git(*args, ok_falla=True):
    r = subprocess.run(["git"] + list(args), cwd=str(RAIZ), capture_output=True, text=True, timeout=900)
    if r.returncode != 0 and not ok_falla:
        print("  git", " ".join(args), "->", (r.stdout + r.stderr)[-300:])
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    token = (sys.argv[1] if len(sys.argv) > 1 else env_local("HF_TOKEN")).strip()
    usuario = sys.argv[2].strip() if len(sys.argv) > 2 else ""
    espacio = sys.argv[3].strip() if len(sys.argv) > 3 else ESPACIO

    codigo, cuerpo = api("/whoami-v2", token, metodo="GET")
    if codigo != 200:
        print("token invalido:", codigo, cuerpo[:200])
        return 1
    quien = json.loads(cuerpo)
    usuario = usuario or quien.get("name", "")
    print("usuario HF:", usuario, "| tipo:", quien.get("type"))

    print("1) creando Space", usuario + "/" + espacio)
    codigo, cuerpo = api("/repos/create", token,
                         {"name": espacio, "type": "space", "sdk": "docker", "private": False})
    print("   respuesta:", codigo, cuerpo[:140])

    print("2) cargando secretos y variables")
    API = "https://huggingface.co/api/spaces/" + usuario + "/" + espacio
    for k, v in SECRETOS.items():
        if k == "API_KEY":
            v = env_local("API_KEY")
        elif k == "SESSION_SECRET":
            v = env_local("SESSION_SECRET") or ("sess-" + str(int(time.time())))
        elif k == "ADMIN_CLAVE":
            v = env_local("ADMIN_CLAVE") or "eros-admin"
        codigo, cuerpo = api("/spaces/" + usuario + "/" + espacio + "/secrets", token,
                             {"key": k, "value": v, "description": "deploy eros"})
        print("   secreto", k, codigo, (v[:6] + "...") if k == "API_KEY" else "ok")
    for k, v in VARIABLES.items():
        codigo, cuerpo = api("/spaces/" + usuario + "/" + espacio + "/variables", token, {"key": k, "value": v})
        print("   variable", k, "=", v, codigo)

    print("3) preparando el repo (los datos de llaves viajan en la imagen)")
    git("rm", "-r", "--cached", "datos", ok_falla=True)
    git("add", "-f", "datos/llaves.json", "datos")
    git("add", "-A")
    git("-c", "user.email=eros@local", "-c", "user.name=Eros", "commit", "-m",
        "deploy eros-ai a Hugging Face Spaces", "--allow-empty")

    print("4) subiendo")
    remoto = "https://" + usuario + ":" + token + "@huggingface.co/spaces/" + usuario + "/" + espacio
    git("remote", "remove", "hf", ok_falla=True)
    git("remote", "add", "hf", remoto)
    codigo, salida = git("push", "hf", "HEAD:main", "--force", ok_falla=False)
    print(salida[-400:])
    if codigo != 0:
        return 1

    url = "https://" + usuario.lower() + "-" + espacio + ".hf.space"
    print("5) esperando el build en", url)
    for i in range(60):
        time.sleep(10)
        try:
            with urllib.request.urlopen(url + "/api/estado", timeout=15) as r:
                est = json.loads(r.read().decode("utf-8", "ignore"))
            print("   ONLINE tras", i * 10, "s:", {k: est.get(k) for k in ("modelo_visible", "limite_dia", "backend", "alumnos_configurados")})
            print("")
            print("LISTO ->", url)
            print("  chat:  " + url + "/login")
            print("  panel: " + url + "/panel")
            return 0
        except urllib.error.HTTPError as e:
            if e.code in (404, 503):
                continue
            print("   http", e.code, e.read().decode("utf-8", "ignore")[:120])
        except Exception:
            continue
    print("el build tarda mas de 10 minutos, revisá la pestaña Logs del Space:", url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
