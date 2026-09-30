# 작업 지시서: 스포츠 자세 자산을 콘티 프롬프트에 연결 (실행 담당용)

목표는 `sports-pose`의 스포츠 자세 자산 49개(12종목)를 film_assistant가 **콘티 컷의 이미지 프롬프트를 만들 때** 쓰게 하는 것이다.

컷 설명에 스포츠 동작이 나오면(예: "태권도 돌려차기", "투수가 공을 던지는 순간") 프롬프트 에이전트가 두 가지를 받는다.
- **자산 글:** 검사를 통과한 몸 동작 문장(관절 각도, 좌우, 손 모양, 발 접지, 상대를 잡는 위치)과 경기 규칙
- **OpenPose 그림:** 같은 뼈대의 컨트롤 이미지(이번에는 경로만 기록한다. ControlNet 연결은 다음 지시서)

연결은 chat-upgrade 때와 같은 방식이다. 스위치(`off` / `observe` / `act`)를 두고 **기본값은 `off`**, `off`이면 지금과 똑같이 동작한다.

진행은 네 부분이다.
- **S0~S3 (실행 담당, 읽기와 시험만):** 저장소 갱신, 자체 시험, 찾기 시험, 연결 지도
- **S4 (사용자):** 허락
- **S5~S7 (실행 담당, 허락 뒤):** 복사, 한 자리 연결, 확인
- **S8~S9:** 사용자에게 알릴 것, 보고

경로는 아래와 같이 부른다.
- **저장소:** `C:\Users\Administrator\Desktop\film_assistant\javisfilm` (아래 `$R`)
- **도구 폴더:** `$R\sports-pose` (아래 `$S`)
- **프로젝트:** `C:\Users\Administrator\Desktop\film_assistant` (아래 `$P`)

## 반드시 지킬 규칙

1. **허락 뒤에만 고칠 것:** S4에서 사용자가 허락하기 전에는 film_assistant 파일을 하나도 고치지 않는다. S0~S3은 읽기와 시험만 한다.
2. **기본값은 지금과 같을 것:** `sports_modes.json`은 `{"default": "off"}`로 만든다. `off`이면 원래 코드와 똑같이 동작해야 한다. 원래 코드는 지우지 말고 감싼다.
3. **단계마다 커밋 하나:** film_assistant의 **현재 브랜치**에 `sportspose:`로 시작하는 커밋을 만든다(되돌리기는 `git revert <해시>`).
   - 커밋 전에 diff를 사용자에게 보여 준다.
   - `git add`는 그 단계에서 만들거나 고친 파일만 한다. `javisfilm` 폴더는 절대 add하지 않는다.
   - 작업 전부터 `git status`에 보이던 파일(다른 사람이 고치던 파일)은 건드리지 않는다. 그 파일을 고쳐야 하면 멈추고 묻는다.
