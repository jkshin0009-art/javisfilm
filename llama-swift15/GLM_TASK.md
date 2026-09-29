# 작업 지시서: Swift 1.5 150K MTP 서버 검증 (실행 담당용)

목표는 RTX 3090(GPU0)에서 `Swift15-27B-MTP-150K.bat`으로 llama-server를 띄우고, 150K 컨텍스트·8비트 KV·MTP가 실제로 동작하는지와 속도(tok/s)를 측정해 보고서로 남기는 것이다.
분석은 다른 담당이 하므로, 이 문서는 **실행하고 결과를 그대로 기록**하는 것까지만 한다.

작업 폴더는 프로젝트 폴더 `C:\Users\Administrator\Desktop\film_assistant` 안의 git 저장소 `C:\Users\Administrator\Desktop\film_assistant\javisfilm`이다(아래 `$R`). 배치 파일은 `C:\Users\Administrator\Desktop\film_assistant\javisfilm\llama-swift15`에 있다.

llama.cpp 프로그램(`D:\llama.cpp\src_mtp`), 모델(`D:\LM-Studio\models`), 서버 로그(`D:\llama.cpp\swift15_150k_server.log`)는 원래 있던 D 드라이브 위치를 그대로 쓴다. 이 경로들은 바꾸지 않는다.

## 반드시 지킬 규칙

1. **건드리지 말 것:** 기존 `Swift15-27B-MTP.bat`, ComfyUI(GPU1, 포트 8189), 이 문서에 나오지 않는 다른 프로세스와 파일.
2. **배치 파일을 수정하지 말 것:** 수정이 필요해 보이면 멈추고 보고서에 이유를 적는다.
3. **확인 기준을 못 넘으면 멈출 것:** 각 단계의 확인 기준을 통과하지 못하면 다음 단계로 가지 않는다. 그때까지의 결과로 9단계 보고서를 만들고 끝낸다.
4. **출력을 요약하지 말 것:** 명령 출력은 보고서에 원문 그대로 붙인다. 추측으로 채우지 않는다.
5. **셸:** 명령은 PowerShell 기준이다. bash에서 실행 중이면 명령을 `.ps1` 파일로 저장하고 `powershell -NoProfile -ExecutionPolicy Bypass -File <파일>`로 실행한다.

