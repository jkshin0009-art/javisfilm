# 작업 지시서: H3 6인 참조 시험 (실행 담당용)

목표는 실제 영화 인물 6명(A~F)으로 MiniMax H3 + Extender가 다인원 장면에서 얼굴을 얼마나 유지하는지 재고, 참조를 넣는 세 방식(X3a/X3b/X3c) 중 무엇이 나은지 숫자로 비교하는 것이다.
분석은 다른 담당이 하므로, 이 문서는 **실행하고 결과를 그대로 기록**하는 것까지만 한다.

진행은 세 단계다.
- **A단계 (실행 담당):** 준비와 조사
- **B단계 (사용자):** ComfyUI에서 클립 8개 렌더
- **C단계 (실행 담당):** 얼굴 검사, 보고서 작성, push

작업 폴더는 프로젝트 폴더 `C:\Users\Administrator\Desktop\film_assistant` 안의 git 저장소 `C:\Users\Administrator\Desktop\film_assistant\javisfilm`의 `h3-multicast`이다(아래 `$H`).

## 반드시 지킬 규칙

1. **건드리지 말 것:** ComfyUI(GPU1, 포트 8189)를 재시작하거나 설정·노드를 바꾸지 않는다. llama-server나 다른 프로세스도 건드리지 않는다.
2. **올리지 말 것:** 인물 이미지, 영상, 음성, `experiment\` 폴더(인물 설명이 든 cast.yaml 포함), 표시된 프레임은 git에 올리지 않는다. 올리는 것은 `reports\` 안의 텍스트뿐이다. 이 저장소는 공개 저장소다.
3. **확인 기준을 못 넘으면 멈출 것:** 각 단계의 확인 기준을 통과하지 못하면 다음 단계로 가지 않고, 그때까지의 결과를 보고서에 적고 끝낸다.
4. **출력을 요약하지 말 것:** 명령 출력은 보고서에 원문 그대로 붙인다. 추측으로 채우지 않는다.
5. **셸:** 명령은 PowerShell 기준이다. bash에서 실행 중이면 `.ps1`로 저장해 `powershell -NoProfile -ExecutionPolicy Bypass -File`로 실행한다.

---

## A단계: 준비와 조사

### A1. 저장소 갱신

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
if (Test-Path "$R\.git") { git -C $R pull } else { git clone -b claude/affectionate-brahmagupta-24a19d https://github.com/jkshin0009-art/javisfilm $R }
$H = "$R\h3-multicast"
git -C $R log --oneline -3
```

확인 기준: `$H\h3_scene.py`, `$H\face_check.py`가 있다.

### A2. 파이썬 환경

```powershell
$H = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\h3-multicast'
py -0p
py -3 -c "import sys; print(sys.version)"
py -3 -m venv "$H\.venv"
& "$H\.venv\Scripts\python" -m pip install --upgrade pip
& "$H\.venv\Scripts\pip" install -r "$H\requirements.txt"
& "$H\.venv\Scripts\python" -c "from insightface.app import FaceAnalysis; FaceAnalysis(name='buffalo_l', allowed_modules=['detection','recognition'])"
```

- 파이썬 3.10 이상이어야 한다. `py -3`이 3.10 미만이면 `py -0p` 목록에서 3.10 이상 버전을 골라 `py -3.12`처럼 지정한다.
- 마지막 줄이 얼굴 인식 모델(약 280MB)을 받는다.

확인 기준: 설치와 모델 다운로드가 에러 없이 끝난다.

### A3. 자체 테스트

```powershell
$H = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\h3-multicast'
Set-Location $H
& "$H\.venv\Scripts\python" -m pytest tests -q -p no:cacheprovider
```

확인 기준: failed가 0이다. `43 passed, 1 skipped`가 정상이다. 건너뛴 1개는 Extender 호환 검사이고, A4에서 따로 돌린다.

### A4. ComfyUI와 Extender 조사

