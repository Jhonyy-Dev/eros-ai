# arrancar-todo.ps1 - levanta el modelo, la web y el tunel publico de Eros, y muestra el enlace
$ErrorActionPreference = 'Continue'
$cfg = Get-Content 'D:\LocalAI\web\config.json' -Raw | ConvertFrom-Json

"1/3 modelo..."
& 'D:\LocalAI\start-ds9b.ps1' -Modo eros -ApiKey $cfg.upstream_api_key

"2/3 web..."
& 'D:\LocalAI\start-web.ps1'

"3/3 tunel publico..."
& 'D:\LocalAI\start-tunnel.ps1'

Start-Sleep -Seconds 2
$u = ''
try { $u = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 'http://127.0.0.1:8090/api/estado').Content | ConvertFrom-Json | Select-Object -ExpandProperty url_publica } catch { }
$vram = [int](nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)

if ($u) {
  Set-Content 'D:\LocalAI\url_publica.txt' -Encoding UTF8 -Value @(
    'Enlace publico de Eros:',
    '',
    '  ' + $u,
    '',
    'Clave: ' + $cfg.clave_acceso,
    'Panel de uso: ' + $u + '/panel',
    'La url cambia cada vez que se reinicia el tunel.'
  )
  "======================================================"
  "  EROS ARRIBA"
  "  chat:  $u"
  "  clave: $($cfg.clave_acceso)"
  "  panel: $u/panel"
  "  vram usada por el modelo: ${vram} MiB"
  "======================================================"
} else {
  "El modelo y la web arrancaron, pero el tunel todavia no dio url. Mira D:\LocalAI\logs\tunnel.log"
}
