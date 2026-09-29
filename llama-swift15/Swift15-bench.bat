<# : batch portion
@echo off
setlocal
rem ASCII ONLY. cmd runs this top part, PowerShell runs the rest of the file.
rem ============================================================================
rem Swift15-bench.bat - health check + speed test for Swift15-27B-MTP-150K.bat
rem   Swift15-bench.bat         3 short prompts: decode tok/s, MTP acceptance
rem   Swift15-bench.bat long    + one 110K-135K token prompt, 150K ctx + needle test
rem Other server:  set SWIFT_URL=http://127.0.0.1:5678  before running.
rem Writes swift15_bench_DATE_TIME.txt next to this file - paste it into the chat.
rem ============================================================================
set "BENCH_ARGS=%*"
set "BENCH_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ([IO.File]::ReadAllText('%~f0'))"
echo.
pause
exit /b
#>

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Base = 'http://127.0.0.1:5678'
if ($env:SWIFT_URL) { $Base = $env:SWIFT_URL.TrimEnd('/') }
$Long = ("$env:BENCH_ARGS" -match 'long')
$Dir = $env:BENCH_DIR
if (-not $Dir) { $Dir = (Get-Location).Path }
$Out = Join-Path $Dir ('swift15_bench_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.txt')
Start-Transcript -Path $Out | Out-Null

function Show-Vram([string]$label) {
  try {
    $v = & nvidia-smi -i 0 --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits 2>$null
    if ($v) {
      $p = "$v".Split(',')
      Write-Host ('   VRAM GPU0 ' + $label + ': ' + $p[1].Trim() + ' / ' + $p[2].Trim() + ' MiB (' + $p[0].Trim() + ')')
    }
  } catch { Write-Host '   nvidia-smi not available' }
}

$script:Results = @()
function Invoke-Chat([string]$name, [string]$prompt, [int]$maxTokens) {
  $body = @{
    messages   = @(@{ role = 'user'; content = $prompt })
    max_tokens = $maxTokens
    stream     = $false
  } | ConvertTo-Json -Depth 5
  $bytes = [Text.Encoding]::UTF8.GetBytes($body)
  $t0 = Get-Date
  try {
    $r = Invoke-RestMethod -Uri "$Base/v1/chat/completions" -Method Post -ContentType 'application/json; charset=utf-8' -Body $bytes -TimeoutSec 3600
  } catch {
    Write-Host ('   [FAIL] ' + $name + ': ' + $_.Exception.Message)
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) { Write-Host ('   ' + $_.ErrorDetails.Message); return $null }
    try {
      $sr = New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())
      Write-Host ('   ' + $sr.ReadToEnd())
    } catch { }
    return $null
  }
  $wall = ((Get-Date) - $t0).TotalSeconds
  $t = $r.timings
  if (-not $t) {
    Write-Host ('   [WARN] ' + $name + ': no timings in the response')
    return $r
  }
  $acc = 'n/a (MTP off?)'
  if ($t.draft_n -gt 0) {
    $acc = ([math]::Round(100.0 * $t.draft_n_accepted / $t.draft_n, 1)).ToString() + '% (' + $t.draft_n_accepted + '/' + $t.draft_n + ')'
  }
  $fmt = 'RESULT {0,-6} prompt {1,7} tok @ {2,8:N1} tok/s | gen {3,5} tok @ {4,6:N1} tok/s | MTP accept {5} | wall {6:N1}s'
  Write-Host ($fmt -f $name, $t.prompt_n, $t.prompt_per_second, $t.predicted_n, $t.predicted_per_second, $acc, $wall)
  $script:Results += [pscustomobject]@{ name = $name; tps = [double]$t.predicted_per_second }
  return $r
}

Write-Host ('== 1/4 health check: ' + $Base + '/health')
$deadline = (Get-Date).AddMinutes(15)
while ($true) {
  $ok = $false
  try {
    $h = Invoke-WebRequest -Uri "$Base/health" -UseBasicParsing -TimeoutSec 5
    if ($h.StatusCode -eq 200) { $ok = $true }
  } catch { }
  if ($ok) { break }
  if ((Get-Date) -gt $deadline) {
    Write-Host '[FAIL] no healthy server after 15 min. Start Swift15-27B-MTP-150K.bat first.'
    Stop-Transcript | Out-Null
    exit 1
  }
  Write-Host '   waiting - model still loading, or the server is not started...'
  Start-Sleep -Seconds 5
}
Write-Host '   OK'

Write-Host '== 2/4 server settings: /props'
try {
  $props = Invoke-RestMethod -Uri "$Base/props" -TimeoutSec 10
  $nctx = $props.default_generation_settings.n_ctx
  Write-Host ('   model      : ' + $props.model_alias)
  Write-Host ('   model path : ' + $props.model_path)
  Write-Host ('   ctx / slot : ' + $nctx + '   slots: ' + $props.total_slots)
  if ($nctx -and ([int]$nctx -lt 150000)) { Write-Host '   [WARN] context per slot is below 150000' }
} catch { Write-Host ('   [WARN] /props failed: ' + $_.Exception.Message) }
Show-Vram 'idle'

Write-Host '== 3/4 short prompts (first one is a warm-up and is not counted)'
$null = Invoke-Chat 'warmup' 'Say hello in one short sentence.' 64
$script:Results = @()
$null = Invoke-Chat 'code' 'Write a Python function that reads a CSV file and returns the mean, median and standard deviation of every numeric column. Use type hints and a docstring. Output only the code.' 768
$null = Invoke-Chat 'json' 'Return a JSON array of 25 objects for fictional users with the fields id, name, email, city and age. Output only the JSON.' 768
$null = Invoke-Chat 'prose' 'Explain in about 300 words how speculative decoding with a multi-token-prediction head speeds up LLM inference.' 768
if ($script:Results.Count -gt 0) {
  $avg = ($script:Results | Measure-Object -Property tps -Average).Average
  Write-Host ('RESULT avg    decode {0:N1} tok/s over {1} prompts (target 100+)' -f $avg, $script:Results.Count)
}
Show-Vram 'after short prompts'

if ($Long) {
  Write-Host '== 4/4 long prompt: about 110K-135K tokens + a needle in the middle (takes minutes)'
  $sb = New-Object Text.StringBuilder
  $lines = 3800
  for ($i = 1; $i -le $lines; $i++) {
    if ($i -eq [int]($lines / 2)) { [void]$sb.AppendLine('Note: the secret passphrase for the audit is BLUE-HARBOR-7431.') }
    [void]$sb.AppendLine(('Line {0}: the warehouse report lists {1} crates, {2} pallets and {3} shipping manifests for depot {4}.' -f $i, (($i * 7) % 97), (($i * 13) % 89), (($i * 3) % 41), ($i % 17)))
  }
  $q = $sb.ToString() + "`nWhat is the secret passphrase for the audit? Answer with the passphrase only."
  $r = Invoke-Chat 'long' $q 512
  if ($r) {
    $ans = "$($r.choices[0].message.content)"
    if ($ans -match 'BLUE-HARBOR-7431') { Write-Host '   needle: FOUND' } else { Write-Host ('   needle: NOT found. answer = ' + $ans.Substring(0, [math]::Min(200, $ans.Length))) }
  }
  Show-Vram 'after long prompt'
} else {
  Write-Host '== 4/4 long prompt skipped - run "Swift15-bench.bat long" to test 150K'
}

Write-Host ''
Write-Host ('Saved: ' + $Out)
Write-Host 'Paste that file, or the RESULT lines, into the chat.'
Stop-Transcript | Out-Null
