"""Los bloques de metadatos del modelo tienen que quedar afuera de la respuesta."""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import server.app as app  # noqa: E402

C = "`" * 3
CASOS = [
    ("ds_safety con cerca detras",
     "<ds_safety>[user]no\n[clase]otra</ds_safety>Safe\n" + C + "\n# a.py", C + "\n# a.py"),
    ("ds_safety sin cerca",
     "<ds_safety>dato</ds_safety>\n\n# b.py", "# b.py"),
    ("plantilla jinja con cerca adelante",
     C + "{{#if (eq system_prompt 'Eros')}}\nX\n{{/if}}Safe\n# c.py", C + "\n# c.py"),
    ("plantilla jinja sola",
     "{{#if x}}{{/if}}" + C + "python\n# d.py", C + "python\n# d.py"),
    ("cerca normal del modelo", C + "python\n# e.py", C + "python\n# e.py"),
    ("prosa sin nada raro", "# f.py\nimport os", "# f.py\nimport os"),
]

fallas = 0
for nombre, entrada, esperado in CASOS:
    salida = app.sin_meta(entrada)
    bien = salida == esperado
    fallas += 0 if bien else 1
    print(("  OK   " if bien else "  FALLA") + "  " + nombre)
    if not bien:
        print("        obtuve : " + repr(salida))
        print("        queria : " + repr(esperado))

print("espera mientras el bloque esta abierto:", app.parece_meta("<ds_safety>[x"), app.parece_meta("{{#if x"),
      app.parece_meta(C + "{{#if"))
print("no espera con contenido normal     :", app.parece_meta("# texto"), app.parece_meta(C + "python\n# x"))
print("\nresultado: %d/%d" % (len(CASOS) - fallas, len(CASOS)))
sys.exit(1 if fallas else 0)
