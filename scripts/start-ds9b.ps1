param(
  [ValidateSet('raw','directo','pensante','liberado','duro','duro2','duro3','duro4','eros')] [string]$Modo = 'eros',
  [int]$Slots = 20,
  [int]$Ctx = 131072,
  [int]$Puerto = 8099,
  [string]$ApiKey = '',
  [double]$Temp = 0.6,
  [double]$TopP = 0.95,
  [double]$MinP = 0.05,
  [double]$RepPen = 1.05,
  [string]$Modelo = ''
)
$ErrorActionPreference = 'Continue'
$bin    = 'D:\LocalAI\bin\llama-server.exe'
$cmd    = 'D:\LocalAI\bin\run-ds9b.cmd'
$log    = 'D:\LocalAI\logs\server.log'
$modelo = 'D:\OllamaModels\blobs\sha256-1b251677521c3452c4e2eb8cdb1504d40d0c2e64f77cd4222cfd17cbe2d195fc'
if ($Modelo -ne '') { $modelo = $Modelo }
$vbs    = Join-Path ([Environment]::GetFolderPath('Startup')) 'LocalAI DeepSeek9B.vbs'
$lnkviejo = Join-Path ([Environment]::GetFolderPath('Startup')) 'LocalAI-DeepSeek9B.lnk'

Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
for ($w = 0; $w -lt 45; $w++) {
  Start-Sleep -Seconds 1
  $libre = [int](nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits)
  if ($libre -gt 8000) { break }
}

$a = @('--model', $modelo, '--host', '0.0.0.0', '--port', "$Puerto", '--no-webui', '--offline',
       '-c', "$Ctx", '-np', "$Slots", '--cont-batching', '--flash-attn', 'on',
       '--cache-type-k', 'q8_0', '--cache-type-v', 'q8_0',
       '-ngl', '99', '-b', '512', '-ub', '256', '--threads', '12',
       '--metrics', '--slots',
       '--temp', "$Temp", '--top-p', "$TopP", '--min-p', "$MinP", '--repeat-penalty', "$RepPen",
       '--log-file', $log)
if ($Modo -ne 'raw') { $a = $a + @('--chat-template-file', "D:\LocalAI\config\ds9b-$Modo.jinja") }
if ($ApiKey -ne '')  { $a = $a + @('--api-key', $ApiKey) }
$linea = $a -join ' '

$L1 = '@echo off'
$L2 = 'tasklist /fi "imagename eq llama-server.exe" | find /i "llama-server.exe" >nul'
$L3 = 'if not errorlevel 1 exit /b'
$L4 = "`"$bin`" $linea >> `"D:\LocalAI\logs\stdout.log`" 2>&1"
$cab = (@($L1, $L2, $L3, $L4) -join "`r`n") + "`r`n"
[IO.File]::WriteAllText($cmd, $cab, [Text.Encoding]::ASCII)

$V1 = 'Set sh = CreateObject("WScript.Shell")'
$V2 = 'sh.Run "cmd.exe /c ""D:\LocalAI\bin\run-ds9b.cmd""", 0, False'
$vabcab = (@($V1, $V2) -join "`r`n") + "`r`n"
[IO.File]::WriteAllText($vbs, $vabcab, [Text.Encoding]::ASCII)
if (Test-Path $lnkviejo) { Remove-Item $lnkviejo -Force }

$via = 'ninguna'
$arrancado = $false
$salida = (& schtasks.exe /Create /TN "LocalAI-DeepSeek9B" /TR "$cmd" /SC ONLOGON /F 2>&1 | Out-String)
if ($LASTEXITCODE -eq 0) {
  (& schtasks.exe /Run /TN "LocalAI-DeepSeek9B" 2>&1 | Out-Null)
  if ($LASTEXITCODE -eq 0) { $arrancado = $true; $via = 'tarea programada ONLOGON' }
} else {
  $motivo = ($salida -replace "`r?`n", ' ').Trim()
}
if (-not $arrancado) {
  $r = ([wmiclass]'Win32_Process').Create("cmd.exe /c `"$cmd`"")
  if ($r.ReturnValue -eq 0) { $arrancado = $true; $via = 'WMI + arranque automatico en carpeta Inicio' }
}

$ok = $false
for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep -Seconds 2
  try { $h = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:$Puerto/health").Content } catch { $h = '' }
  if ($h -match 'ok') { $ok = $true; break }
}
$proc = Get-Process llama-server -ErrorAction SilentlyContinue
$vram = [int](nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
if ($ok -and $proc -and $vram -lt 3000) {
  "AVISO: no cargo en GPU (VRAM usada=$vram). Relanzo una vez."
  Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
  for ($w = 0; $w -lt 45; $w++) { Start-Sleep -Seconds 1; if ([int](nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits) -gt 8000) { break } }
  $r2 = ([wmiclass]'Win32_Process').Create("cmd.exe /c `"$cmd`"")
  for ($i = 0; $i -lt 60; $i++) { Start-Sleep -Seconds 2; try { $h = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:$Puerto/health").Content } catch { $h = '' }; if ($h -match 'ok') { break } }
  $proc = Get-Process llama-server -ErrorAction SilentlyContinue
  $vram = [int](nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
}
if ($ok -and $proc) { "ARRANCADO pid=$($proc.Id) modo=$Modo slots=$Slots ctx=$Ctx puerto=$Puerto vram_usada=${vram}MiB via=$via" }
else { "FALLO al arrancar, revisa $log y D:\LocalAI\logs\stdout.log" }
if ($motivo) { "tarea programada no disponible: $motivo (queda el .vbs en Inicio)" }
