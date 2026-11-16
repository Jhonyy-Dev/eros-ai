$ErrorActionPreference = 'Continue'
$app  = 'D:\LocalAI\web\app.py'
$cmd  = 'D:\LocalAI\bin\run-web.cmd'
$log  = 'D:\LocalAI\logs\web.log'
$vbs  = Join-Path ([Environment]::GetFolderPath('Startup')) 'LocalAI Web.vbs'

Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*LocalAI\web\app.py*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 800

$L1 = '@echo off'
$L2 = 'netstat -an | findstr ":8090" | findstr "LISTENING" >nul'
$L3 = 'if not errorlevel 1 exit /b'
$L4 = 'python "' + $app + '" >> "' + $log + '" 2>&1'
$cab = (@($L1, $L2, $L3, $L4) -join "`r`n") + "`r`n"
[IO.File]::WriteAllText($cmd, $cab, [Text.Encoding]::ASCII)

$V1 = 'Set sh = CreateObject("WScript.Shell")'
$V2 = 'sh.Run "cmd.exe /c ""D:\LocalAI\bin\run-web.cmd""", 0, False'
[IO.File]::WriteAllText($vbs, ((@($V1, $V2) -join "`r`n") + "`r`n"), [Text.Encoding]::ASCII)

([wmiclass]'Win32_Process').Create("cmd.exe /c `"$cmd`"") | Out-Null

$ok = $false
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep -Seconds 1
  try { $h = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:8090/api/estado").Content } catch { $h = '' }
  if ($h -match 'limite_por_ip') { $ok = $true; break }
}
if ($ok) { "WEB ARRANCADA en http://127.0.0.1:8090 (autostart: $vbs)" } else { "FALLO la web, revisa $log" }
