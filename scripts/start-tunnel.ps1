$ErrorActionPreference = 'Continue'
$bin = 'D:\LocalAI\bin\cloudflared.exe'
$cmd = 'D:\LocalAI\bin\run-tunnel.cmd'
$log = 'D:\LocalAI\logs\tunnel.log'
$vbs = Join-Path ([Environment]::GetFolderPath('Startup')) 'LocalAI Tunel.vbs'

if (-not (Test-Path $bin)) {
  "descargando cloudflared..."
  Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile $bin
}
if (-not (Test-Path $bin)) { "FALLO la descarga de cloudflared"; exit 1 }

Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 800
Remove-Item $log -ErrorAction SilentlyContinue
Remove-Item $log.Replace('.log', '.err.log') -ErrorAction SilentlyContinue

$L1 = '@echo off'
$L2 = 'tasklist /fi "imagename eq cloudflared.exe" | find /i "cloudflared.exe" >nul'
$L3 = 'if not errorlevel 1 exit /b'
$L4 = '"' + $bin + '" tunnel --url http://127.0.0.1:8090 --no-autoupdate --loglevel info --logfile "' + $log + '" >> "' + $log.Replace('.log', '.err.log') + '" 2>&1'
[IO.File]::WriteAllText($cmd, ((@($L1, $L2, $L3, $L4) -join "`r`n") + "`r`n"), [Text.Encoding]::ASCII)

$V1 = 'Set sh = CreateObject("WScript.Shell")'
$V2 = 'sh.Run "cmd.exe /c ""D:\LocalAI\bin\run-tunnel.cmd""", 0, False'
[IO.File]::WriteAllText($vbs, ((@($V1, $V2) -join "`r`n") + "`r`n"), [Text.Encoding]::ASCII)

([wmiclass]'Win32_Process').Create("cmd.exe /c `"$cmd`"") | Out-Null

$url = ''
for ($i = 0; $i -lt 45; $i++) {
  Start-Sleep -Seconds 1
  if (Test-Path $log) {
    $m = Select-String -Path $log -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -AllMatches -ErrorAction SilentlyContinue
    if ($m) { $url = $m.Matches[0].Value; break }
  }
}
if ($url) { "TUNEL ACTIVO: $url" } else { "sin url todavia, revisa $log" }