```powershell
$H = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\h3-multicast'
New-Item -ItemType Directory -Force "$H\reports" | Out-Null
Invoke-RestMethod http://127.0.0.1:8189/system_stats | ConvertTo-Json -Depth 6
$o = Invoke-RestMethod http://127.0.0.1:8189/object_info
$h3 = [ordered]@{}
foreach ($p in $o.PSObject.Properties) { if ($p.Name -match 'MiniMax|H3') { $h3[$p.Name] = $p.Value } }
$h3 | ConvertTo-Json -Depth 30 | Set-Content -Encoding utf8 "$H\reports\comfy_h3_nodes.json"
"H3 nodes: " + ($h3.Keys -join ', ')
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'main\.py' -and $_.CommandLine -match '8189' } | Select-Object ProcessId, CommandLine | Format-List
```

마지막 명령의 CommandLine에서 ComfyUI 폴더(`main.py`가 있는 폴더)를 찾아 `$C`에 넣고 아래를 실행한다.

```powershell
$C = '<ComfyUI 폴더>'
$H = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\h3-multicast'
Get-Content "$C\custom_nodes\ComfyUI_MiniMax_H3_Extender\pyproject.toml" | Select-String '^version'
$env:EXTENDER_DIR = "$C\custom_nodes\ComfyUI_MiniMax_H3_Extender"
& "$H\.venv\Scripts\python" -m pytest "$H\tests\test_comfy_node.py" -q -p no:cacheprovider
git -C "$C\custom_nodes\ComfyUI_MiniMax_H3_Extender" log --oneline -1
Get-ChildItem "$C\models" -Recurse -File | Where-Object { $_.Name -match 'minimax|h3' } | Select-Object FullName, @{n='GB';e={[math]::Round($_.Length/1GB,2)}}
```

확인 기준: H3 노드 목록에 `MiniMaxH3Extender` 또는 이름에 `Extender`가 들어간 노드가 있다. ComfyUI가 8189에서 응답하지 않으면 그 사실을 적고 A5로 넘어간다.

### A5. 인물 자료 확인