4. **재시작하지 말 것:** 앱, LLM(5678), ComfyUI(8189), TTS를 켜거나 끄지 않는다. ComfyUI의 워크플로, 노드, 모델, 설정도 바꾸지 않는다. ControlNet은 이번에 **조사만** 한다.
5. **내용은 적지 말 것:** 저장소는 공개 저장소다.
   - 보고서에는 파일:줄, 함수 이름, 키 이름, 개수, 자산 코드, 시간만 적는다.
   - 줄거리, 대사, 콘티 설명, 프롬프트 문장, 인물 외모 설명은 적지 않는다. 콘티 폴더 이름도 내용이 드러날 수 있으니 `board 1`, `board 2`처럼 번호로 바꾼다.
   - 기록 파일(`$P\data\sports_logs\`)은 올리지 않는다.
6. **멈출 것, 요약하지 말 것:** 확인 기준을 통과하지 못하면 다음 단계로 가지 않고 그때까지를 보고서에 적는다. 명령 출력은 보고서에 원문 그대로 붙인다. 추측으로 채우지 않는다.
7. **셸:** PowerShell 기준이다. bash에서 실행 중이면 `.ps1`로 저장해 `powershell -NoProfile -ExecutionPolicy Bypass -File`로 실행한다.

---

## S0. 저장소 갱신

새 도구는 브랜치 `claude/intelligent-lamport-p19iv3`에 있다. 지금 브랜치를 바꾸지 말고 **병합**한다. 병합하면 PC에만 있는 보고서 커밋과 다른 도구(h3-multicast, chat-upgrade, board-check, h3-prompt)가 그대로 남는다. 이 브랜치는 `sports-pose` 폴더만 더하므로 충돌은 나지 않아야 한다.

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
git -C $R branch --show-current
git -C $R status --short
git -C $R pull --rebase
git -C $R fetch origin claude/intelligent-lamport-p19iv3
git -C $R merge --no-edit origin/claude/intelligent-lamport-p19iv3
git -C $R log --oneline -5
Test-Path "$R\sports-pose\sportslook.py", "$R\sports-pose\library\index.json", "$R\sports-pose\library\sequences.json"
```

- `git status`에 고친 파일이 보이면(작업 중인 파일이 있으면) 병합하지 말고 멈추고 묻는다.
- 병합에서 충돌이 나면 `git -C $R merge --abort`로 되돌리고, 충돌한 파일 이름을 보고한다.
- 병합 커밋은 S9에서 보고서와 함께 push된다. 그 전에 다른 지시서의 `git pull --rebase`를 돌리지 않는다(병합 커밋이 풀린다).

확인 기준: 병합이 끝났고, 마지막 줄에 `True`가 세 번 나온다.

## S1. 자체 시험

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$S = "$R\sports-pose"
py -3 -c "import sys; print(sys.version)"
py -3 -m venv "$S\.venv"
& "$S\.venv\Scripts\python" -m pip install --upgrade pip
& "$S\.venv\Scripts\pip" install pillow pytest
Push-Location $S
& "$S\.venv\Scripts\python" -m pytest -q tests\test_sportslook.py -p no:cacheprovider
& "$S\.venv\Scripts\python" -m pytest -q tests -p no:cacheprovider
Pop-Location
```

- 파이썬 3.9 이상이어야 한다. `py -3`이 낮으면 `py -0p` 목록에서 골라 `py -3.12`처럼 지정한다.
- 첫 번째 시험(`test_sportslook.py`)은 1초 안에 끝난다. 프로젝트에 붙일 모듈의 시험이다.
- 두 번째는 전체 시험이고 5~10분 걸린다. 자세 엔진 전체를 다시 계산한다.

확인 기준:
- 첫 번째의 마지막 줄이 `41 passed`이다. 아니면 멈춘다.
- 두 번째의 마지막 줄이 `89 passed`이다. 몇 개만 실패하면(윈도에서만 생기는 경로·인코딩 문제일 수 있다) 실패한 시험 이름과 오류 원문을 적고 S2로 간다. 프로젝트는 첫 번째 모듈만 쓰기 때문이다.

## S2. 찾기 시험 (읽기만)

### S2a. 정해진 문장

```powershell
$S = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\sports-pose'
$Py = "$S\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
& $Py "$S\sportslook.py" match "태권도 선수가 상대 몸통에 돌려차기를 찬다"
& $Py "$S\sportslook.py" match "투수가 공을 던지는 순간"
& $Py "$S\sportslook.py" match "민지가 카페에서 커피를 마신다"
& $Py "$S\sportslook.py" match "배우 블로킹을 맞춘다"
$j = (& $Py "$S\sportslook.py" pack "유도 업어치기, 측면" --subject "SUBJECT_LOOK" --setting "SETTING_TEXT" --partner "B=PARTNER_LOOK") -join "`n" | ConvertFrom-Json
"code=$($j.code) camera=$($j.camera) size=$($j.size -join 'x') unfilled=$($j.unfilled.Count) control_exists=$(Test-Path $j.openpose_png) guide_chars=$($j.guide.Length)"
```

확인 기준:
- 첫 줄의 맨 앞 코드가 `TAEKWONDO_ROUNDHOUSE_KICK`, 둘째 줄이 `BASEBALL_PITCH_RELEASE`이다.
- 셋째, 넷째 줄은 `[]`이다. 일상 장면과 촬영 용어("블로킹")는 자산을 부르지 않아야 한다.
- 마지막 줄이 `code=JUDO_SEOI_NAGE camera=side size=1344x768 unfilled=0 control_exists=True`로 시작한다.

### S2b. 실제 콘티로 재기

최근 콘티 10개의 컷 설명에서 자산이 몇 번 불리는지, 그중 맞는 것이 몇 개인지 잰다.

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
$S = "$P\javisfilm\sports-pose"
$Py = "$S\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$M = Get-ChildItem $P -Recurse -Filter manifest.json -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|__pycache__|\.venv|venv|javisfilm|_trash|_checkpoint)\\' } |
  Sort-Object LastWriteTime -Descending | Select-Object -First 10
$M.Count
& $Py "$S\sportslook.py" scan @($M.FullName)
```

- 출력의 첫 칸(콘티 폴더 이름)은 보고서에 옮길 때 `board 1`~`board 10`으로 바꾼다.
- 마지막 줄 `panels N, with a sports asset K`에서 `N`이 0이면, 컷 설명이 다른 키에 있다는 뜻이다.
  - manifest 하나를 열어 컷 항목의 **키 이름만** 보고, 설명이 든 키를 `--keys desc_ko,visual`처럼 주고 다시 돌린다.
  - 쓴 키 이름을 보고서에 적는다.
- 불린 컷마다 그 컷의 설명을 **화면에서만** 읽고 판정한다. 설명은 보고서에 옮기지 않는다.
  - **맞음:** 그 스포츠 동작을 보여 주는 컷이다.
  - **틀림:** 스포츠 동작이 아니거나 다른 동작이다.
  - **애매:** 판정하기 어렵다.
- 스포츠 동작이 있는데 불리지 않은 컷이 눈에 띄면, 그 개수와 동작 이름(예: "수영 배영", "골프 스윙")만 적는다. 자산이 없는 동작일 수 있다.

## S3. 연결 지도 (읽기만)

콘티 한 컷이 이미지 프롬프트가 되는 자리를 찾는다. `board-check\reports\QC_SURVEY.md`가 PC에 있으면 그 S1을 먼저 읽고 겹치는 조사는 건너뛴다.

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
Get-ChildItem $P -Recurse -Include *.py -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|__pycache__|\.venv|venv|javisfilm|_trash|_checkpoint)\\' } |
  Select-String -Pattern 'image_prompt|build_prompt|make_prompt|prompt_for|positive|negative|workflow|comfy|ControlNet|controlnet|openpose|detailed_description' |
  Group-Object Path | Sort-Object Count -Descending | Select-Object -First 30 |
  ForEach-Object { "{0}  ({1})" -f $_.Name.Substring($P.Length), $_.Count }
