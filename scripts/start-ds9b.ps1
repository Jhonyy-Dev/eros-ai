param(
  [ValidateSet('raw','directo','pensante','liberado','duro','duro2','duro3','duro4','eros','eros2')] [string]$Modo = 'eros2',
  [int]$Slots = 12,
  [int]$Ctx = 65536,
  [int]$Puerto = 8099,
  [string]$ApiKey = '',
  [string]$Modelo = '',
  [double]$Temp = 0.45,
  [double]$TopP = 0.95,
  [double]$MinP = 0.05,
  [double]$RepPen = 1.05
)
$ErrorActionPreference = 'Continue'
$raiz = Split-Path -Parent $PSScriptRoot
$bin = Join-Path $raiz 'bin\llama-server.exe'
$cmd = Join-Path $raiz 'bin\run-ds9b.cmd'
$log = Join-Path $raiz 'logs\modelo.log'
$vbs = Join-Path ([Environment]::GetFolderPath('Startup')) 'Eros Modelo.vbs'
$jinja = Join-Path $raiz ('config\ds9b-' + $Modo + '.jinja')

function Env([string]$k) {
  $linea = (Get-Content (Join-Path $raiz '.env') -ErrorAction SilentlyContinue) | Where-Object { $_ -like "$k=*" } | Select-Object -First 1
  if ($linea) { return (($linea -split '=', 2)[1]).Trim() }
  return ''
}

$blob = 'D:\OllamaModels\blobs\sha256-1b251677521c3452c4e2eb8cdb1504d40d0c2e64f77cd4222cfd17cbe2d195fc'
if ($Modelo -ne '') { $blob = $Modelo }
if ($ApiKey -eq '') { $ApiKey = Env 'LOCAL_KEY' }

Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
for ($w = 0; $w -lt 45; $w++) {
  Start-Sleep -Seconds 1
  if ([int](nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits) -gt 5000) { break }
}

$args = @('--model', $blob, '--host', '0.0.0.0', '--port', "$Puerto", '--no-webui', '--offline',
          '-c', "$Ctx", '-np', "$Slots", '--cont-batching', '--flash-attn', 'on',
          '--cache-type-k', 'q8_0', '--cache-type-v', 'q8_0',
          '-ngl', '99', '-b', '512', '-ub', '256', '--threads', '12',
          '--metrics', '--slots',
          '--temp', "$Temp", '--top-p', "$TopP", '--min-p', "$MinP", '--repeat-penalty', "$RepPen",
          '--log-file', $log)
if ($Modo -ne 'raw') { $args = $args + @('--chat-template-file', $jinja) }
if ($ApiKey -ne '') { $args = $args + @('--api-key', $ApiKey) }
$linea = $args -join ' '

$logOut = Join-Path $raiz 'logs\modelo-stdout.log'
$l1 = '@echo off'
$l2 = 'tasklist /fi "imagename eq llama-server.exe" | find /i "llama-server.exe" >nul'
$l3 = 'if not errorlevel 1 exit /b'
$l4 = '"' + $bin + '" ' + $linea + ' >> "' + $logOut + '" 2>&1'
[IO.File]::WriteAllText($cmd, ((@($l1, $l2, $l3, $l4) -join "`r`n") + "`r`n"), [Text.Encoding]::ASCII)

$v1 = 'Set sh = CreateObject("WScript.Shell")'
$v2 = 'sh.Run "cmd.exe /c ""' + $cmd + '""", 0, False'
[IO.File]::WriteAllText($vbs, ((@($v1, $v2) -join "`r`n") + "`r`n"), [Text.Encoding]::ASCII)

([wmiclass]'Win32_Process').Create("cmd.exe /c `"$cmd`"") | Out-Null

$ok = $false
for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep -Seconds 2
  try { $h = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:$Puerto/health").Content } catch { $h = '' }
  if ($h -match 'ok') { $ok = $true; break }
}
$proc = Get-Process llama-server -ErrorAction SilentlyContinue
$vram = [int](nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
if ($ok -and $proc) { "MODELO ARRANCADO pid=$($proc.Id) modo=$Modo slots=$Slots ctx=$Ctx vram=${vram}MiB" }
else { "FALLO el modelo, revisa $log" }
