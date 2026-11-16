# arrancar-todo.ps1 - levanta modelo local, web y tunel, y muestra el enlace publico
$ErrorActionPreference = 'Continue'
$raiz = Split-Path -Parent $PSScriptRoot
$s = Join-Path $raiz 'scripts'

& (Join-Path $s 'start-ds9b.ps1') -Modo eros
& (Join-Path $s 'start-web.ps1')
& (Join-Path $s 'start-tunnel.ps1')

Start-Sleep -Seconds 2
$u = ''
try { $u = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 'http://127.0.0.1:8090/api/estado').Content | ConvertFrom-Json | Select-Object -ExpandProperty url_publica } catch { }
if ($u) {
  Set-Content (Join-Path $raiz 'url_publica.txt') -Encoding UTF8 -Value @(
    'Enlace publico de Eros:', '', '  ' + $u, '', 'Panel: ' + $u + '/panel',
    'Cada alumno entra con su nombre y el codigo que le diste.', 'La url cambia si se reinicia el tunel.')
  "=================================================="
  "  EROS ARRIBA"
  "  chat:         $u"
  "  panel:        $u/panel"
  "  estudiantes:  .env -> ALUMNOS=nombre:codigo"
  "=================================================="
} else {
  "modelo y web arriba, pero el tunel todavia no dio url. Revisa $raiz\logs\tunnel.log"
}
