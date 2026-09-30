# h3-prompt: MiniMax H3 영상 프롬프트 규격 검사와 에이전트 개선

영상이 자꾸 뜻대로 구성되지 않는 원인이 **프롬프트 형식**에 있는지 먼저 잰다. 그다음 에이전트를 H3 규격대로 고친다.

## H3 프롬프트 규격 (IAMCCS-nodes 코드에서 확인)

IAMCCS-nodes(GPL-3.0, `iamccs_prompter.py`, `iamccs_minimax_h3_shotboard_core.py`)는 H3 프롬프트를 아래 형식으로 조립한다. 코드는 복사하지 않고 규칙만 옮겼다.

- **참조 모드(ref2v, 참조 그림·오디오):** 제목 6개를 이 순서로 쓴다: `subject_definitions:` → `summary:`(`[reference generation]`으로 시작) → `retention_analysis:` → `detailed_description:` → `overall_soundscape:` → `non_diegetic_music:`. 빈 칸은 `N/A`로 쓴다.
- **기본 모드(t2v, i2v):** `integrated_multimodal_description:`(`[Shot 1]`로 시작) → `overall_soundscape:` → `non_diegetic_music:`
- **태그:** 인물·사물은 `<Subject N>`, 참조는 `<Picture N>`·`<Audio N>`·`<Video N>`. 대사는 `<Subject 1> (S1): <d>[Korean] 대사 그대로</d>`로 쓰고, 없는 말은 지어내지 않는다.
- **립싱크:** `<Audio 1>`을 `retention_analysis`에 `fully_copy`로 두고, 입 모양은 그 오디오에 맞추라고만 쓴다. 발음 기호를 글로 풀어 쓰지 않는다.
- **긍정문만:** "no / do not / never / without / avoid"로 시작하는 문장을 쓰지 않고, 보여야 할 상태를 쓴다. 음악 칸의 "No score"만 예외다.
- **카메라:** 이유 있는 움직임 하나. 여러 움직임을 나열하지 않는다.
- **컷:** 실제로 뒤에 오는 컷만 `[Shot N] At MM:SS.mmm`으로 쓰고, 컷을 지어내지 않는다.
- **시간:** 24 fps. 프레임 수는 17k+5, 학습 최대 362프레임(약 15초), 프롬프트는 7000자 이하. 시간 줄은 `0.00-1.40s: ...` 또는 `Timeline 0.00s to 2.50s: ...`로 쓴다.
- **Extender(여러 조각):** 마지막 조각이 아니면 대사는 조각 끝 1초 전에 끝내고, 다음 조각의 첫 1초는 주변 소리와 이어지는 동작만 둔다. 조각마다 시간은 그 조각 시작을 0초로 다시 센다.

## `h3lint.py`

프롬프트가 위 규격을 지키는지 검사한다. 한 인물을 she와 he로 섞어 부르는지, 참조를 `<Picture 1>`이 아니라 `Picture 1`로 쓰는지, 조립하다 제목(`detailed_description:`)이나 같은 문장이 본문 안에 한 번 더 붙었는지도 본다. `[Shot N]` 표시는 장면을 설명하는 칸에서만 센다(`retention_analysis`가 `[Shot 1]`을 가리키는 것은 세지 않는다). 어긴 규칙 이름과 개수만 보고하고, 프롬프트 문장은 보고서에 넣지 않는다. IAMCCS 조립기로 만든 공식 예제 4개는 모두 통과한다.

```powershell
python h3lint.py check work\h3_prompts.jsonl --frames 90 --chunk-ends 3.75,7.5 --report reports\H3LINT_CURRENT.md --details work\h3lint_details.jsonl
python h3lint.py shape work\h3_prompts.jsonl --n 3      # 글자 없이 뼈대만: 제목, [Shot N], 태그, 시각, (N단어)
python -m pytest -q tests      # 10 passed
```

입력은 `.txt`(프롬프트 하나), `.json`(문자열 목록이나 `prompt` 키가 있는 객체), `.jsonl`, 또는 이런 파일이 든 폴더다.

## 순서

1. 지금 에이전트가 만든 최근 프롬프트를 이 검사기로 잰다(읽기만).
2. 새 에이전트를 만든다. LLM은 칸(JSON)만 채우고, 코드가 위 규격으로 조립한다. 조립된 프롬프트를 이 검사기로 다시 검사해서, 어기면 최대 2번 다시 쓰게 한다.
3. 스위치를 두고 기존 방식과 함께 돌려(observe) 검사 결과를 비교한다. 그다음 같은 컷을 두 방식으로 만들어 비교한다.
