# 작업 지시서: 말풍선(ComfyUI-BubbleText) 진단과 수정 (실행 담당용)

목표는 영화 프로젝트에서 Qwen Image 2.1 이미지에 쓰는 말풍선 노드의 문제(한글 깨짐, 검은 덩어리, 문장 쪼개짐, 크기 불균형, 검은 결과 이미지)를 실제 이미지로 확인하고, 사용자가 확인한 뒤 고치는 것이다.
분석은 다른 담당이 하므로, 이 문서는 **실행하고 결과를 그대로 기록**하는 것까지만 한다.

- **저장소:** `C:\Users\Administrator\Desktop\film_assistant\javisfilm` (아래 `$R`)
- **도구 폴더:** `$R\bubble-doctor` (아래 `$B`)

## 반드시 지킬 규칙

1. **원본 워크플로는 수정하지 말 것:** 고친 설정은 `fix-workflow`로 **사본**을 만든다.
2. **노드 코드는 사용자가 확인한 뒤에만 고칠 것:** `patch_bubbletext.py`를 쓰고, 백업이 자동으로 생긴다. 다른 방법으로 노드 파일을 고치지 않는다.
3. **ComfyUI를 직접 재시작하지 말 것:** 재시작이 필요하면 사용자에게 요청한다. 다른 프로세스도 건드리지 않는다.
4. **이미지와 영상은 git에 올리지 말 것:** `bubble-doctor\work\`는 git에 올라가지 않는다. 올리는 것은 `reports\` 안의 텍스트뿐이고, 이 저장소는 공개 저장소다.
5. **확인 기준을 못 넘으면 멈출 것:** 그때까지의 결과를 보고서에 적고 끝낸다.
6. **출력을 요약하지 말 것:** 명령 출력은 보고서에 원문 그대로 붙인다. 추측으로 채우지 않는다.
7. **셸:** 명령은 PowerShell 기준이다. bash에서 실행 중이면 `.ps1`로 저장해 `powershell -NoProfile -ExecutionPolicy Bypass -File`로 실행한다.

## 1. 저장소 갱신

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
if (Test-Path "$R\.git") { git -C $R pull } else { git clone -b claude/affectionate-brahmagupta-24a19d https://github.com/jkshin0009-art/javisfilm $R }
git -C $R log --oneline -3
Test-Path "$R\bubble-doctor\bubble_doctor.py"
```

확인 기준: 마지막 줄이 `True`다.