Get-ChildItem $P -Recurse -Include *.json -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|javisfilm|_trash|_checkpoint|data)\\' } |
  Select-String -Pattern '"class_type"' -List | ForEach-Object { $_.Path.Substring($P.Length) }
```

아래 표를 채운다. 모르는 칸은 "모름"으로 두고 추측하지 않는다.

| 자리 | 적을 것 |
|---|---|
| C1 컷 프롬프트 | 컷 이미지 프롬프트를 만드는 파일:줄과 함수. **LLM이 쓰는지(A)**, **틀로 조립하는지(B)**. A이면 LLM 요청의 지시문이 어디서 오는지(시스템 메시지 변수 이름이나 파일). 입력(컷 설명 키)과 출력(프롬프트를 저장하는 키) |
| C2 인물과 장소 | 그 자리에서 쓸 수 있는 인물 외모(캐스트 `look` 같은 것)와 장소·빛 설명의 변수 이름이나 키. 컷에 나오는 인물 목록이 어디 있는지 |
| C3 워크플로 | 컷 그림을 만드는 ComfyUI 워크플로 파일 이름. 모델 계열(Flux, Qwen Image, SDXL 등). 노드 `class_type` 목록에 ControlNet 계열이 있는지. negative 입력을 쓰는지 |
| C4 ControlNet 모델 | ComfyUI의 `models\controlnet` 폴더 안 파일 이름 목록(이름만). 폴더 위치를 못 찾으면 "모름" |
| C5 컷 기록 | manifest의 컷 항목을 저장하는 파일:줄과 함수 |
| C6 영상 | H3 영상 프롬프트(`detailed_description`)를 만드는 파일:함수, LLM이 쓰는지 틀인지 |
| C7 파이썬 | `run_film_assistant.bat`이 쓰는 파이썬 경로. 프로젝트 테스트가 있는지와 실행 방법 |

## S4. 사용자 허락 받기

사용자에게 아래를 보여 주고, film_assistant 코드를 고쳐도 되는지 묻는다. 안 된다고 하면 S9로 가서 S0~S3만 보고한다.

- **새로 만드는 것:** `$P\core\sportslook.py`(복사본), `$P\core\sportslook_VENDORED_FROM.txt`, `$P\core\sports_hook.py`, `$P\sports_modes.json`
- **고치는 파일:** C1 파일 하나. C5가 다른 파일이면 그 파일도.
- **기본값:** `off`이고, `off`이면 지금과 똑같이 동작한다. 커밋이 단계마다 따로 있어서 하나씩 되돌릴 수 있다.
- **이번에 하지 않는 것:** ControlNet 연결과 H3 영상 연결. S3의 C3·C4·C6 조사 결과를 보고 다음 지시서로 정한다.

허락을 받으면 시작 상태를 기록한다.

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
git -C $P branch --show-current
git -C $P log --oneline -3
git -C $P status --short | Measure-Object -Line
Test-Path "$P\core\sportslook.py", "$P\core\sports_hook.py", "$P\sports_modes.json"
```

