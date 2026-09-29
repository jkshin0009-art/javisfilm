# 작업 지시서: 강좌 영상의 예시 장면으로 역프롬프트 검증 (실행 담당용)

## 목표

사용자가 준 강좌 영상 https://www.youtube.com/watch?v=dcN5Gwbz0xM 의 가운데(8:51 부근)에 예시 결과 영상들이 나온다. 이 장면들로 다음을 한다.
1. 장면을 샷으로 자른다.
2. **프로젝트에 이미 있는 역프롬프트 로직**으로 샷마다 프롬프트를 만든다.
3. 그 프롬프트가 화면과 맞는지 `reverse-check`로 점수를 매긴다. 실제로 쓴 프롬프트를 알 수 있으면 그것과도 비교한다.

분석은 분석 담당이 한다. 이 문서는 **실행하고 기록**하는 것까지다.

- **저장소:** `C:\Users\Administrator\Desktop\film_assistant\javisfilm` (아래 `$R`)
- **도구:** `$R\reverse-check` (아래 `$V`)
- **작업 폴더:** `$V\work\dcN5Gwbz0xM` (아래 `$W`)
- **파이썬:** chat-upgrade 때 만든 `$R\chat-upgrade\.venv`를 같이 쓴다(아래 `$Py`)

## 반드시 지킬 규칙

1. **프로젝트를 고치지 말 것:** film_assistant의 코드, 설정, 데이터를 고치지 않는다. 역프롬프트 로직은 **불러서 쓰기만** 한다. 부르는 데 필요한 작은 스크립트는 `$V\local\`에 만든다(`.gitignore`로 올라가지 않음).
2. **영상은 올리지 말 것:** 받은 영상, 프레임, 클립은 남의 저작물이다. `$W` 밖으로 복사하지 않고 git에 올리지 않는다. 올리는 것은 `$V\reports\`의 점수 보고서뿐이다.
3. **새 프로그램 설치는 물어볼 것:** `pip install`은 `$Py` 가상환경 안에서만 한다. 그 밖의 설치(예: Deno, ffmpeg)는 사용자에게 먼저 묻는다.
4. **LLM이 바쁘면 물어볼 것:** classify, prompt, score는 5678 비전 모델을 많이 부른다(샷 하나에 요청 수십 건). 영화 작업이 LLM을 쓰는 중이면 먼저 묻는다.
5. 확인 기준을 못 넘으면 멈추고 그때까지를 보고한다. 출력은 원문 그대로 붙인다. 셸은 PowerShell 기준이다.

## V0. 갱신과 테스트

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$V = "$R\reverse-check"
$Py = "$R\chat-upgrade\.venv\Scripts\python.exe"
git -C $R pull --rebase
git -C $R log --oneline -3
Get-Command ffmpeg -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
Push-Location $V
& $Py -m pytest -q tests
Pop-Location
```

- ffmpeg가 PATH에 없으면 프로젝트가 쓰는 ffmpeg.exe를 찾는다. 찾으면 `$env:FFMPEG = '<경로>'`로 지정하고 다시 실행한다.
- 확인 기준: `4 passed`이다. ffmpeg를 못 찾으면 테스트 2개가 skip된다. 그 상태로는 V3 이후를 할 수 없으니 멈추고 묻는다.