## 1단계: 저장소 받기 (이미 있으면 최신으로 갱신)

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
if (Test-Path "$R\.git") { git -C $R pull } else { git clone -b claude/affectionate-brahmagupta-24a19d https://github.com/jkshin0009-art/javisfilm $R }
git -C $R log --oneline -3
Get-ChildItem "$R\llama-swift15\*.bat" | Select-Object Name, Length
```

확인 기준: `Swift15-27B-MTP-150K.bat`과 `Swift15-bench.bat`이 있다.

## 2단계: llama.cpp 빌드가 필요한 옵션을 지원하는지 확인

```powershell
$exe = 'D:\llama.cpp\src_mtp\build-faq\bin\llama-server.exe'
if (-not (Test-Path $exe)) { $exe = 'D:\llama.cpp\src_mtp\build\bin\Release\llama-server.exe' }
"exe: $exe"
& $exe --version 2>&1 | Select-Object -First 5
$h = (& $exe --help 2>&1 | Out-String)
foreach ($o in '-ctkd', '-ctvd', '--spec-type', 'draft-mtp', '--spec-draft-n-max', '--spec-draft-backend-sampling', '--fit', '--reasoning-budget-message', '--log-file', 'q8_0') {
  '{0,-32} {1}' -f $o, $h.Contains($o)
}
```

확인 기준: 모든 줄이 `True`다. `False`가 하나라도 있으면 멈춘다.

## 3단계: 포트와 VRAM 확인

```powershell
Get-NetTCPConnection -LocalPort 5678 -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object { Get-Process -Id $_.OwningProcess | Select-Object Id, ProcessName, Path }
nvidia-smi --query-gpu=index,name,memory.used,memory.free,memory.total --format=csv
```

확인 기준:
- 첫 명령의 출력이 비어 있다(5678 포트가 비어 있음). 사용 중이면 그 프로세스를 끄지 말고 멈춘다.
- GPU0의 `memory.free`를 기록해 둔다.

## 4단계: 서버 시작 (MTP 드래프트 2개)

```powershell
$B = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\llama-swift15'
$env:SPEC_N = '2'
Start-Process -FilePath "$B\Swift15-27B-MTP-150K.bat"
$log = 'D:\llama.cpp\swift15_150k_server.log'
$t = Get-Date; $ready = $false
while (((Get-Date) - $t).TotalMinutes -lt 15) {
  Start-Sleep -Seconds 10
  if ((Test-Path $log) -and (Select-String -Path $log -Pattern 'listening on' -Quiet)) { $ready = $true; break }
}
"ready: $ready  (" + [int]((Get-Date) - $t).TotalSeconds + " s)"
if (-not $ready -and (Test-Path $log)) { Get-Content $log -Tail 60 }
```

- 배치는 새 창에서 돈다. 벤치 결과 txt는 `llama-swift15` 폴더에 저장된다.
- 메모리가 부족하면 배치가 알아서 KV 모드를 낮춰 다시 시작하므로 기다리기만 하면 된다.

확인 기준: `ready: True`. 15분이 지나도 `False`면 로그 끝부분을 보고서에 붙이고 멈춘다.

## 5단계: 로그에서 메모리와 설정 정보 뽑기

```powershell
$log = 'D:\llama.cpp\swift15_150k_server.log'
Select-String -Path $log -Pattern 'llama_kv_cache|memory_recurrent|model buffer size|compute buffer size|n_ctx|n_seq|MTP|mtp|nextn|draft|flash_attn|type_k|type_v|warn|error' |
  Select-Object -First 100 | ForEach-Object { $_.Line }
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv
```

확인 기준: 출력이 있다. 이 단계는 결과를 기록만 하고, 판단은 하지 않는다.

## 6단계: 짧은 벤치 (프롬프트 3개)

```powershell
$B = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\llama-swift15'
$env:BENCH_DIR = "$B\"; $env:BENCH_ARGS = ''
powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ([IO.File]::ReadAllText('$B\Swift15-bench.bat'))"
```

확인 기준:
- `RESULT avg` 줄이 있다.
- `MTP accept` 값이 `n/a`가 아니다.

## 7단계: 긴 벤치 (150K 컨텍스트, 5~15분 걸림)

```powershell
$B = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\llama-swift15'
$env:BENCH_DIR = "$B\"; $env:BENCH_ARGS = 'long'
powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ([IO.File]::ReadAllText('$B\Swift15-bench.bat'))"
```

확인 기준:
- `RESULT long` 줄의 prompt 토큰 수가 100000보다 크다.
- `needle: FOUND`가 나온다.
- 실패해도 출력을 기록하고 8단계로 넘어간다.

## 8단계: MTP 드래프트 3개와 비교

먼저 서버를 끈다. 배치 창을 먼저 끄지 않으면 배치가 서버를 다시 켜므로 순서를 지킨다.

```powershell
Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" | Where-Object { $_.CommandLine -match 'Swift15-27B-MTP-150K' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Sleep -Seconds 2
Get-CimInstance Win32_Process -Filter "Name='llama-server.exe'" | Where-Object { $_.CommandLine -match '--port 5678' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Sleep -Seconds 5
```

그다음 4단계 명령에서 `$env:SPEC_N = '2'`를 `'3'`으로 바꿔 실행하고, 6단계 명령(짧은 벤치)을 한 번 더 실행한다. 끝나면 위의 종료 명령으로 서버를 다시 끈다.

## 9단계: 보고서 작성

`C:\Users\Administrator\Desktop\film_assistant\javisfilm\llama-swift15\reports\SWIFT15_REPORT.md`를 만든다. 아래 항목마다 해당 단계의 출력을 **원문 그대로** 붙인다.

1. 1단계: `git log` 3줄
2. 2단계: exe 경로, `--version`, 옵션별 True/False
3. 3단계: 포트 결과, 시작 전 `nvidia-smi`
4. 4단계: `ready` 결과와 걸린 시간. 실패했다면 로그 끝부분
5. 5단계: 로그에서 뽑은 줄 전체, 로드 후 `nvidia-smi`
6. 6단계(SPEC_N=2): `RESULT` 줄 전체와 VRAM 줄
7. 7단계(long): `RESULT long` 줄, needle 결과, VRAM 줄
8. 8단계(SPEC_N=3): `RESULT` 줄 전체
9. 멈춘 단계가 있으면 그 단계와 이유
10. 규칙 2 때문에 하지 않은 수정 제안이 있으면 그 내용

## 10단계: 보고서를 저장소에 올리기

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
New-Item -ItemType Directory -Force "$R\llama-swift15\reports" | Out-Null
Move-Item "$R\llama-swift15\swift15_bench_*.txt" "$R\llama-swift15\reports\" -Force -ErrorAction SilentlyContinue
git -C $R pull
git -C $R add llama-swift15/reports
git -C $R commit -m "Add Swift15 150K MTP test report"
git -C $R push
```

- 이 저장소는 공개 저장소다. 보고서에 API 키, 비밀번호, 토큰이 들어가지 않았는지 올리기 전에 확인한다.
- push가 실패하면(권한 오류 등) 억지로 해결하지 말고, `SWIFT15_REPORT.md` 전체 내용을 화면에 출력한다. 사용자가 복사해 분석 담당에게 전달한다.
- push가 성공하면 커밋 해시를 화면에 출력한다.
