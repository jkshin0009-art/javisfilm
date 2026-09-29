# 작업 지시서: 챗봇 판단 기능 점검과 연결 지도 (실행 담당용)

목표는 두 가지다.
1. `chat-upgrade`의 Jev식 판단이 **프로젝트가 지금 쓰는 LLM**에서 제대로 되는지, 판단 하나에 몇 ms가 걸리는지 잰다.
2. 프로젝트 챗봇 코드에서 부품을 붙일 자리를 찾아 **연결 지도**를 만든다.

분석 담당은 이 두 보고서를 받아서 프로젝트 챗봇에 붙이는 작업 지시를 쓴다. 이 문서는 **점검하고 기록**하는 것까지만 한다.

작업 폴더는 `C:\Users\Administrator\Desktop\film_assistant\javisfilm\chat-upgrade`이다(아래 `$C`).

## 반드시 지킬 규칙

1. **프로젝트를 고치지 말 것:** film_assistant의 코드, 설정, 데이터를 고치지 않는다. 서버(LLM, ComfyUI, TTS)를 켜거나 끄거나 재시작하지 않는다.
2. **바쁠 때 재지 말 것:** probe는 LLM에 짧은 요청을 약 50번 보낸다. 영화 작업(예: `julia_router.py`, `mv_*.py`, `server.py`의 배치 작업)이 LLM을 쓰는 중이면 probe를 돌리지 말고 사용자에게 언제 해도 되는지 묻는다.
3. **내용은 적지 말 것:** 연결 지도에는 파일 경로, 줄 번호, 함수 이름, 설정 항목 이름, 역할 한 줄만 적는다. 대사, 인물 설정 문장, 줄거리는 적지 않는다. API 키, 토큰, 비밀번호는 `***`로 가린다. 저장소가 공개 저장소다.
4. **출력은 원문 그대로:** 명령 출력은 요약하지 말고 붙인다. 모르는 것은 "확인 못 함"으로 적는다.
5. **셸:** PowerShell 기준이다. bash에서 실행 중이면 `.ps1`로 저장해 `powershell -NoProfile -ExecutionPolicy Bypass -File`로 실행한다.

## C1. 저장소 갱신

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
git -C $R pull
$C = "$R\chat-upgrade"
git -C $R log --oneline -3
Get-ChildItem "$C\chatup" -Name
```

확인 기준: `decide.py`, `judge.py`, `shaper.py`, `policy.py`, `voice.py`, `llm.py`, `loop.py`, `__main__.py`가 있다.

## C2. 테스트

프로젝트 파이썬 환경을 건드리지 않도록 `chat-upgrade` 안에 따로 가상환경을 만든다. 핵심 코드는 표준 라이브러리만 쓰고, 테스트에만 pytest가 필요하다.

```powershell
$C = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\chat-upgrade'
py -3.10 -m venv "$C\.venv"
if (-not $?) { py -3 -m venv "$C\.venv" }
& "$C\.venv\Scripts\python.exe" --version
& "$C\.venv\Scripts\python.exe" -m pip install -q pytest
Push-Location $C
& "$C\.venv\Scripts\python.exe" -m pytest -q tests
Pop-Location
```

확인 기준: 마지막 줄이 `50 passed`이다.

## C3. 챗봇이 쓰는 LLM 확인

survey 6장(챗봇)에서 확인한 **챗봇의 LLM 주소**를 `$URL`에 넣는다. survey에서 못 찾았으면 `http://127.0.0.1:5678`로 해 본다.

```powershell
$URL = 'http://127.0.0.1:5678'
try { Invoke-RestMethod "$URL/health" -TimeoutSec 5 | ConvertTo-Json -Compress } catch { "health failed: $($_.Exception.Message)" }
try {
  $p = Invoke-RestMethod "$URL/props" -TimeoutSec 5
  "alias=$($p.model_alias)  n_ctx=$($p.default_generation_settings.n_ctx)  slots=$($p.total_slots)  build=$($p.build_info)"
  "model_path=$($p.model_path)"
  "modalities=" + ($p.modalities | ConvertTo-Json -Compress)
} catch { "props failed: $($_.Exception.Message)" }
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'llama-server|julia_router|mv_extender|server\.py' } |
  ForEach-Object { "pid=$($_.ProcessId): $($_.CommandLine)" }
```