## V1. 영상 정보

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$V = "$R\reverse-check"; $W = "$V\work\dcN5Gwbz0xM"
$Py = "$R\chat-upgrade\.venv\Scripts\python.exe"
New-Item -ItemType Directory -Force $W | Out-Null
& $Py -m pip install -q -U yt-dlp
& $Py -m yt_dlp --version
& $Py -m yt_dlp --skip-download --dump-json 'https://www.youtube.com/watch?v=dcN5Gwbz0xM' | Set-Content -Encoding utf8 "$W\meta.json"
$m = Get-Content "$W\meta.json" -Raw -Encoding utf8 | ConvertFrom-Json
"title: $($m.title)"; "channel: $($m.channel)"; "duration: $($m.duration) s"
$m.chapters | ForEach-Object { "{0,7:N1} - {1,7:N1}  {2}" -f $_.start_time, $_.end_time, $_.title }
"--- description ---"; $m.description
```

- yt-dlp가 JavaScript 런타임(Deno 등)이 필요하다는 오류를 내면, 설치하지 말고 사용자에게 묻는다(규칙 3). 대안은 사용자가 영상을 직접 받아 `$W\src.mp4`로 넣어 주는 것이다.
- 확인 기준: 제목과 길이가 나온다.
- 설명(description)이나 챕터에 **실제로 쓴 프롬프트**가 있으면 V7에서 쓰니 기록해 둔다.

## V2. 구간 받기

8:51이 들어 있는 챕터가 있으면 그 챕터 시작 30초 전부터 끝 30초 뒤까지 받는다. 챕터가 없으면 7:30~16:00을 받는다. 정한 시작 시각을 `$Start`에 둔다(보고서의 시각 보정에 쓴다).

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$V = "$R\reverse-check"; $W = "$V\work\dcN5Gwbz0xM"
$Py = "$R\chat-upgrade\.venv\Scripts\python.exe"
$Start = '7:30'; $End = '16:00'
& $Py -m yt_dlp -f 'bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]' --download-sections "*$Start-$End" `
  --force-keyframes-at-cuts --merge-output-format mp4 -o "$W\src.%(ext)s" 'https://www.youtube.com/watch?v=dcN5Gwbz0xM'
Get-Item "$W\src.mp4" | Select-Object Name, Length
"$Start" | Set-Content -Encoding ascii "$W\offset.txt"
```

확인 기준: `$W\src.mp4`가 있다.

## V3. 샷 자르기

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$V = "$R\reverse-check"; $W = "$V\work\dcN5Gwbz0xM"
$Py = "$R\chat-upgrade\.venv\Scripts\python.exe"
Push-Location $V
& $Py revcheck.py shots "$W\src.mp4" --work $W
Pop-Location
```

- 확인 기준: `N shots` 줄이 나오고 `$W\index.html`이 생겼다.
- 예시 영상이 강좌 화면의 **일부 창 안에서만** 재생되면, index.html의 프레임을 보고 그 창의 위치를 `w:h:x:y`로 재서 `--crop`을 붙여 다시 실행한다. 확신이 없으면 사용자에게 index.html을 보여 주고 묻는다.
- 샷이 80개를 넘거나 5개보다 적으면 `--threshold`를 0.4 또는 0.2로 바꿔 본다.

## V4. 장면 분류

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$V = "$R\reverse-check"; $W = "$V\work\dcN5Gwbz0xM"
$Py = "$R\chat-upgrade\.venv\Scripts\python.exe"
Push-Location $V
& $Py revcheck.py classify --work $W --url http://127.0.0.1:5678
Pop-Location
```

- 확인 기준: `RESULT kinds:` 줄이 나오고 `showcase`가 1개 이상이다.
- 사용자에게 `$W\index.html`을 열어 보라고 알린다. 분류가 틀린 샷이 있으면 사용자가 말해 준 대로 `shots.json`의 `kind`를 고친다. 이 파일은 우리 작업 파일이라 고쳐도 된다.

## V5. 프로젝트의 역프롬프트 로직 찾기 (읽기만)

film_assistant에서 "영상이나 이미지를 보고 프롬프트를 만드는" 코드를 찾는다.

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
Get-ChildItem $P -Recurse -Include *.py -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|__pycache__|\.venv|venv|javisfilm|_trash|_checkpoint)' } |
  Select-String -Pattern '역프롬|reverse.?prompt|img2prompt|interrogat|image_to_prompt|video_to_prompt|caption|describe_(image|video|frame)' |
  Group-Object Path | ForEach-Object { "{0}  ({1} hits)" -f $_.Name.Substring($P.Length), $_.Count }
```

