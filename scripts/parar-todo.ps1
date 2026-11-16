# parar-todo.ps1 - apaga chat publico, web y modelo
$raiz = Split-Path -Parent $PSScriptRoot
& (Join-Path $raiz 'scripts\stop-web.ps1')
& (Join-Path $raiz 'scripts\stop-ds9b.ps1')
"Eros apagado (modelo, web y tunel)"
