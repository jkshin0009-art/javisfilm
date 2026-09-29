# 작업 지시서: 챗봇에 판단 기능 연결 (실행 담당용)

목표는 `chat-upgrade`의 Jev식 판단을 film_assistant 챗봇의 여섯 자리에 **스위치로** 붙이는 것이다. 스위치의 기본값은 `off`이고, `off`이면 지금과 똑같이 동작한다. 붙인 뒤 사용자가 `observe`(판단만 기록, 동작은 그대로)로 한 번 대화해 보고, 기록을 보고 자리마다 `act`(판단대로 동작)를 켤지 정한다.

| 자리 | 파일 (연결 지도 기준) | 지금 | 판단을 붙이면 |
|---|---|---|---|
| H1 think | `conversation/llm.py` `llm_stream()` | `<think>` 제거 없음 | 스트림에서 `<think>…</think>`와 특수 토큰을 걸러 냄 |
| H2 image | `visuals/storyboard.py:325` | `IMAGE_FORCE_RE`(그려·이미지·컷·장면·보여…)가 맞으면 이미지 생성 | 정규식이 맞았을 때만 "정말 그림을 원하나"를 물어 거짓 양성을 거름 |
| H3 autonomy | `turns/companion.py` `companion_loop()` | 모델이 STOP을 쓰기 전까지 자율 발화 | 자율 발화 직전에 "대답을 기다리는 중인가"를 물음 |
| H4 speaker | `orchestrator.py` | 경질 규칙으로 다음 화자 결정 | 허용된 후보 중 누가 말할지 물음 |
| H5 addressed | `turns/multi_persona.py:68` 뒤 | 이름 언급이 없으면 지목 없음 | 언급이 없을 때 누구에게 한 말인지 물음 |
| H6 stuck | `turns/multi_persona.py:208` `_decide_next_cycle_action()` | 10턴마다 규칙으로 continue/pause | 대화가 제자리를 도는지 물어, 돌면 pause |

- **저장소:** `C:\Users\Administrator\Desktop\film_assistant\javisfilm` (아래 `$R`), 도구 폴더 `$R\chat-upgrade` (아래 `$C`)
- **프로젝트:** `C:\Users\Administrator\Desktop\film_assistant` (아래 `$P`)

## 반드시 지킬 규칙

