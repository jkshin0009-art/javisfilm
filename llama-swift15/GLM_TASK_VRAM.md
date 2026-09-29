# 작업 지시서: Swift15 속도 저하 원인 확인 — VRAM 넘침 검사 (실행 담당용)

## 왜 하는가

지난 보고(`SWIFT15_REPORT.md`)에서 프롬프트 처리가 36~122 tok/s, 생성이 11.8 tok/s였다. RTX 3090에서 27B Q4 모델은 보통 프롬프트 처리가 1000 tok/s 이상, 생성이 30 tok/s 이상이다. 적재 뒤 GPU0 사용량이 23919 / 24576 MiB로 거의 꽉 차 있었다.

분석 담당의 추정은 이렇다. VRAM이 모자라서 Windows 드라이버가 일부를 **공유 GPU 메모리(시스템 RAM)**로 넘겼다. 그래서 PCIe를 거치느라 수십 배 느려졌다. 13:30에 IDE가 GPU0 메모리를 더 잡으면서 0.12 tok/s까지 떨어진 것도 같은 원인으로 설명된다.

이 지시서는 그 추정이 맞는지 **숫자로 확인**한다. 서버별 "공유 메모리 사용량"을 직접 읽고, 150K와 32K를 비교한다.

## 반드시 지킬 규칙

1. **사용자가 정한 시간에만:** 5678은 프로젝트 LLM 자리다. 이 시험은 GPU0를 쓰므로, 사용자가 "지금 해도 된다"고 한 뒤에만 시작한다. 시험 서버는 **5679 포트**로 띄워서 프로젝트 클라이언트가 잘못 붙지 않게 한다.
2. **다른 프로세스는 건드리지 않는다.** ComfyUI(GPU1)도 그대로 둔다. 배치 파일을 고치지 않는다.
3. 확인 기준을 못 넘으면 멈추고, 그때까지를 보고한다. 출력은 원문 그대로 붙인다.
4. 셸은 PowerShell 기준이다.

## V1. 준비

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
git -C $R pull
$S = "$R\llama-swift15"
Select-String -Path "$S\Swift15-27B-MTP-150K.bat" -Pattern 'SWIFT_PORT' | ForEach-Object { $_.Line }
nvidia-smi --query-gpu=index,memory.used,memory.free,memory.total --format=csv
Get-NetTCPConnection -LocalPort 5679 -State Listen -ErrorAction SilentlyContinue
```

확인 기준: 배치에 `SWIFT_PORT` 줄이 있고, 5679에 리스너가 없다.

## V2. 측정 함수 (한 번 붙여 넣고 V3, V4에서 씀)

```powershell
function Measure-Swift([string]$Tag, [string]$Ctx) {
  $S = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\llama-swift15'
  $Log = 'D:\llama.cpp\swift15_150k_server.log'
  $env:SWIFT_PORT = '5679'; $env:CTX = $Ctx; $env:SPEC_N = '2'
  $bat = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', "`"$S\Swift15-27B-MTP-150K.bat`"" -PassThru
  $ok = $false
  for ($i = 0; $i -lt 180; $i++) {
    Start-Sleep 2
    try { if ((Invoke-RestMethod 'http://127.0.0.1:5679/health' -TimeoutSec 2).status -eq 'ok') { $ok = $true; break } } catch {}
  }
  "== $Tag ctx=$Ctx ready=$ok"
  $srv = Get-CimInstance Win32_Process -Filter "Name='llama-server.exe'" | Where-Object { $_.CommandLine -match '--port 5679' }
  "server pid=$($srv.ProcessId)"
  nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv
  $pidTag = "pid_$($srv.ProcessId)_*"
  (Get-Counter "\GPU Process Memory($pidTag)\Dedicated Usage", "\GPU Process Memory($pidTag)\Shared Usage" -ErrorAction SilentlyContinue).CounterSamples |
    ForEach-Object { "{0,-70} {1,8:N0} MiB" -f $_.Path, ($_.CookedValue / 1MB) }
  if ($ok) {
    $env:SWIFT_URL = 'http://127.0.0.1:5679'; $env:BENCH_NOPAUSE = '1'
    cmd /c "`"$S\Swift15-bench.bat`"" | Select-String 'RESULT|VRAM'
    (Get-Counter "\GPU Process Memory($pidTag)\Shared Usage" -ErrorAction SilentlyContinue).CounterSamples |
      ForEach-Object { "after bench shared: {0:N0} MiB" -f ($_.CookedValue / 1MB) }
  }
  if ($srv) { Stop-Process -Id $srv.ProcessId -Force }
  Stop-Process -Id $bat.Id -Force -ErrorAction SilentlyContinue
  Start-Sleep 5
  Remove-Item Env:SWIFT_PORT, Env:CTX, Env:SPEC_N, Env:SWIFT_URL -ErrorAction SilentlyContinue
  "port 5679 free: " + (-not (Get-NetTCPConnection -LocalPort 5679 -State Listen -ErrorAction SilentlyContinue))
}
```

## V3. 150K 측정

```powershell
Measure-Swift 'A' '150000'
```

## V4. 32K 측정

```powershell
Measure-Swift 'B' '32768'
```

확인 기준(V3, V4 각각): `ready=True`, `RESULT` 줄이 있다, 마지막에 `port 5679 free: True`.

## V5. 보고

`$S\reports\SWIFT15_VRAM.md`에 V1~V4 출력을 원문 그대로 붙이고, 끝에 아래 표를 채운다.

| 조건 | GPU0 사용 MiB | 서버 Dedicated MiB | 서버 Shared MiB | 프롬프트 tok/s(3개) | 생성 tok/s avg | MTP 수용률 |
|---|---|---|---|---|---|---|
| A 150K | | | | | | |
| B 32K | | | | | | |

사용자에게 보여 주고, 허락하면 `llama-swift15/reports`만 add해서 commit·push한다. push가 실패하면 보고서 전문을 화면에 출력한다.
