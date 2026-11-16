Stop-ScheduledTask -TaskName 'LocalAI-DeepSeek9B' -ErrorAction SilentlyContinue
Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 800
if (Get-Process llama-server -ErrorAction SilentlyContinue) { "sigue vivo" } else { "modelo detenido" }