확인 기준: 마지막 줄이 `False`, `False`, `False`이다. C1(과 C5) 파일이 이미 `git status`에 보이면 사용자에게 묻고 정한다.

## S5. 복사와 스위치 모듈

`sportslook.py`는 표준 라이브러리만 쓰는 파일 하나다. 프로젝트에는 이 파일만 복사한다. 자산(그림과 글)은 복사하지 않고 `$P\javisfilm\sports-pose\library`에서 바로 읽는다.

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$P = 'C:\Users\Administrator\Desktop\film_assistant'
Copy-Item "$R\sports-pose\sportslook.py" "$P\core\sportslook.py"
"vendored from javisfilm sports-pose/sportslook.py at " + (git -C $R rev-parse --short HEAD) | Set-Content -Encoding utf8 "$P\core\sportslook_VENDORED_FROM.txt"
'{"default": "off"}' | Set-Content -Encoding utf8 "$P\sports_modes.json"
```

`$P\core\sports_hook.py`를 아래 내용 그대로 만든다.

```python
"""Sports pose assets for the storyboard prompt agent, behind a switch (core/sportslook.py).

sports_modes.json at the project root is re-read on every call:
  {"default": "off"}  nothing changes
  "observe"           logs which asset a panel would use (data/sports_logs/hooks.jsonl: codes and times only)
  "act"               returns the asset pack; the caller hands pack["guide"] to the prompt agent
Places: "prompt" (panel image prompt). "pose" (ControlNet) and "video" (H3) come in later steps.
The assets are read from javisfilm/sports-pose/library (SPORTS_POSE_LIBRARY overrides).
"""
import os

from core.sportslook import Hook

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = Hook(_ROOT)


def sports_pack(text, place="prompt", panel=None, **fill):
    """The asset pack for this panel text in act mode, else None. Never raises."""
    try:
        return HOOK.lookup(place, text, panel=panel, **fill)
    except Exception:
        return None
```

확인(프로젝트가 쓰는 파이썬으로 실행한다. C7에서 확인한 경로):

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
$Py = 'python'   # C7 에서 확인한 프로젝트 파이썬 경로로 바꾼다
Push-Location $P
& $Py -c "from core.sports_hook import HOOK, sports_pack; print('mode', HOOK.mode('prompt'), 'assets', len(HOOK.library().rows), 'pack', sports_pack('유도 업어치기'))"
Pop-Location
```

확인 기준: 출력이 `mode off assets 49 pack None`이다.

여기까지를 커밋 하나로 만든다. add할 파일은 `core/sportslook.py`, `core/sportslook_VENDORED_FROM.txt`, `core/sports_hook.py`, `sports_modes.json`이고, 커밋 메시지는 `sportspose: vendor sportslook and switch (all places off)`이다.

