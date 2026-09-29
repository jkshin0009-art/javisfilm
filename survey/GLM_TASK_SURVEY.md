# 작업 지시서: film_assistant 프로젝트 구조 조사 (실행 담당용)

목표는 분석 담당이 프로젝트를 모르는 채로 만든 도구들(`llama-swift15`, `h3-multicast`, `bubble-doctor`)을 실제 프로젝트에 맞게 고칠 수 있도록, `C:\Users\Administrator\Desktop\film_assistant`의 **구조**를 보고하는 것이다.
이 문서는 **읽고 기록**만 한다. 아무것도 고치거나 실행하지 않는다.

## 반드시 지킬 규칙

1. **읽기만 할 것:** 파일을 수정, 이동, 삭제하지 않는다. 프로그램, 서버, 학습, 생성을 실행하지 않는다.
2. **내용은 적지 말 것:** 줄거리, 대사, 인물 설명, 대본 문장은 보고서에 적지 않는다. 파일 이름, 폴더 구조, 코드의 역할, 설정 항목 이름까지만 적는다. 저장소가 공개 저장소다.
3. **비밀값은 가릴 것:** API 키, 토큰, 비밀번호, 이메일은 `***`로 가린다.
4. **추측과 확인을 나눌 것:** 모르는 것은 "확인 못 함"으로 적는다. 추측으로 채우지 않는다. 추측한 내용은 "추정:"을 붙인다.
5. **셸:** 명령은 PowerShell 기준이다.

## 1. 폴더 구조

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
Get-ChildItem $P -Directory -Recurse -Depth 2 -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|__pycache__|\.venv|venv|javisfilm)(\\|$)' } |
  ForEach-Object { $_.FullName.Substring($P.Length) }
Get-ChildItem $P -File -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|__pycache__|\.venv|venv|javisfilm)\\' } |
  Group-Object Extension | Sort-Object Count -Descending |
  Select-Object Name, Count, @{n='MB';e={[math]::Round(($_.Group | Measure-Object Length -Sum).Sum/1MB,1)}}
```

## 2. 코드와 실행 방법

- `.py`, `.js`, `.ts`, `.bat`, `.ps1` 파일 목록을 뽑는다.
- 각 파일의 첫 주석이나 README를 읽고 파일마다 **한 줄**로 역할을 적는다.
- 실행 진입점을 찾는다(메인 스크립트, 배치 파일, 웹 서버 등).
- 의존성을 적는다: `requirements.txt`, `package.json`, `pyproject.toml`의 주요 패키지.
- git 저장소인지 확인하고, 맞으면 `git log --oneline -10`과 원격 주소(`git remote -v`, 비밀값은 가림)를 적는다.

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
Get-ChildItem $P -File -Recurse -Include *.py,*.js,*.ts,*.bat,*.ps1 -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|__pycache__|\.venv|venv|javisfilm)\\' } |
  Select-Object @{n='file';e={$_.FullName.Substring($P.Length)}}, @{n='lines';e={(Get-Content $_.FullName -ErrorAction SilentlyContinue | Measure-Object -Line).Lines}}
Get-ChildItem $P -File -Include README*,requirements*.txt,package.json,pyproject.toml -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object FullName
git -C $P log --oneline -10 2>$null
```

## 3. ComfyUI 워크플로

`film_assistant` 안의 `.json` 중 ComfyUI 워크플로(최상위에 `nodes`와 `links`가 있거나, 값마다 `class_type`이 있는 파일)를 찾는다. 각 파일마다 다음을 적는다.
- 파일 경로
- 쓰인 노드 종류와 개수(`type` 또는 `class_type`별)
- MiniMax H3, Extender, SpeechBubble(말풍선), Qwen Image, LoRA, 업스케일, 얼굴 관련 노드가 있으면 그 노드들의 설정값. 긴 프롬프트 문장은 적지 말고 "프롬프트 N자"로 적는다.

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
foreach ($f in Get-ChildItem $P -File -Recurse -Filter *.json -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|javisfilm)\\' }) {
  try { $j = Get-Content $f.FullName -Raw -Encoding utf8 | ConvertFrom-Json } catch { continue }
  $types = @()
  if ($j.nodes) { $types = $j.nodes | ForEach-Object { $_.type } }
  elseif ($j.PSObject.Properties | Where-Object { $_.Value.class_type }) { $types = $j.PSObject.Properties | ForEach-Object { $_.Value.class_type } }
  if ($types.Count) {
    "== " + $f.FullName.Substring($P.Length)
    $types | Group-Object | Sort-Object Count -Descending | ForEach-Object { "   {0} x{1}" -f $_.Name, $_.Count }
  }
}
```

## 4. 영화 제작 자료의 형식

내용은 적지 않고 **형식과 위치**만 적는다.
- **인물 자료:** 캐릭터 시트, 얼굴 이미지, LoRA가 어디에 어떤 이름 규칙으로 있는지, 인물이 몇 명인지. 인물 정보가 들어 있는 설정 파일(yaml, json, csv 등)이 있으면 그 **항목 이름**(키 이름)만 적는다.
- **대본·장면 자료:** 대본, 장면 목록, 샷 목록이 어떤 파일 형식으로 어디 있는지, 장면과 샷을 어떻게 나누고 번호를 매기는지.
- **결과물:** 생성된 이미지와 영상이 어디에 어떤 이름 규칙으로 쌓이는지, 대략 몇 개인지.
- **말풍선:** 말풍선을 넣는 단계가 워크플로 어디에 있는지, 이전에 누가 만든 스크립트나 수정본이 있는지. 사용자가 말한 "검은 이미지"를 만드는 부분으로 보이는 것이 있으면 그 파일 경로와 역할을 적는다.

## 5. 이미 있는 기능

아래 각 항목이 프로젝트에 **이미 있는지** 적는다. 있으면 파일 경로를 적는다.
- 인물 일관성 처리(참조 이미지 관리, LoRA, 얼굴 교체 등)
- H3 프롬프트를 만드는 코드나 템플릿
- 로컬 LLM(llama.cpp, LM Studio 등)을 부르는 코드
- 장면·샷을 관리하는 목록이나 도구
- 말풍선, 자막, 텍스트 합성

## 6. 보고서

`C:\Users\Administrator\Desktop\film_assistant\javisfilm\survey\reports\SURVEY_REPORT.md`에 1~5단계 결과를 정리한다. 명령 출력은 원문 그대로 붙이고, 역할 설명은 한 줄씩 쓴다.

마지막에 **분석 담당에게 묻고 싶은 것**을 적는다. 조사하면서 판단이 필요했던 점을 3개 이내로 쓴다.

**올리기 전에 사용자에게 보고서를 보여주고 공개 저장소에 올려도 되는지 묻는다.**
- 사용자가 안 된다고 하면 올리지 않고, 보고서 전체를 화면에 출력한다.
- 된다고 하면 아래를 실행한다.

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
git -C $R pull
git -C $R add survey/reports
git -C $R status --short
git -C $R commit -m "Add film_assistant structure survey"
git -C $R push
```

- `git status --short`에 `survey/reports/` 밖의 파일이 보이면 commit하지 말고 멈춘다.
- push가 실패하면 보고서 전체를 화면에 출력한다.
