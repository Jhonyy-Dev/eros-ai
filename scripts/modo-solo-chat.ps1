# modo-solo-chat.ps1 - apaga la voz (fish-speech) y deja Eros completo y rapido
$ErrorActionPreference = 'Continue'
$raiz = Split-Path -Parent $PSScriptRoot

"apagando voz (fish-speech)..."
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*fish-speech*api_server.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
for ($i = 0; $i -lt 30; $i++) { Start-Sleep 1; if ([int](nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits) -gt 12000) { break } }

"arrancando Eros completo (20 slots, 131k de contexto)..."
& (Join-Path $raiz 'scripts\start-ds9b.ps1') -Modo eros -Slots 20 -Ctx 131072
& (Join-Path $raiz 'scripts\start-web.ps1')
& (Join-Path $raiz 'scripts\start-tunnel.ps1')
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
"listo: Eros solo, sin voz. Para volver a la voz: scripts\modo-voz.ps1"
