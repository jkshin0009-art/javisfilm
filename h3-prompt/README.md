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
python -m pytest -q tests      # 21 passed (h3lint 11 + h3compose 10)
```

일부러 다른 형식을 쓰는 곳(예: MV의 대사 형식과 사고 방지 부정 조항)은 `--ignore dialogue_format,negative_language`로 빼고 회귀 검사로 쓴다.

입력은 `.txt`(프롬프트 하나), `.json`(문자열 목록이나 `prompt` 키가 있는 객체), `.jsonl`, 또는 이런 파일이 든 폴더다.

## `h3compose.py`: H3 프롬프트를 만드는 한 곳 (컴포넌트와 상속)

| 컴포넌트 | 하는 일 | 상속해서 바꾸는 것 |
|---|---|---|
| `Clip` | 기본(t2v) 문법으로 한 클립을 조립 | — |
| `FirstFrameClip(Clip)` | i2v: 첫 프레임 정렬 줄 | `prefix()`만 |
| `ReferenceClip(Clip)` | 참조 모드 제목 6칸, 인물 정의, 유지 분석 | `blocks()`, `definitions()`, `retention()` |
| `LipsyncClip(ReferenceClip)` | `<Audio 1>` 1:1 재사용과 입 모양 맞춤 문장 | `definitions()`, `retention()`, `body_parts()`에 한 줄씩 더함 |
| `Checker` | 클립 규칙 + h3lint + Jev 뜻 질문 | 경로마다 일부러 유지하는 규칙은 `ignore`로 (`MVChecker`) |
| `Writer` | LLM에 내용 칸을 받아 조립·검사·재시도 | 경로(실행기, 콘티 애니매틱, 대화 앱, MV)는 `facts()`만 바꿔 상속 |

운동 동작 컷은 `sports-pose`의 연속 동작(`library/sequences.json`, 예: 배구 스파이크 = 도약 → 팔 젖히기 → 타격)을 `facts["sports_sequence"]`로 넘긴다. 작가는 단계 순서대로 동작 줄을 만들고, 단계마다 검사를 통과한 몸 동작(관절 각도, 발, 손, 공 접촉)을 그대로 쓴다.

프로젝트의 H3 작가 10곳은 새로 만들지 않고, 각각 `Writer`를 상속해 `facts()`만 채우는 얇은 어댑터로 바꾼다. 곳마다 따로 있던 틀과 검사 함수는 옮긴 뒤 지운다.

LLM은 내용 칸(장면, 시간별 동작, 연기, 카메라, 빛, 소리, 음악, 요약)만 JSON으로 채운다. 규격 문자열은 코드가 조립한다.

- 인물은 `<Subject N>`으로만 부른다(he/she 금지). 성별과 외형은 캐스트 장부에서 받아 `subject_definitions`에 쓴다.
- 대사는 주어진 글 그대로 `<Subject N> (SN): <d>[Korean] …</d>`로, 말하는 시각이 속한 동작 줄에 넣는다.
- 한 클립에는 한 구도만. 사실(facts)에 구도가 둘이면 LLM은 `{"split": [...]}`로 답하고, 부른 쪽이 클립을 나눈다.
- 조립한 뒤 h3lint 규칙, 클립 규칙(17k+5, 동작 시각, 조각 경계 1초), 그리고 원하면 Jev 뜻 질문(한 클립에 두 구도? 카메라가 구도와 안 맞나?)으로 검사한다. 어기면 이유를 붙여 최대 3번까지 다시 쓰게 한다.
- 입력 `shot` = `{mode: base|i2v|ref, frames, subjects:[{look, gender, picture}], lipsync_audio, final_chunk, continues_previous, sections:{dialogue:[{subject, lang, text, start}]}}`, `facts` = 컷의 사실(비트, 장소, 시간, 카메라 힌트 등).

```powershell
python h3compose.py try work\cut01.json --judge --out work
ew     # {shot, facts} 하나로 새 프롬프트 만들기
python -m pytest -q tests                                            # 16 passed
```

## 순서

1. 지금 에이전트가 만든 최근 프롬프트를 이 검사기로 잰다(읽기만).
2. 새 에이전트를 만든다. LLM은 칸(JSON)만 채우고, 코드가 위 규격으로 조립한다. 조립된 프롬프트를 이 검사기로 다시 검사해서, 어기면 최대 2번 다시 쓰게 한다.
3. 스위치를 두고 기존 방식과 함께 돌려(observe) 검사 결과를 비교한다. 그다음 같은 컷을 두 방식으로 만들어 비교한다.