## S6. 한 자리 연결: P1 컷 프롬프트

C1 자리에 붙인다. 아래는 **하는 일**과 **틀**이다. 실제 변수 이름은 그 함수의 코드를 읽고 맞춘다.

`sports_pack()`이 돌려주는 것(act일 때만, 스포츠 동작이 없는 컷이면 `None`):

| 키 | 내용 |
|---|---|
| `code` | 자산 코드 (예: `TAEKWONDO_ROUNDHOUSE_KICK`) |
| `guide` | 프롬프트 에이전트에게 줄 영어 지시문과 자산 프롬프트 틀. 몸 동작 문장은 고치지 말고 `{SUBJECT}`, `{PARTNER_B}`, `{SETTING}`만 채우라는 지시가 들어 있다 |
| `prompt` | 틀을 채운 프롬프트. `subject=`, `setting=`, `partners=`를 주면 채워진다 |
| `unfilled` | 아직 안 채워진 자리 목록 |
| `negative` | negative 프롬프트 (SDXL 계열만) |
| `camera`, `size`, `openpose_png` | 컷 설명에 맞는 카메라, 그림 크기, OpenPose 그림 경로 |

### (A) LLM이 컷 프롬프트를 쓰는 경우

LLM 요청을 보내기 직전에 붙인다.

```python
from core.sports_hook import sports_pack
...
pack = sports_pack(<컷 설명 텍스트>, panel=<컷 번호 문자열>)
if pack:
    <LLM 요청의 지시문(시스템 메시지나 사용자 메시지)> += "\n\n" + pack["guide"]
```

- LLM이 인물 외모와 장소를 이미 알고 있으면(C2), 틀의 자리를 스스로 채운다.
- 한 컷에 인물이 두 명이면 첫 인물이 `{SUBJECT}`, 둘째 인물이 `{PARTNER_B}`이다. 지시문에 그렇게 적혀 있다.

### (B) 코드가 틀로 조립하는 경우

```python
from core.sports_hook import sports_pack
...
pack = sports_pack(<컷 설명 텍스트>, panel=<컷 번호 문자열>,
                   subject=<그 컷 첫 인물의 외모 문장>, setting=<장소·빛 문장>,
                   partners={"B": <둘째 인물의 외모 문장 또는 "another athlete">})
if pack and not pack["unfilled"]:
    <프롬프트의 동작 부분> = pack["prompt"]
```

### 두 경우 공통

- **컷 기록:** C5 자리에서 컷 항목에 `"sports_pose": {"code": pack["code"], "camera": pack["camera"], "control": pack["openpose_png"]}`를 더한다. 다음 단계(ControlNet)와 board-check가 이 기록을 쓴다. `pack`이 없으면 아무것도 더하지 않는다.
- **negative:** 워크플로가 negative를 쓰는 경우(C3)에만 `pack["negative"]`를 원래 negative 뒤에 붙인다. Flux 계열이면 붙이지 않는다.
- **글자 수:** `guide`는 영어 2천~3천 자다. LLM 컨텍스트가 짧아서 잘리면 보고서에 적는다(분석 담당이 짧은 판을 만든다).

`py_compile`을 통과한 뒤 커밋한다: `sportspose: P1 panel prompt uses the sports asset`. C5가 다른 파일이면 커밋을 하나 더 만든다: `sportspose: record the sports asset on the panel`.

