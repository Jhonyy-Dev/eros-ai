# stop-web.ps1 - apaga gateway y tunel
$ErrorActionPreference = 'Continue'
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*server\app.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 700
$web = if (Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*server\app.py*' }) { 'web sigue viva' } else { 'web detenida' }
$tun = if (Get-Process cloudflared -ErrorAction SilentlyContinue) { 'tunel sigue vivo' } else { 'tunel detenido' }
"$web / $tun"