1. **사용자 허락 뒤에만 고칠 것:** I3에서 사용자가 허락하기 전에는 film_assistant 파일을 하나도 고치지 않는다.
2. **기본값은 지금과 같을 것:** 모든 연결은 `off`일 때 원래 코드와 똑같이 동작해야 한다. 원래 코드는 지우지 말고 감싼다.
3. **자리마다 커밋 하나:** film_assistant의 **현재 브랜치**에 `chatup:`으로 시작하는 커밋을 자리마다 하나씩 만든다(되돌리기는 `git revert <해시>`). 커밋 전에 그 자리의 diff를 사용자에게 보여 준다. `git add`는 그 자리에서 고친 파일만 한다. 다른 사람이 고치던 파일(작업 전부터 `git status`에 보이던 파일)은 건드리지 않는다. 그 파일을 고쳐야 하면 멈추고 묻는다.
4. **재시작하지 말 것:** 앱, LLM, TTS, ComfyUI를 켜거나 끄지 않는다. 새 코드는 사용자가 앱을 다시 켤 때 적용된다.
5. **내용은 적지 말 것:** 보고서에는 파일 경로, 줄 번호, 함수 이름, 바꾼 줄 수만 적는다. 대사와 인물 설정 문장은 적지 않는다. 판단 기록(`data\judge_logs\`)은 올리지 않는다.
6. **셸:** PowerShell 기준이다.

## I0. 저장소 갱신과 테스트

로컬에 올리지 못한 보고서 커밋이 있으므로 `--rebase`로 받는다.

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$C = "$R\chat-upgrade"
git -C $R pull --rebase
git -C $R log --oneline -5
Push-Location $C
& "$C\.venv\Scripts\python.exe" -m pytest -q tests
Pop-Location
```

확인 기준: 마지막 줄이 `63 passed`이다. `chatup\bridge.py`가 있다.

## I1. 지금 LLM 서버의 VRAM 넘침 확인 (읽기만)

5678 서버를 끄거나 다시 켜지 않고 숫자만 읽는다. 공유(Shared) 사용량이 크면, 판단과 대사 생성이 느린 원인이 VRAM 넘침이라는 뜻이다.

```powershell
$srv = Get-CimInstance Win32_Process -Filter "Name='llama-server.exe'" | Where-Object { $_.CommandLine -match '--port\s+5678' }
"pid=$($srv.ProcessId)"
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv
foreach ($id in $srv.ProcessId) {
  (Get-Counter "\GPU Process Memory(pid_$($id)_*)\Dedicated Usage", "\GPU Process Memory(pid_$($id)_*)\Shared Usage" -ErrorAction SilentlyContinue).CounterSamples |
    ForEach-Object { "{0,-80} {1,8:N0} MiB" -f $_.Path, ($_.CookedValue / 1MB) }
}
```

## I2. 판단 점검 다시 (probe 19건)

이번 판에서 바뀐 점은 세 가지다.
- `should_speak`를 "대화 상태 고르기"로 바꿨다.
- 이미지 판단 3건을 추가했다. 그중 2건은 '장면', '보여'가 들어 있지만 그림 요청이 아닌 경우다.
- 판단 요청 두 개를 동시에 보낸다.

영화 작업이 LLM을 쓰는 중이면 사용자에게 먼저 묻는다.

```powershell
$C = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\chat-upgrade'
Push-Location $C
& "$C\.venv\Scripts\python.exe" -m chatup probe --url http://127.0.0.1:5678 --report "$C\reports\CHAT_PROBE2.md"
Pop-Location
```

확인 기준: `RESULT` 줄 5개가 나오고 `CHAT_PROBE2.md`가 생겼다.

## I3. 사용자 허락 받기

사용자에게 아래를 보여 주고, film_assistant 코드를 고쳐도 되는지 묻는다. 안 된다고 하면 I8로 가서 I0~I2만 보고한다.
- 새로 만드는 것: `$P\chatup\`(복사본), `$P\core\judge_hook.py`, `$P\judge_modes.json`
- 고치는 파일: `conversation/llm.py`, `visuals/storyboard.py`, `turns/companion.py`, `orchestrator.py`, `turns/multi_persona.py`
- 기본값은 `off`이고, `off`이면 지금과 똑같이 동작한다는 것. 자리마다 커밋이 따로 있어서 하나씩 되돌릴 수 있다는 것.

허락을 받으면 시작 상태를 기록한다.

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
git -C $P branch --show-current
git -C $P log --oneline -3
git -C $P status --short | Measure-Object -Line
git -C $P status --short -- conversation/llm.py visuals/storyboard.py turns/companion.py orchestrator.py turns/multi_persona.py core/config.py
Test-Path "$P\chatup"
```

확인 기준: `$P\chatup`이 없다(`False`). 고칠 파일 다섯 개가 `git status`에 이미 보이면(누가 고치는 중이면) 그 파일은 사용자에게 묻고 정한다.

## I4. chatup 복사와 연결 모듈

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$P = 'C:\Users\Administrator\Desktop\film_assistant'
robocopy "$R\chat-upgrade\chatup" "$P\chatup" /E /XD __pycache__ /NFL /NDL /NJH /NJS
"vendored from javisfilm chat-upgrade/chatup at " + (git -C $R rev-parse --short HEAD) | Set-Content -Encoding utf8 "$P\chatup\VENDORED_FROM.txt"
'{"default": "off"}' | Set-Content -Encoding utf8 "$P\judge_modes.json"
Get-ChildItem "$P\chatup" -Name
```

`$P\core\judge_hook.py`를 아래 내용 그대로 만든다. `USER_LABEL`은 프로젝트 대화 기록에서 사용자를 부르는 이름으로 맞춘다(기록 형식을 보고 정한다).

```python
"""Jev-style judgments behind switches (chatup.bridge).

Modes live in judge_modes.json at the project root and are re-read while the app
runs: {"default": "off"} changes nothing; "observe" only logs what the judge would
do; "act" lets a confident judgment decide. Per place: think, image, autonomy,
speaker, addressed, stuck. Logs: data/judge_logs/hooks.jsonl (no conversation text).
"""
import os
import threading

from chatup.bridge import JudgeBridge
from core import config

USER_LABEL = "사용자"
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOCK = threading.Lock()
_BRIDGE = None


def bridge() -> JudgeBridge:
    global _BRIDGE
    with _LOCK:
        if _BRIDGE is None:
            os.environ.setdefault("FJ_JUDGE_LOG", os.path.join(_ROOT, "data", "judge_logs"))
            os.environ.setdefault("FJ_JUDGE_FILE", os.path.join(_ROOT, "judge_modes.json"))
            base = os.environ.get("FJ_JUDGE_URL") or config.LLM_URL
            _BRIDGE = JudgeBridge.from_env(base, user_name=USER_LABEL)
        return _BRIDGE


def mode(place: str) -> str:
    try:
        return bridge().mode(place)
    except Exception:
        return "off"


def safe(fn, baseline):
    """Run a hook; any error in building its input returns the baseline."""
    try:
        return fn()
    except Exception:
        return baseline
```

확인 기준(프로젝트가 쓰는 파이썬으로 실행한다. `run_film_assistant.bat`에서 어느 python인지 확인한다):

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
$Py = 'python'   # run_film_assistant.bat 이 쓰는 파이썬 경로로 바꾼다
Push-Location $P
& $Py -c "from core.judge_hook import bridge, mode; b = bridge(); print('image', mode('image'), 'log', b.log_path)"
Pop-Location
```

출력이 `image off log ...\data\judge_logs\hooks.jsonl`이다. 여기까지를 커밋 하나로 만든다: `chatup: vendor judge bridge (all places off)`.

## I5. 자리마다 연결

아래는 자리마다 **하는 일**과 **틀**이다. 실제 변수 이름은 그 함수의 코드를 읽고 맞춘다.

모든 자리에 공통인 규칙이 있다.
- **최근 기록:** 대화 기록을 `(말한 사람, 대사)` 쌍 목록으로 넘긴다. 최근 10줄이면 충분하다. 사용자는 `USER_LABEL`, 인물은 표시 이름으로 적는다. 대사에서 `EMOTION:`, `SCENE:` 줄과 속마음 괄호는 빼고 넘긴다. 그 자리에서 기록을 얻을 수 없으면 있는 것만 넘기고 보고서에 적는다.
- **safe로 감쌀 것:** 입력을 만드는 코드는 `safe(lambda: ..., baseline)`로 감싼다. 판단 쪽에서 무슨 일이 나도 원래 값으로 돌아가게 하기 위해서다.
- **자리마다 커밋:** 한 자리를 고칠 때마다 diff를 보여 주고, `py_compile`을 통과한 뒤 커밋한다.

### H1 think — `conversation/llm.py` `llm_stream()`

SSE 루프에서 `delta`의 content 조각을 받는 곳에 붙인다.

```python
from core.judge_hook import bridge as _judge, mode as _judge_mode
...
tf = _judge().think_filter() if _judge_mode("think") != "off" else None
...
    piece = <받은 조각>
    if tf is not None:
        piece = tf.feed(piece)
        if not piece:
            continue            # 걸러진 조각은 on_token 에도 넘기지 않는다
...
# 스트림이 끝난 뒤(끼어들기로 끝난 경우 포함)
if tf is not None:
    tail = tf.flush()
    # tail 이 있으면 원래 조각과 같은 방식으로 본문과 on_token 에 넘긴다
```

첫 문장을 TTS로 먼저 보내는 동작(`on_token`)은 바꾸지 않는다. 커밋: `chatup: H1 think filter in llm_stream`.

### H2 image — `visuals/storyboard.py:325`

정규식이 맞았고 `force_image`가 아닐 때만 묻는다. 정규식이 안 맞으면 묻지 않는다(요청이 늘지 않는다).

```python
from core.judge_hook import bridge as _judge, safe as _safe, USER_LABEL
...
matched = bool(IMAGE_FORCE_RE.search(user_text))
if matched and not force_image:
    matched = _safe(lambda: _judge().image(<최근 기록>, baseline=True), True)
if force_image or matched:
    ...  # 원래 코드
```

- `<최근 기록>`은 최소한 `[(USER_LABEL, user_text)]`이다.
- 자율 발화 턴에서 `user_text`가 무엇으로 채워지는지 확인해서 보고서에 적는다. 예를 들어 마지막 사용자 말이 계속 들어가서, 그 말에 '장면'이 있으면 자율 턴마다 정규식이 맞는지.
- 커밋: `chatup: H2 image gate on keyword trigger`.

### H3 autonomy — `turns/companion.py` `companion_loop()`

**자율 발화**(사용자 입력에 대한 답이 아닌 턴)를 시작하기 직전에 붙인다.

```python
from core.judge_hook import bridge as _judge, safe as _safe
...
speak = _safe(lambda: _judge().autonomy(<최근 기록>, baseline=True), True)
if not speak:
    # 이번 자율 턴을 건너뛰고 기다린다. 대기 중에도 연결·ACK 확인과 사용자 입력 처리는 원래대로 돈다.
    <원래 루프의 대기 방식으로 JUDGE_WAIT_SEC(8초) 기다린 뒤 continue>
```

- `off`이거나 `observe`이면 `speak`는 항상 `True`라서 지금과 같다.
- 죽은 탭 판정(`AUTO_DEAD_CLIENT_SEC`), `tts_go` 대기, 다른 탭 양보 규칙은 그대로 둔다.
- 커밋: `chatup: H3 autonomy gate`.

### H4 speaker — `orchestrator.py`

다음 화자를 정하는 곳에서, `max_same_speaker_turns` 같은 경질 규칙을 적용한 **뒤**의 후보 목록으로 묻는다.

```python
from core.judge_hook import bridge as _judge, safe as _safe
...
speaker = _safe(lambda: _judge().speaker(<최근 기록>, <허용된 후보 이름 목록>, baseline=speaker), speaker)
```

- 결과는 항상 후보 안에서 나온다. 후보가 하나면 묻지 않는다.
- 후보를 이름이 아니라 id로 다루는 코드이면, 이름↔id를 바꿔서 넘기고 받는다.
- 커밋: `chatup: H4 next speaker`.

### H5 addressed — `turns/multi_persona.py` `_resolve_persona_mentions()` 호출 뒤

이름 언급으로 지목된 인물이 **없을 때만** 묻는다.

```python
from core.judge_hook import bridge as _judge, safe as _safe
...
target = <원래 멘션 결과>
if not target:
    target = _safe(lambda: _judge().addressed(<최근 기록>, <인물 이름 목록>, baseline=None), None)
```

- 모두에게 한 말이면 `None`이 그대로 돌아온다(지금과 같다).
- 커밋: `chatup: H5 addressee when no mention`.

### H6 stuck — `turns/multi_persona.py:208` `_decide_next_cycle_action()`

원래 규칙의 결과가 `continue`일 때만 묻는다.

```python
from core.judge_hook import bridge as _judge, safe as _safe
...
action = <원래 규칙의 결과>
if action == "continue":
    looping = _safe(lambda: _judge().stuck(<최근 기록>, baseline=False), False)
    if looping:
        action = "pause"
```

- 사용자가 명시적으로 계속하라고 한 경우는 원래 규칙이 먼저 `continue`로 정한다. 이 경우는 묻지 않게 그 분기 안쪽으로 넣는다.
- 커밋: `chatup: H6 stuck check at cycle end`.

## I6. 확인

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
$Py = 'python'   # I4 에서 확인한 파이썬
Push-Location $P
& $Py -m py_compile conversation\llm.py visuals\storyboard.py turns\companion.py orchestrator.py turns\multi_persona.py core\judge_hook.py
"py_compile exit: $LASTEXITCODE"
git -C $P log --oneline -8
git -C $P status --short -- chatup core/judge_hook.py judge_modes.json
Pop-Location
```

- 프로젝트에 테스트가 있으면(예: `tests\`, `selftest`) I3 전에 한 번, 여기서 한 번 돌려 결과를 비교한다.
- `judge_modes.json`이 `{"default": "off"}`인지 확인한다.

확인 기준: `py_compile exit: 0`. 커밋이 7개(`vendor` 1개, H1~H6 6개)이다. 자리를 건너뛰었으면 그 이유를 적는다.

## I7. 사용자에게 알릴 것 (그대로 전달)

1. 새 코드는 **앱을 다시 켜야** 적용된다. 켜기 전까지는 아무것도 바뀌지 않는다.
2. 다시 켠 뒤 `film_assistant\judge_modes.json`을 `{"default": "observe"}`로 바꾸면, 앱을 끄지 않아도 2초 안에 적용된다. 20~30분 평소처럼 대화한다. 자율 대화, 여러 인물 대화, 그림 요청이 섞이면 좋다. 동작은 그대로이고, 판단이 기록만 된다.
3. 끝나면 `{"default": "off"}`로 되돌리고, 실행 담당에게 요약을 부탁한다.

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
$C = "$P\javisfilm\chat-upgrade"
Push-Location $C
& "$C\.venv\Scripts\python.exe" -m chatup report --log "$P\data\judge_logs\hooks.jsonl" --out "$C\reports\OBSERVE_1.md"
Pop-Location
```

요약에는 자리별 판단 횟수, 원래 동작과 같은 비율, 걸린 시간만 들어 있다. 대사와 이름은 들어 있지 않다.

## I8. 보고

`$C\reports\INTEGRATE_REPORT.md`에 아래를 적는다.
- I0~I2와 I6의 출력 원문
- 자리마다: 파일:줄, 붙인 함수 이름, 바꾼 줄 수, 커밋 해시, `<최근 기록>`을 어디서 가져왔는지(변수 이름), 건너뛴 것과 이유
- H2의 `user_text`가 자율 턴에서 무엇인지

사용자에게 보여 주고, 허락하면 `chat-upgrade/reports`만 add해서 커밋·push한다. push가 실패하면 `CHAT_PROBE2.md`와 `INTEGRATE_REPORT.md` 전문을 화면에 출력한다.