## 2. ComfyUI와 BubbleText 노드 찾기

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'main\.py' } | Select-Object ProcessId, CommandLine | Format-List
```

- CommandLine에서 ComfyUI 폴더(`main.py`가 있는 곳)를 찾는다. ComfyUI가 꺼져 있으면 사용자에게 위치를 묻는다.
- 그 경로를 아래 첫 줄의 `$C`에 넣고 실행한다.
- 이 블록은 이후 단계가 쓸 값을 `work\env.ps1`에 저장한다. 이후 블록은 모두 이 파일을 불러와서 시작하므로, 단계마다 PowerShell을 새로 띄워도 된다.

```powershell
$C = 'ComfyUI 폴더 경로로 바꿀 것'
$B = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\bubble-doctor'
$N = "$C\custom_nodes\ComfyUI-BubbleText"
New-Item -ItemType Directory -Force "$B\work" | Out-Null
@"
`$B = '$B'
`$C = '$C'
`$N = '$N'
`$PY = '$B\.venv\Scripts\python.exe'
"@ | Set-Content -Encoding utf8 "$B\work\env.ps1"
Test-Path "$N\bubble_text.py"
git -C $N log --oneline -1
git -C $N status --short
Get-ChildItem "$N\fonts"
```

확인 기준: `Test-Path`가 `True`다. `git status --short`에 `bubble_text.py`가 보이면 누군가 이미 노드를 고친 것이니 보고서에 적는다.

## 3. 도구 설치와 자체 테스트

```powershell
. 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\bubble-doctor\work\env.ps1'
py -3 -m venv "$B\.venv"
& "$B\.venv\Scripts\pip" install -r "$B\requirements.txt"
$env:BUBBLETEXT_DIR = $N
$env:KOREAN_FONT = 'C:\Windows\Fonts\malgunbd.ttf'
Set-Location $B
& $PY -m pytest tests -q -p no:cacheprovider
```

- 파이썬은 3.10 이상이어야 한다.

확인 기준: `10 passed`이다.

## 4. 사용 중인 워크플로 조사

```powershell
. 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\bubble-doctor\work\env.ps1'
$P = 'C:\Users\Administrator\Desktop\film_assistant'
$files = @(Get-ChildItem $P -Recurse -Filter *.json -ErrorAction SilentlyContinue) + @(Get-ChildItem "$C\user" -Recurse -Filter *.json -ErrorAction SilentlyContinue)
$hits = @($files | Where-Object { $_.FullName -notmatch '_bubblefix\.json$' -and (Select-String -Path $_.FullName -Pattern 'SpeechBubble' -Quiet) })
$hits.FullName | Set-Content -Encoding utf8 "$B\work\workflows.txt"
$hits.FullName
if ($hits.Count) { & $PY "$B\bubble_doctor.py" workflow --node-dir $N @($hits.FullName) }
```

확인 기준: BubbleText 노드가 하나 이상 나온다. 하나도 없으면 사용자에게 말풍선 워크플로 파일 위치를 묻는다.

출력에서 값을 골라 아래 블록을 바꾸고 실행한다.
- 대사는 워크플로의 `text` 값을 `@'` 다음 줄부터 `'@` 앞 줄까지 그대로 붙인다. 여러 줄(빈 줄로 말풍선 구분)이어도, 따옴표가 있어도 그대로 둔다.
- 대사는 `work\text.txt`에, 나머지 값은 `env.ps1`에 저장된다. 대사는 파일로 넘겨야 Windows PowerShell 5.1에서 따옴표가 깨지지 않는다.

```powershell
$B = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\bubble-doctor'
@'
여기에 text 값을 붙여 넣는다
'@ | Set-Content -Encoding utf8 "$B\work\text.txt"
@'
$TEXTFILE = "$B\work\text.txt"
$CUR_FONT = 'comicbd.ttf'
$CUR_MAX = 64
$CUR_MARGIN = 0.08
$THR = 195
'@ | Add-Content -Encoding utf8 "$B\work\env.ps1"
. "$B\work\env.ps1"
Get-Content -Encoding utf8 $TEXTFILE
"font: $CUR_FONT  max: $CUR_MAX  margin: $CUR_MARGIN  threshold: $THR"
```

## 5. 글꼴 확인과 한글 글꼴 설치

```powershell
. 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\bubble-doctor\work\env.ps1'
& $PY "$B\bubble_doctor.py" fonts --node-dir $N --text-file $TEXTFILE
[Net.ServicePointManager]::SecurityProtocol = 'Tls12'
Invoke-WebRequest 'https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Bold.ttf' -OutFile "$N\fonts\NanumGothic-Bold.ttf" -UseBasicParsing
& $PY "$B\bubble_doctor.py" fonts --node-dir $N --text-file $TEXTFILE
```

- 나눔고딕 Bold는 무료 OFL 글꼴이다.
- 노드 `fonts` 폴더에 글꼴 파일을 하나 추가할 뿐이라 노드 코드는 바뀌지 않는다.

확인 기준: 두 번째 출력에 `NanumGothic-Bold.ttf ... OK for the text`가 있다.

## 6. 시험 이미지 모으기

- 말풍선이 들어간 Qwen Image 2.1 결과 이미지 3~10장을 `work\in\`에 **복사**한다(원본은 그대로 둔다).
- 어디 있는지 모르면 `$C\output`의 최근 이미지를 보여주고 사용자에게 고르게 한다.
- 말풍선이 제대로 안 나온 이미지(검은 덩어리, 깨진 한글)가 섞여 있으면 좋다.

```powershell
. 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\bubble-doctor\work\env.ps1'
New-Item -ItemType Directory -Force "$B\work\in" | Out-Null
Get-ChildItem "$C\output" -File -Include *.png,*.jpg,*.webp -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName, LastWriteTime
```

사용자가 고른 파일을 `Copy-Item <파일> "$B\work\in\"`로 복사한 뒤 확인한다.

```powershell
. 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\bubble-doctor\work\env.ps1'
Get-ChildItem "$B\work\in" | Select-Object Name, Length
```

확인 기준: 이미지가 3장 이상이다.

## 7. 말풍선 인식 확인

```powershell
. 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\bubble-doctor\work\env.ps1'
& $PY "$B\bubble_doctor.py" scan --node-dir $N --in "$B\work\in" --out "$B\work\scan" --text-file $TEXTFILE --threshold $THR
```

확인 기준: 이미지마다 한 줄씩 결과가 나온다. `!` 경고가 있어도 계속한다(경고를 찾는 단계다).