## S7. 확인

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
$Py = 'python'   # C7 에서 확인한 파이썬
Push-Location $P
& $Py -m py_compile core\sportslook.py core\sports_hook.py <C1 파일> <C5 파일>
"py_compile exit: $LASTEXITCODE"
Get-Content "$P\sports_modes.json"
git -C $P log --oneline -4
git -C $P status --short -- core/sportslook.py core/sports_hook.py sports_modes.json
Pop-Location
```

- 프로젝트에 테스트가 있으면(C7) S4 전에 한 번, 여기서 한 번 돌려 결과를 비교한다.

확인 기준:
- `py_compile exit: 0`
- `sports_modes.json`이 `{"default": "off"}`
- 커밋이 2개(C5가 다른 파일이면 3개)

## S8. 사용자에게 알릴 것 (그대로 전달)

1. 새 코드는 **앱을 다시 켜야** 적용된다. 켜기 전까지는 아무것도 바뀌지 않는다.
2. 다시 켠 뒤 `film_assistant\sports_modes.json`을 `{"default": "observe"}`로 바꾼다.
   - 파일은 부를 때마다 다시 읽으므로 앱을 끄지 않아도 바로 적용된다.
   - 스포츠 컷(예: 태권도 돌려차기, 수영 자유형, 유도 업어치기)과 일반 컷이 섞인 콘티를 하나 만든다.
   - 동작은 그대로이고, 어느 컷에 어떤 자산이 불렸는지만 기록된다.
3. 기록을 보고 괜찮으면 `{"default": "off", "prompt": "act"}`로 바꿔 같은 콘티를 다시 만든다. 스포츠 컷의 몸 동작이 자산을 따르는지 전후 그림을 비교한다.
4. 끝나면 실행 담당에게 요약을 부탁한다.

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
$S = "$P\javisfilm\sports-pose"
New-Item -ItemType Directory -Force "$S\reports" | Out-Null
& "$S\.venv\Scripts\python.exe" "$S\sportslook.py" report "$P\data\sports_logs\hooks.jsonl" | Set-Content -Encoding utf8 "$S\reports\OBSERVE_1.md"
```

요약에는 자리별 호출 수, 자산이 불린 수, 오류 수, 걸린 시간, 자산 코드별 횟수만 들어 있다. 컷 설명과 인물은 들어 있지 않다.

## S9. 보고

`$S\reports\SPORTS_REPORT.md`에 아래를 적는다.

- **S0~S2 출력 원문.** 콘티 폴더 이름은 번호로 바꾼다.
- **S2b 판정 표:** board 번호 / 컷 번호 / 자산 코드 / 점수 / 판정(맞음·틀림·애매). 그리고 스포츠 동작이 있는데 불리지 않은 컷의 개수와 동작 이름.
- **S3 연결 지도 표.**
- **S5~S7 (진행했다면):** 파일:줄, 붙인 함수 이름, 바꾼 줄 수, 커밋 해시, (A)/(B) 중 어느 경우였는지, 건너뛴 것과 이유.
- **분석 담당에게 묻고 싶은 것:** 3개 이내.

사용자에게 보여 주고, 허락하면 `sports-pose/reports`만 add해서 **javisfilm 저장소의 현재 브랜치**에 커밋하고 push한다.

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
git -C $R add sports-pose/reports
git -C $R commit -m "sports-pose: connection survey and report"
git -C $R push
```

push가 실패하면 `SPORTS_REPORT.md` 전문을 화면에 출력한다.

## S10. 복사본 다시 맞추기 (분석 담당이 sportslook.py나 자산을 고쳤을 때만)

- **자산만 바뀐 경우:** 프로젝트는 `javisfilm\sports-pose\library`를 바로 읽으므로, 병합만 하고 앱을 다시 켜면 된다.
- **`sportslook.py`가 바뀐 경우:** 복사본도 같게 맞춘다. 스위치 설정(`sports_modes.json`)과 연결 코드는 건드리지 않는다.

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$P = 'C:\Users\Administrator\Desktop\film_assistant'
$Py = 'python'   # C7 에서 확인한 프로젝트 파이썬
git -C $R fetch origin claude/intelligent-lamport-p19iv3
git -C $R merge --no-edit origin/claude/intelligent-lamport-p19iv3
$h = git -C $R rev-parse --short HEAD
Copy-Item "$R\sports-pose\sportslook.py" "$P\core\sportslook.py" -Force
"vendored from javisfilm sports-pose/sportslook.py at $h" | Set-Content -Encoding utf8 "$P\core\sportslook_VENDORED_FROM.txt"
Push-Location $P
& $Py -c "from core.sports_hook import HOOK; print('mode', HOOK.mode('prompt'), 'assets', len(HOOK.library().rows))"
git -C $P add core/sportslook.py core/sportslook_VENDORED_FROM.txt
git -C $P commit -m "sportspose: resync vendored sportslook ($h)"
Pop-Location
```

확인 기준: `assets` 수가 나오고, 커밋이 하나 생긴다. `mode`는 그대로다.
