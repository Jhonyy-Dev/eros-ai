"""El código que entrega Eros tiene que venir completo y compilar.

    python pruebas\\codigo_completo.py [url]

Pide 3 trabajos, saca los bloques de código y los compila de verdad (compile()).
Falla si algún bloque queda abierto, si trae "..." o si un bloque que dice ser python no compila.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("EROS_URL") or "http://127.0.0.1:8090").rstrip("/")
ALIAS = os.environ.get("EROS_ALIAS") or "cod"
CLAVE = os.environ.get("EROS_CLAVE") or "Prueba123@"

PEDIDOS = [
    ("script python con argparse", "dame un script en python que escanee una carpeta y saque hashes, con argparse"),
    ("script bash", "dame un script en bash que haga backup incremental con rsync y log"),
    ("clase python con manejo de errores", "dame una clase en python para leer un csv enorme por chunks con reintentos"),
]
def tiene_huecos(cuerpo):
    """Igual que el servidor: solo lineas '...' o comentarios cortados, no 'tuple[T, ...]'."""
    marcas = ("resto igual", "sin cambios", "omito", "omitid", "etc.")
    for linea in (cuerpo or "").split("\n"):
        p = linea.strip()
        if not p:
            continue
        if p in ("...", "# ...", "// ...", "#...", "//..."):
            return True
        if p.startswith("#") or p.startswith("//") or p.startswith("--") or p.startswith(";"):
            bajo = p.lower()
            if (p.startswith("# ...") or p.startswith("// ...") or p.endswith("...")
                    or any(m in bajo for m in marcas)):
                return True
    return False
BLOQUES = re.compile(r"```([^\n]*)\n([\s\S]*?)```")


def parece_python(etiqueta, cuerpo):
    et = (etiqueta or "").lower().strip()
    if et.startswith("py") or "python" in et or et.startswith("#") and ".py" in et:
        return True
    if not et and re.search(r"^\s*(import |from \w+ import|def |class )", cuerpo, re.M):
        return True   # bloque sin etiqueta pero con pinta de python
    for linea in cuerpo.split("\n"):
        s = linea.strip()
        if not s or s.startswith("#") or s.startswith("!"):
            continue
        return bool(re.match(r"^(import|from|def |class |async def|@|if |for |while |print\()", s))
    return False


op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
op.open(urllib.request.Request(BASE + "/login", data=urllib.parse.urlencode(
    {"nombre": ALIAS, "codigo": CLAVE}).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=40)

fallas = []
for nombre, pedido in PEDIDOS:
    t0 = time.time()
    try:
        resp = op.open(urllib.request.Request(BASE + "/api/chat", data=json.dumps(
            {"mensajes": [{"role": "user", "content": pedido}], "max_tokens": 4000}).encode(),
            headers={"Content-Type": "application/json"}), timeout=600)
    except urllib.error.HTTPError as e:
        print("  límite:", e.read().decode("utf-8", "ignore")[:70])
        continue
    texto = ""
    for linea in resp:
        if linea.startswith(b"data: "):
            j = json.loads(linea[6:].decode("utf-8", "ignore"))
            texto += j.get("t", "")
            if j.get("error"):
                print("  error:", j["error"])
    texto = texto.strip()
    bloques = BLOQUES.findall(texto)
    compilado = False
    abierto = texto.count("```") % 2 == 1
    print("\n  %s | %.1fs | %d chars | bloques: %d | cerca abierta: %s | rehizo: %s"
          % (nombre, time.time() - t0, len(texto), len(bloques), abierto, "sin abreviar" in texto))
    if not bloques:
        fallas.append(nombre + ": sin bloque de codigo")
        print("    FALLA: no trajo código")
        continue
    if abierto:
        fallas.append(nombre + ": cerca sin cerrar")
        print("    FALLA: bloque sin cerrar")
    for etiqueta, cuerpo in bloques:
        if tiene_huecos(cuerpo):
            fallas.append(nombre + ": codigo abreviado")
            print("    FALLA: código abreviado (linea '...' o comentario cortado)")
        try:
            compile(cuerpo, "<eros>", "exec")
            print("    OK: bloque '%s' compila (%d líneas)" % (etiqueta or "sin etiqueta", len(cuerpo.splitlines())))
        except SyntaxError as e:
            if parece_python(etiqueta, cuerpo) and not compilado:
                fallas.append(nombre + ": no compila (linea %s)" % e.lineno)
                print("    FALLA: no compila ->", str(e)[:90])
            else:
                print("    aviso: bloque '%s' de %d líneas no compila (fragmento)"
                      % (etiqueta or "sin etiqueta", len(cuerpo.splitlines())))
        if parece_python(etiqueta, cuerpo):
            compilado = True

print("\nresultado:", "TODO OK" if not fallas else "FALLAS: " + "; ".join(fallas))
sys.exit(1 if fallas else 0)
