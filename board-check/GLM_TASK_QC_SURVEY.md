# 작업 지시서: 콘티 프롬프트와 기존 검수기 조사 (실행 담당용, 읽기만)

## 왜 하는가

사용자는 하루 5시간 넘게 콘티 그림을 눈으로 보고 고치라고 지시한다. 그런데도 맥락이 안 맞거나 잘못된 그림이 계속 나온다. 사용자가 정한 순서는 이렇다.
1. 그림을 만드는 **프롬프트가 콘티와 정확히 맞아야** 한다.
2. **이미 있는 검수기**가 제 역할을 해야 한다. 지금은 믿을 수 없다.
3. 틀린 것은 **자동으로 고쳐져야** 한다.
4. 그다음이 최종 검수다.

분석 담당이 이 순서대로 고치려면, 지금 구조를 정확히 알아야 한다. 이 문서는 **읽고 기록**만 한다.

## 반드시 지킬 규칙

1. **읽기만:** 파일을 고치지 않는다. 검수기, 생성, 서버를 실행하지 않는다.
2. **내용은 적지 말 것:** 줄거리, 대사, 인물 설명, 프롬프트 문장은 적지 않는다. 파일:줄, 함수 이름, 키 이름, 개수, 시간만 적는다. 프롬프트나 질문 문장은 "영문 N자", "한글 N자"처럼 길이만 적는다. 비밀값은 `***`로 가린다.
3. **추측 표시:** 확인 못 한 것은 "확인 못 함", 추측은 "추정:"을 붙인다.
4. 셸은 PowerShell 기준이다.

## S1. 콘티 → 프롬프트 → 그림 흐름

콘티 한 컷이 그림이 되기까지의 단계를 순서대로 적는다. 단계마다 다음을 적는다.
- 파일:함수
- 입력(어느 키를 읽는지)과 출력(어느 키에 저장하는지)
- 쓰는 모델과 주소: LLM(5678 등), ComfyUI 워크플로 이름
- 프롬프트를 LLM이 쓰는지, 틀(템플릿)로 조립하는지

특히 아래를 확인한다.
- `manifest.json`의 컷(panel) 항목에서 "이 컷이 보여 줘야 할 것"(콘티 설명)과 "그림 생성에 실제로 넣은 프롬프트"가 **따로 저장되는지**, 각각 키 이름은 무엇인지
- 인물 참조(얼굴·LoRA·캐릭터 시트)가 프롬프트나 워크플로에 어떻게 들어가는지
- 한 콘티에 컷이 몇 개인지, 컷마다 그림을 몇 장 만드는지(후보 여러 장인지)

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
Get-ChildItem "$P\tools", "$P\visuals", "$P\core" -Recurse -Include *.py -ErrorAction SilentlyContinue |
  Select-String -Pattern 'manifest|panel|storyboard|comic_|prompt' -List |
  ForEach-Object { $_.Path.Substring($P.Length) } | Sort-Object -Unique
```

## S2. 이미 있는 검수기

그림이나 컷을 판정하는 코드를 **모두** 찾는다. 예: `tools/greenlight.py`, `tools/comic_board.py`의 `check_*`, `tools/comic_animatic.py`의 진행 중단 조건. 그 밖에 이름에 judge, verdict, review, qa, check, gate, 검수, 판정이 들어간 것.

```powershell
$P = 'C:\Users\Administrator\Desktop\film_assistant'
Get-ChildItem $P -Recurse -Include *.py -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|__pycache__|\.venv|venv|javisfilm|_trash|_checkpoint)' } |
  Select-String -Pattern 'greenlight|judge|verdict|review|check_|gate|검수|판정|reject|redo|regenerat' |
  Group-Object Path | Sort-Object Count -Descending | Select-Object -First 40 |
  ForEach-Object { "{0}  ({1})" -f $_.Name.Substring($P.Length), $_.Count }
```

검수기마다 표 한 줄로 적는다.

| 항목 | 적을 것 |
|---|---|
| 위치 | 파일:함수, 실행 방법(CLI, 웹, 생성 직후 자동 호출 등) |
| 무엇을 보나 | 검사 항목 목록(말풍선, 얼굴, 인물 수, 콘티 일치 등) |
| 어떻게 보나 | SAM3 같은 검출 모델인지 LLM인지. LLM이면 질문 형식(자유 서술 / JSON / 예·아니오), 생각 켜짐 여부, max_tokens, 이미지 해상도 |
| 기준 | 통과·실패를 가르는 값과 줄 번호 |
| 결과 저장 | 판정 결과가 남는 파일과 키 이름 |
| 실패하면 | 자동 재생성(몇 번까지), 표시만, 사람에게 넘김, 아무것도 안 함 중 무엇인지. 코드 줄로 확인 |
| 걸리는 시간 | 로그에 시각이 있으면 컷 하나에 몇 초인지 |

## S3. 사람이 고친 기록 (정답 자료가 있는가)

검수기를 믿을 수 있는지 재려면 "사용자가 틀렸다고 한 컷"의 기록이 필요하다. 아래를 찾아 **개수와 위치만** 적는다.
- `manifest.json` 안에 재생성 이력(버전, seed 변경 이력, rejected·redo 같은 표시, 이전 파일 이름)이 남는지, 그 키 이름
- 컷 그림의 옛 버전 파일(`pNN_v2.png`, `old\`, `_rejected\` 같은 것)이 남는지, 몇 개인지
- 대화 기록(`data\chat_sessions\`)에서 사용자가 컷을 다시 그리라고 한 메시지 수. 내용은 적지 말고 개수만 센다. 예: "다시", "고쳐", "틀렸", "안 맞", "재생성"이 들어간 사용자 메시지 수
- 검수기 판정과 사용자 지시가 **같은 컷에 대해 둘 다** 남아 있는 경우가 있는지, 몇 건인지. 이것이 가장 중요한 정답 자료다.

## S4. 규모

- 콘티 폴더 수, 전체 컷 수, 검수기 판정이 남은 컷 수, 한 번 이상 다시 그린 컷 수
- 가장 최근 콘티 하나를 골라 컷마다 한 줄씩 표로 적는다. 칸은 컷 번호 / 콘티 설명 있음 / 프롬프트 저장됨 / 검수 판정(통과·실패·없음) / 다시 그린 횟수이고, 내용은 적지 않는다.

## S5. 보고

`C:\Users\Administrator\Desktop\film_assistant\javisfilm\board-check\reports\QC_SURVEY.md`에 S1~S4를 적는다. 끝에 **분석 담당에게 묻고 싶은 것**을 3개 이내로 적는다.

사용자에게 보여 주고, 허락하면 `board-check/reports`만 add해서 커밋·push한다. push가 실패하면 보고서 전문을 화면에 출력한다(사용자가 분석 담당에게 붙여 넣는다).
