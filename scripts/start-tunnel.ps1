# start-tunnel.ps1 - publica la web por https con cloudflared (sin cuenta)
$ErrorActionPreference = 'Continue'
$raiz = Split-Path -Parent $PSScriptRoot
$bin  = Join-Path $raiz 'bin\cloudflared.exe'
$cmd  = Join-Path $raiz 'bin\run-tunnel.cmd'
$log  = Join-Path $raiz 'logs\tunnel.log'
$err  = Join-Path $raiz 'logs\tunnel.err.log'
$vbs  = Join-Path ([Environment]::GetFolderPath('Startup')) 'Eros Tunel.vbs'
$puerto = 8090
$l = (Get-Content (Join-Path $raiz '.env') -ErrorAction SilentlyContinue) | Where-Object { $_ -like 'PUERTO=*' } | Select-Object -First 1
if ($l) { $puerto = [int](($l -split '=', 2)[1]).Trim() }

if (-not (Test-Path $bin)) {
  "descargando cloudflared..."
  Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile $bin
}
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 700
Remove-Item $log, $err -ErrorAction SilentlyContinue

$L1 = '@echo off'
$L2 = 'tasklist /fi "imagename eq cloudflared.exe" | find /i "cloudflared.exe" >nul'
$L3 = 'if not errorlevel 1 exit /b'
$L4 = '"' + $bin + '" tunnel --url http://127.0.0.1:' + $puerto + ' --no-autoupdate --loglevel info --logfile "' + $log + '" >> "' + $err + '" 2>&1'
[IO.File]::WriteAllText($cmd, ((@($L1, $L2, $L3, $L4) -join "`r`n") + "`r`n"), [Text.Encoding]::ASCII)

$V1 = 'Set sh = CreateObject("WScript.Shell")'
$V2 = 'sh.Run "cmd.exe /c ""' + $cmd + '""", 0, False'
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