사용자가 미리 넣어 두었어야 하는 파일은 다음과 같다(`$H\experiment\`는 git에 올라가지 않는다).

- `experiment\assets\A_face.png` ~ `F_face.png`: 필수. 얼굴이 크게 나온 이미지.
- `experiment\assets\A_sheet.png` ~ `F_sheet.png`: 선택. 캐릭터 시트.
- `experiment\assets\A_voice.wav`, `B_voice.wav`: 선택. 2~15초 음성.
- `experiment\looks.txt`: 필수. 한 줄에 한 명씩 `A: 이름 / 외모 설명`.

```powershell
$H = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\h3-multicast'
Get-ChildItem "$H\experiment\assets" | Select-Object Name, Length
Get-Content "$H\experiment\looks.txt" -Encoding utf8
```

확인 기준: A~F의 `_face` 이미지 6개와 `looks.txt`가 있다. 없으면 무엇이 빠졌는지 사용자에게 말하고 멈춘다.

### A6. 캐스트 파일 작성

`$H\examples\EXP_cast_template.yaml`을 `$H\experiment\cast.yaml`로 복사해 채운다.

- **`name`:** 영어 로마자로 쓴다(예: 민지 → Minji). 한글이 프롬프트에 들어가면 생성기가 오류를 낸다.
- **`look`:** `looks.txt` 설명을 영어 명사구로 옮긴다. "a woman in her late twenties with a short silver bob, a red wool coat and round gold glasses"처럼 머리, 옷 색, 소품이 들어가게 쓴다.
- **`short`:** "the woman in the red coat" 같은 짧은 영어 명사구다.
- **`sheet`, `voice`:** 파일이 실제로 있을 때만 적는다. 없는 파일은 줄을 지운다.
- **장소:** `studio` 줄은 그대로 둔다.

확인 기준: `experiment\cast.yaml`에 인물 6명이 있고 한글이 없다.

### A7. 인물 얼굴 구분도

```powershell
$H = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\h3-multicast'
Set-Location $H
& "$H\.venv\Scripts\python" face_check.py cast --cast experiment\cast.yaml
```

확인 기준: `reference faces: A=… F=…`가 모두 1 이상이다. 0인 인물이 있으면 그 이미지에서 얼굴이 안 잡힌 것이니 사용자에게 알리고 멈춘다.

### A8. 시험 프롬프트 생성

```powershell
$H = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\h3-multicast'
Set-Location $H
& "$H\.venv\Scripts\python" h3_scene.py build examples\EXP_multicast.yaml --cast experiment\cast.yaml --out experiment\out --check-files
"exit code: $LASTEXITCODE"
Get-ChildItem experiment\out\EXP | Select-Object Name
```

- `--llm`은 쓰지 않는다. X3a/X3b/X3c는 참조 방식만 달라야 하는데, LLM이 조건마다 묘사를 다르게 쓰면 비교가 흐려진다.
- X2의 경고("6 people … medium shot")는 일부러 넣은 조건이라 정상이다.

- X5b의 경고("master shot not rendered yet")도 정상이다. X1을 렌더한 뒤에 만드는 클립이다.

확인 기준: `exit code: 0`이고, 클립 8개의 `.prompt.txt`와 `.refs.txt`, 그리고 `order.json`이 있다.

### A8b. (선택) Prompt Pack 노드 설치

- 이 노드가 있으면 사용자가 프롬프트를 클립마다 붙여 넣지 않아도 된다. Extender의 `prompt_pack` 입력에 연결하면 클립 카드가 만들어지고 프롬프트가 채워진다.
- 사용자에게 설치 여부를 먼저 묻는다. 설치는 ComfyUI `custom_nodes`에 폴더 링크를 하나 만드는 것뿐이고, 저장소를 `git pull`하면 노드도 같이 갱신된다.

```powershell
$C = '<ComfyUI 폴더>'
$H = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\h3-multicast'
cmd /c mklink /J "$C\custom_nodes\javisfilm-h3-scene" "$H\comfyui_node"
Get-ChildItem "$C\custom_nodes\javisfilm-h3-scene"
```

- 설치했으면 사용자에게 ComfyUI 재시작을 요청한다.
- 재시작 후 노드 목록에 `H3 Scene Prompt Pack (javisfilm)`이 보이는지 확인한다(MiniMax H3 분류).
- 되돌리기: `cmd /c rmdir "$C\custom_nodes\javisfilm-h3-scene"`. 링크만 지우고 원본 폴더는 남는다.

### A9. 사용자에게 렌더 요청하고 멈추기

아래 B단계 체크리스트를 화면에 출력하고 멈춘다.
- 출력할 때 각 `experiment\out\EXP\<클립>.refs.txt`의 파일 경로, 길이, 시드를 채워서 보여준다.
- 사용자가 "렌더 끝났다"고 하면 C단계를 한다.

---

## B단계: 렌더 (사용자가 ComfyUI에서)

**모든 클립 공통**
- 해상도 1024×576
- `ref_image_size`: match
- Motion Context: OFF
- 모드: Ref2VA
- 시드는 `refs.txt`에 적힌 값으로 고정한다. X3a·X3b·X3c는 같은 시드여야 한다.

**프롬프트 넣는 법** (둘 중 하나)
- **노드 사용(A8b 설치 시):** `H3 Scene Prompt Pack` 노드를 추가하고 연결합니다.
  - `scene_folder`: `C:\Users\Administrator\Desktop\film_assistant\javisfilm\h3-multicast\experiment\out\EXP`
  - `clips`: 아래 프로젝트별 목록
  - 연결: `prompt_pack` 출력 → Extender `prompt_pack` 입력
  - 카드별 길이와 시드: `card_settings` 출력에 나오는 대로 맞춥니다.
- **직접 붙여넣기:** 각 클립 카드에 `experiment\out\EXP\<클립>.prompt.txt` 내용을 통째로 붙여 넣고, 길이와 시드를 맞춥니다.

**프로젝트 1** (Extender에서 New Project)
- 공통 참조: 슬롯 1~6에 A~F. `refs.txt`에 적힌 파일을 넣는다(시트가 있으면 시트).
- 클립 5개를 이 순서로 만든다(노드의 `clips`: `X1,X2,X3b,X3c,X4`).
- X4: A·B 음성 파일이 있으면 그 클립의 클립별 참조에 Audio 1 = A, Audio 2 = B로 넣는다.
- Final Decode에서 **Save Individual Clips**를 켜고 Full Batch를 실행한다.

**프로젝트 2** (New Project)
- 공통 참조: 슬롯 1 = A, 슬롯 2 = B만 넣는다. 나머지는 비워 둔다.
- 클립 1개: X3a (노드의 `clips`: `X3a`).

**프로젝트 3** (프로젝트 1의 X1을 저장한 뒤, New Project)
- 공통 참조는 프로젝트 1과 같다(슬롯 1~6에 A~F).
- 클립 2개: X5a, X5b (노드의 `clips`: `X5a,X5b`).
- X5b 카드의 클립별 참조(Refs)에 **Video 1** = `experiment\renders\EXP_X1.mp4`를 넣는다(fps 24). X5a에는 넣지 않는다.
- 두 클립은 시드가 같고, 차이는 마스터 샷 영상 참조뿐이다.

**결과 저장**
- 클립 영상 8개를 `experiment\renders\`에 `EXP_X1.mp4`, `EXP_X2.mp4`, `EXP_X3a.mp4`, `EXP_X3b.mp4`, `EXP_X3c.mp4`, `EXP_X4.mp4`, `EXP_X5a.mp4`, `EXP_X5b.mp4`로 저장한다. 이름에 클립 id가 꼭 들어가야 한다.
- 선택: `experiment\notes.txt`에 클립마다 눈으로 본 소감을 한 줄씩 적는다(예: `X1: 옷으로 구분됨, C와 E 얼굴 비슷함`).
  - 얼굴이 작은 와이드 샷은 기계 판정이 안 되므로 이 메모가 중요하다.
  - X5a와 X5b는 배경과 두 사람의 위치가 X1과 얼마나 같은지도 적는다. 얼굴 검사기는 배치를 보지 못한다.

---

## C단계: 검사와 보고

### C1. 렌더 파일 확인

```powershell
$H = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\h3-multicast'
Get-ChildItem "$H\experiment\renders" | Select-Object Name, Length
```

확인 기준: X1, X2, X3a, X3b, X3c, X4, X5a, X5b id가 들어간 영상 8개가 있다. 이름이 다르면 사용자에게 어느 파일이 어느 클립인지 묻고, 이름만 바꾼다. X5a/X5b가 없으면(프로젝트 3을 안 했으면) 6개로 진행하고 그 사실을 적는다.

### C2. 얼굴 검사

```powershell
$H = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\h3-multicast'
Set-Location $H
& "$H\.venv\Scripts\python" face_check.py videos --cast experiment\cast.yaml --scene examples\EXP_multicast.yaml --in experiment\renders --out experiment\face --fps 2
```

확인 기준: `experiment\face\face_report.md`와 `face_report.csv`가 생겼다.

### C3. 보고서 작성

`$H\reports\EXP_REPORT.md`를 만든다. 각 항목에 해당 출력을 원문 그대로 붙인다.

1. A1 `git log` 3줄
2. A3 pytest 마지막 줄
3. A4: ComfyUI 버전(`system_stats`), H3 노드 이름 목록, Extender 버전과 커밋, H3 모델 파일 목록
4. A7 얼굴 구분도 출력 전체
5. A8: `experiment\out\EXP\report.md` 전체
6. C2 `face_report.md` 전체
7. X3 비교표: `face_report.csv`에서 X3a, X3b, X3c 행의 `verdict`, `A_hit_ratio`, `A_median_sim`, `B_hit_ratio`, `B_median_sim`, `unknown_faces`, `duplicates`를 표로 옮긴다.
8. X5 비교표: X5a, X5b 행의 `verdict`, `C_hit_ratio`, `C_median_sim`, `D_hit_ratio`, `D_median_sim`, `unknown_faces`, `duplicates`
9. `experiment\notes.txt`가 있으면 그 내용
10. 멈춘 단계가 있으면 그 단계와 이유

그리고 CSV를 `reports`로 복사한다.

```powershell
$H = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm\h3-multicast'
Copy-Item "$H\experiment\face\face_report.csv" "$H\reports\EXP_face_report.csv"
```

### C4. 보고서 올리기

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
git -C $R pull
git -C $R add h3-multicast/reports
git -C $R status --short
git -C $R commit -m "Add H3 six-cast experiment report"
git -C $R push
```

- `git status --short`에 `h3-multicast/reports/` 밖의 파일이나 이미지·영상이 보이면 commit하지 말고 멈춘다.
- push가 실패하면 억지로 해결하지 말고 `EXP_REPORT.md` 전체를 화면에 출력한다. 사용자가 복사해 분석 담당에게 전달한다.
- 성공하면 커밋 해시를 출력한다.
