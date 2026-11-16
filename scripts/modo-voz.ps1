# modo-voz.ps1 - deja Eros compacto para convivir con la voz (fish-speech) en la misma GPU
$ErrorActionPreference = 'Continue'
$raiz = Split-Path -Parent $PSScriptRoot
$dir  = 'C:\Users\yokar\OpenBot\Shared\ia\fish-speech'

"arrancando Eros compacto (10 slots, 49k de contexto)..."
& (Join-Path $raiz 'scripts\start-ds9b.ps1') -Modo eros -Slots 10 -Ctx 49152
& (Join-Path $raiz 'scripts\start-web.ps1')

$voz = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*fish-speech*api_server.py*' }
if (-not $voz) {
  "arrancando la voz (fish-speech)..."
  Start-Process -FilePath "$dir\.venv\Scripts\python.exe" -WorkingDirectory $dir -WindowStyle Hidden -ArgumentList @(
    'tools/api_server.py', '--listen', '127.0.0.1:8180',
    '--llama-checkpoint-path', "$dir\checkpoints\s2-pro",
    '--decoder-checkpoint-path', "$dir\checkpoints\s2-pro\codec.pth",
    '--decoder-config-name', 'modded_dac_vq')
} else { "la voz ya estaba corriendo" }

Start-Sleep 8
& (Join-Path $raiz 'scripts\start-tunnel.ps1')
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
"listo: Eros compacto + voz. Para dejarlo solo y rapido: scripts\modo-solo-chat.ps1"
