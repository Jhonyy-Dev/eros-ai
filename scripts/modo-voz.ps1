# modo-voz.ps1 - deja Eros compacto para convivir con la voz (fish-speech) en la misma GPU
$ErrorActionPreference = 'Continue'
$cfg = Get-Content 'D:\LocalAI\web\config.json' -Raw | ConvertFrom-Json
$dir = 'C:\Users\yokar\OpenBot\Shared\ia\fish-speech'

"arrancando Eros compacto (10 slots, 49k de contexto)..."
& 'D:\LocalAI\start-ds9b.ps1' -Modo eros -ApiKey $cfg.upstream_api_key -Slots 10 -Ctx 49152
& 'D:\LocalAI\start-web.ps1'

$voz = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*fish-speech*api_server.py*' }
if (-not $voz) {
  "arrancando la voz (fish-speech)..."
  Start-Process -FilePath "$dir\.venv\Scripts\python.exe" -WorkingDirectory $dir -WindowStyle Hidden -ArgumentList @(
    'tools/api_server.py','--listen','127.0.0.1:8180',
    '--llama-checkpoint-path', "$dir\checkpoints\s2-pro",
    '--decoder-checkpoint-path', "$dir\checkpoints\s2-pro\codec.pth",
    '--decoder-config-name', 'modded_dac_vq')
} else { "la voz ya estaba corriendo" }

Start-Sleep 8
& 'D:\LocalAI\start-tunnel.ps1'
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
"listo: Eros compacto + voz. Para dejar Eros solo y rapido usa modo-solo-chat.ps1"