찾은 것마다 다음을 적는다.
- 파일:함수
- 입력: 이미지 한 장 / 여러 장 / 영상 파일 / 영상 URL
- 출력 형식: 자유 문장 / H3 여섯 구간 / krea2 이미지 프롬프트 / JSON 등
- 부르는 모델과 주소
- 부르는 방법: 함수, CLI, 웹 경로

그다음 `$V\local\project_rp.py`를 만든다. 샷 하나의 입력을 받아 그 로직을 부르고, **프롬프트만 표준 출력으로** 내는 작은 스크립트다. 프로젝트 파일은 import하거나 HTTP로 부르기만 하고 고치지 않는다.
- 입력이 이미지면 `{frames}` 또는 `{frame}`을, 영상이면 `{clip}`을 받게 만든다.
- 로직이 여러 개(예: 이미지용, 영상용)면 각각 스크립트를 만들고 V6에서 `--name`을 다르게 준다.
- 샷 하나로 먼저 돌려 본다.

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$V = "$R\reverse-check"; $W = "$V\work\dcN5Gwbz0xM"
$Py = "$R\chat-upgrade\.venv\Scripts\python.exe"   # 프로젝트 로직이 다른 파이썬을 써야 하면 --cmd 안의 python 경로를 그것으로 바꾼다
Push-Location $V
& $Py revcheck.py prompt --work $W --ids s001 --name project --cmd "`"$Py`" local\project_rp.py {frames}"
Get-Content "$W\prompts\project\s001.txt" -Encoding utf8
Pop-Location
```

확인 기준: 프롬프트 한 편이 나온다. 로직을 못 찾았으면 V6에서 `--vlm` 기준선만 돌리고, 못 찾았다고 보고한다.

## V6. 프롬프트 만들기 (예시 영상 샷 전부)

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$V = "$R\reverse-check"; $W = "$V\work\dcN5Gwbz0xM"
$Py = "$R\chat-upgrade\.venv\Scripts\python.exe"
Push-Location $V
& $Py revcheck.py prompt --work $W --only showcase --name project --cmd "`"$Py`" local\project_rp.py {frames}"
& $Py revcheck.py prompt --work $W --only showcase --vlm --url http://127.0.0.1:5678
Pop-Location
```

확인 기준: `RESULT prompts[project]`와 `RESULT prompts[vlm]` 줄이 나온다.

## V7. 실제 프롬프트 (있을 때만)

V1의 설명이나 챕터, 또는 강좌 화면(분류가 `ui`인 샷의 프레임)에 예시 영상을 만들 때 쓴 프롬프트가 보이면 옮겨 적는다.
- 어느 샷의 프롬프트인지 확실할 때만 `$W\truth.csv`에 적는다. 형식은 UTF-8, 머리줄 `shot,prompt`이다.
- 확실하지 않으면 적지 않고, 사용자에게 알려 달라고 한다.
- 없으면 이 단계는 건너뛴다.

## V8. 점수와 보고서

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$V = "$R\reverse-check"; $W = "$V\work\dcN5Gwbz0xM"
$Py = "$R\chat-upgrade\.venv\Scripts\python.exe"
$Start = (Get-Content "$W\offset.txt").Trim()
Push-Location $V
& $Py revcheck.py score --work $W --only showcase --url http://127.0.0.1:5678
& $Py revcheck.py report --work $W --only showcase --offset $Start --with-prompts --out "$V\reports\REVCHECK_dcN5Gwbz0xM.md"
Pop-Location
```

확인 기준: `RESULT scores saved`가 나오고 보고서 파일이 생겼다.

## V9. 보고

1. `$V\reports\REVCHECK_dcN5Gwbz0xM.md` 끝에 아래를 덧붙인다.
   - V5에서 찾은 역프롬프트 로직의 목록(파일:함수, 입력, 출력 형식, 모델)
   - `local\project_rp.py`가 그 로직을 어떻게 부르는지 두세 줄
   - V1의 제목, 채널, 챕터
   - V7을 했는지와 truth가 몇 건인지
2. 사용자에게 보여 주고, 허락하면 `reverse-check/reports`만 add해서 커밋·push한다. push가 실패하면 보고서 전문을 화면에 출력한다.
