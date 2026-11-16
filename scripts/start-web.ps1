# start-web.ps1 - arranca el gateway de Eros desde EROS_AI (FastAPI + uvicorn)
$ErrorActionPreference = 'Continue'
$raiz = Split-Path -Parent $PSScriptRoot          # ...\EROS_AI
$app  = Join-Path $raiz 'server\app.py'
$cmd  = Join-Path $raiz 'bin\run-web.cmd'
$log  = Join-Path $raiz 'logs\web.log'
$vbs  = Join-Path ([Environment]::GetFolderPath('Startup')) 'Eros Web.vbs'
$puerto = 8090
$l = (Get-Content (Join-Path $raiz '.env') -ErrorAction SilentlyContinue) | Where-Object { $_ -like 'PUERTO=*' } | Select-Object -First 1
if ($l) { $puerto = [int](($l -split '=', 2)[1]).Trim() }

Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*server\app.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 700

$L1 = '@echo off'
$L2 = 'netstat -an | findstr ":' + $puerto + '" | findstr "LISTENING" >nul'
$L3 = 'if not errorlevel 1 exit /b'
$L4 = 'python "' + $app + '" >> "' + $log + '" 2>&1'
[IO.File]::WriteAllText($cmd, ((@($L1, $L2, $L3, $L4) -join "`r`n") + "`r`n"), [Text.Encoding]::ASCII)

$V1 = 'Set sh = CreateObject("WScript.Shell")'
$V2 = 'sh.Run "cmd.exe /c ""' + $cmd + '""", 0, False'
[IO.File]::WriteAllText($vbs, ((@($V1, $V2) -join "`r`n") + "`r`n"), [Text.Encoding]::ASCII)

([wmiclass]'Win32_Process').Create("cmd.exe /c `"$cmd`"") | Out-Null

$ok = $false
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep -Seconds 1
  try { $h = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:$puerto/api/estado").Content } catch { $h = '' }
  if ($h -match 'modelo_visible') { $ok = $true; break }
}
if ($ok) { "WEB ARRANCADA en http://127.0.0.1:$puerto  (autostart: $vbs)" } else { "FALLO la web, revisa $log" }