확인 기준: `/health`가 `ok`이다. 서버가 꺼져 있으면 켜지 말고 여기서 멈춘 뒤 사용자에게 알린다. 영화 작업 프로세스가 LLM을 쓰는 중이면 규칙 2에 따라 사용자에게 묻는다.

## C4. 판단 점검 (probe)

가상의 대화 16개(촬영 감독·작가·로케이션 담당이 나오는 지어낸 대화)로 판단을 물어 정답과 비교한다. 프로젝트 내용은 쓰지 않는다.

```powershell
$C = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\chat-upgrade'
$URL = 'http://127.0.0.1:5678'
Push-Location $C
& "$C\.venv\Scripts\python.exe" -m chatup probe --url $URL --report "$C\reports\CHAT_PROBE.md"
Pop-Location
```

확인 기준: `RESULT` 줄 5개가 나오고 `reports\CHAT_PROBE.md`가 만들어졌다. 정답 개수는 판정 대상이 아니다(분석 담당이 본다). 다음은 기록만 한다.
- `levels:`가 `none`이나 `parsed`이면 그대로 적는다(생각이 안 꺼졌거나 서버가 logprobs를 안 준다는 뜻).
- `decision ms`의 median과 max.

## C5. 연결 지도 (읽기만)

프로젝트 챗봇 코드(survey에 나온 `conversation/`, `turns/`, `tts/`, `transport/`, `workers/`, `app.py` 등)를 읽고, 아래 항목마다 **파일:줄, 함수 이름, 역할 한 줄**을 적는다. 여러 곳이면 모두 적는다.

| 번호 | 찾을 것 | 함께 적을 것 |
|---|---|---|
| a | 인물 대사를 만드는 LLM 요청 | 주소, 경로(`/v1/chat/completions` 등), 스트리밍 여부, 넘기는 설정 이름(temperature, max_tokens, stop, 생각 끄기 등), 메시지를 조립하는 방식(인물마다 시스템 프롬프트를 따로 쓰는지) |
| b | 다음 화자를 정하는 곳 | 규칙(순서, 무작위, 모델 지목 등) |
| c | 자율 발화 시점을 정하는 곳 | 타이머 간격, 멈추는 조건, 상한 |
| d | 사용자 입력이 들어오는 곳 | 말하는 중에 입력이 오면 끊는지(끼어들기), 기록에 어떻게 남는지 |
| e | dots.tts를 부르는 곳 | 함수 이름과 인자(텍스트, 참조 음성, 참조 문장, 언어 등), 돌려주는 것(파일, 배열, 스트림), 샘플레이트, 문장 단위로 자르는지 |
| f | 인물별 목소리를 저장하는 형식 | `casting.json`의 voice 항목 **키 이름**과 값의 형식(경로인지 이름인지), 참조 음성 파일 위치와 이름 규칙, 감정별 음성이 있는지 |
| g | 대화 중 이미지를 만드는 곳 | 어떤 조건에서 만드는지, 부르는 함수, ComfyUI 워크플로 이름 |
| h | 대화 기록 | 저장 위치, 길어지면 줄이는 방식 |
| i | 감정이나 표정 태그 | 모델 출력에 태그를 쓰는지, 쓰면 형식 |
| j | 모델 출력 후처리 | `<think>` 제거, 이름표 제거, 반복 검사 같은 처리가 있는지 |

결과를 `$C\reports\INTEGRATION_MAP.md`에 적는다. 표 형식으로 적고, 코드 인용은 함수 선언 줄과 요청 인자 줄 정도만 짧게 붙인다(대사·인물 설정 문장이 섞인 줄은 `***`로 가린다).

## C6. 보고와 push

1. 사용자에게 `reports\CHAT_PROBE.md`와 `reports\INTEGRATION_MAP.md`를 보여 주고 공개 저장소에 올려도 되는지 묻는다.
2. 된다고 하면 아래를 실행한다.

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
git -C $R pull
git -C $R add chat-upgrade/reports
git -C $R status --short
git -C $R commit -m "chat-upgrade: probe and integration map reports"
git -C $R push
```

- `git status --short`에 `chat-upgrade/reports/` 밖의 파일이 보이면 commit하지 말고 멈춘다.
- push가 실패하거나 사용자가 올리지 말라고 하면, 두 보고서 전문을 화면에 출력한다(사용자가 분석 담당에게 붙여 넣는다).
