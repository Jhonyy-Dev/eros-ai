"""Mide que el chat sea fluido: cuadros por segundo, repintados y que el scroll aguante arriba.

    python pruebas\\fluidez.py [url]            (por defecto http://127.0.0.1:8090)

Necesita playwright:  pip install playwright  &&  playwright install chromium
Entra con EROS_ALIAS / EROS_CLAVE (por defecto webtest / Prueba123@).
"""
import statistics
import sys
import os

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("EROS_URL") or "http://127.0.0.1:8090").rstrip("/")
ALIAS = os.environ.get("EROS_ALIAS") or "webtest"
CLAVE = os.environ.get("EROS_CLAVE") or "Prueba123@"
PREGUNTA = ("dame el manual completo para montar un servidor casero con linux: pasos numerados, "
            "cantidades exactas, errores tipicos y precios")
RUEDA = -60          # subir un poquito: es lo que antes te devolvia al fondo

INSTRUMENTO = """
() => {
  window.__f = []; window.__mut = 0;
  let last = performance.now();
  const loop = t => { const d = t - last; last = t; window.__f.push(d); requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
  new MutationObserver(ms => { window.__mut += ms.length; })
      .observe(document.querySelector('#hilo .col'), { childList:true, subtree:true, characterData:true });
}
"""


def main():
    fallas = []
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page(viewport={"width": 1366, "height": 820})
        pg.goto(BASE + "/login", wait_until="domcontentloaded")
        pg.fill("#nombre", ALIAS)
        pg.fill("#codigo", CLAVE)
        pg.click("button[type=submit]")
        pg.wait_for_selector("#entrada", timeout=60000)
        pg.evaluate(INSTRUMENTO)
        pg.fill("#entrada", PREGUNTA)
        pg.click("#enviar")

        for _ in range(120):
            pg.wait_for_timeout(200)
            if pg.evaluate("() => { const h=document.querySelector('#hilo');"
                           " return h.scrollHeight - h.clientHeight; }") > 900:
                break

        pg.mouse.move(683, 400)
        pg.mouse.wheel(0, RUEDA)
        pg.wait_for_timeout(150)
        base = pg.evaluate("document.querySelector('#hilo').scrollTop")
        quedarse = []
        for _ in range(18):
            pg.wait_for_timeout(100)
            quedarse.append(pg.evaluate("document.querySelector('#hilo').scrollTop") - base)
        quieto = max(map(abs, quedarse)) < 40
        boton = pg.evaluate("getComputedStyle(document.querySelector('#irFinal')).display") != "none"
        if boton:
            pg.click("#irFinal")
            pg.wait_for_timeout(400)
        abajo = pg.evaluate("() => { const h=document.querySelector('#hilo');"
                            " return h.scrollHeight - h.scrollTop - h.clientHeight; }")

        for _ in range(180):
            if not pg.evaluate("!!document.querySelector('.cursor')"):
                break
            pg.wait_for_timeout(500)
        datos = pg.evaluate("({f: window.__f, mut: window.__mut})")
        largo = len(pg.inner_text(".turno.ia .cuerpo"))
        nav.close()

    marcos = [d for d in datos["f"] if d < 500]
    segundos = sum(marcos) / 1000 or 1
    print("respuesta: %d caracteres | %.1f s" % (largo, segundos))
    print("cuadros: %d | promedio %.1f fps | lentos (>50ms): %d | peor %.0f ms"
          % (len(marcos), 1000 / statistics.mean(marcos), len([d for d in marcos if d > 50]), max(marcos)))
    print("repintados del DOM: %d (%.1f por segundo)" % (datos["mut"], datos["mut"] / segundos))
    print("al subir %d px, el chat se queda: %s (desvio maximo %d px) | boton 'ir al final': %s"
          % (-RUEDA, "SI" if quieto else "NO", max(map(abs, quedarse)), boton))
    print("el boton devuelve al fondo: %s (%d px)" % ("SI" if abajo < 40 else "NO", abajo))
    if not quieto:
        fallas.append("el scroll no se queda arriba")
    if not boton:
        fallas.append("no aparece el boton ir al final")
    if abajo >= 40:
        fallas.append("el boton no vuelve al fondo")
    if datos["mut"] / max(1, segundos) > 40:
        fallas.append("demasiados repintados por segundo")
    print("\nresultado: " + ("TODO OK" if not fallas else "FALLAS: " + ", ".join(fallas)))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