## 8. 지금 설정과 고친 설정 비교

```powershell
. 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\bubble-doctor\work\env.ps1'
& $PY "$B\bubble_doctor.py" render --node-dir $N --in "$B\work\in" --out "$B\work\render" --text-file $TEXTFILE --font NanumGothic-Bold.ttf --current-font $CUR_FONT --current-max-size $CUR_MAX --current-margin $CUR_MARGIN --threshold $THR
```

그다음 사용자에게 `work\render\*__compare.png`를 열어 보라고 한다. 각 이미지는 왼쪽부터 원본 | 지금 설정 | 고친 설정이다. 그리고 두 가지를 묻는다.
- 고친 설정이 나은가?
- 글자 크기가 적당한가? 바꾸고 싶으면 위 명령 끝에 `--max-size 90`처럼 크기나 `--margin 0.15`를 붙여 다시 렌더한다.

확인 기준: 사용자가 "적용해도 된다"고 답한다. 아니라고 하면 이유를 보고서에 적고 10단계로 간다.

## 9. 적용 (사용자 동의 후)

아래 블록의 `$SIZE`를 사용자가 고른 최대 크기로 바꾼다. 기본값은 8단계 출력의 `fixed (max 숫자` 값이다.
- 첫 부분: 노드의 검은 말풍선 오인 수정(백업 자동)
- 뒷부분: 워크플로마다 설정을 바꾼 **사본**(`_bubblefix.json`) 만들기. 원본은 그대로 둔다.

```powershell
. 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\bubble-doctor\work\env.ps1'
$SIZE = 111
& $PY "$B\patch_bubbletext.py" status --node-dir $N
& $PY "$B\patch_bubbletext.py" apply --node-dir $N
& $PY "$B\patch_bubbletext.py" status --node-dir $N
foreach ($f in (Get-Content -Encoding utf8 "$B\work\workflows.txt")) {
  $dst = [IO.Path]::Combine([IO.Path]::GetDirectoryName($f), [IO.Path]::GetFileNameWithoutExtension($f) + '_bubblefix.json')
  & $PY "$B\bubble_doctor.py" fix-workflow $f $dst --font NanumGothic-Bold.ttf --max-size $SIZE --margin 0.12 --no-uppercase
}
```

그리고 사용자에게 두 가지를 요청한다.
1. ComfyUI를 재시작해 달라고 한다. 노드 수정과 새 글꼴은 재시작해야 반영된다.
2. `_bubblefix.json` 워크플로를 열어 한 장 생성해 보라고 한다. 4단계에서 "bubble mask is shown/saved as an image" 경고가 나왔다면, 그 미리보기·저장 노드의 선을 노드의 첫 번째 출력 `IMAGE`로 옮기라고 안내한다. 연결은 도구로 바꾸지 않는다.

확인 기준: 마지막 `status`가 `patched`다.

- **되돌리기:** `& $PY "$B\patch_bubbletext.py" revert --node-dir $N` 실행 후 ComfyUI 재시작.
- **노드 업데이트 전:** 반드시 `revert`하고, 업데이트한 뒤 다시 `apply`한다.

## 10. 보고서와 올리기

`$B\reports\BUBBLE_REPORT.md`를 만든다. 각 항목에 해당 출력을 원문 그대로 붙인다.
1. 1단계 `git log`, 2단계 노드 커밋·`git status`·fonts 목록
2. 3단계 pytest 마지막 줄
3. 4단계 workflow 출력 전체. 대사 내용이 공개되면 안 된다고 사용자가 말하면 대사만 `***`로 가린다.
4. 5단계 fonts 출력 두 번
5. 7단계 scan 출력 전체
6. 8단계 render 출력 전체와 사용자의 답
7. 9단계 patch status 출력과 fix-workflow 출력
8. 사용자가 새 워크플로로 생성해 본 소감(있으면)
9. 멈춘 단계가 있으면 그 단계와 이유

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
git -C $R pull
git -C $R add bubble-doctor/reports
git -C $R status --short
git -C $R commit -m "Add bubble-doctor report"
git -C $R push
```

- `git status --short`에 `bubble-doctor/reports/` 밖의 파일이나 이미지가 보이면 commit하지 말고 멈춘다.
- push가 실패하면 `BUBBLE_REPORT.md` 전체를 화면에 출력한다. 사용자가 복사해 분석 담당에게 전달한다.
- 성공하면 커밋 해시를 출력한다.
