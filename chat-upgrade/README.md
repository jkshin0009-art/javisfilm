# chat-upgrade: 루프형 다자 챗봇에 판단 능력 붙이기

film_assistant의 챗봇(여러 인물이 대화하고, 사용자가 말하지 않아도 스스로 말하는 루프형 챗봇)을 **엔진은 그대로 두고** 업그레이드하는 부품입니다. 지금 쓰는 LLM 서버(llama-server)와 dots.tts를 그대로 씁니다.

| 파일 | 하는 일 | 가져온 곳 |
|---|---|---|
| `chatup/decide.py` | **Jev식 판단.** 질문을 선택지·예/아니오·점수로 묻고, 글을 생성하지 않고 첫 토큰 확률만 읽어 "답 + 확률"을 돌려줌 | Jev(TypeSafe)의 방식, AnyJev(Apache-2.0)의 L0 방법 |
| `chatup/judge.py` | 챗봇이 턴 사이에 내리는 판단 8가지(아래 표) | 새로 작성 |
| `chatup/shaper.py` | LLM 출력 → 말할 문장 단위. `<think>`·특수 토큰 제거, 감정·제스처·이미지 태그 읽기, 한국어 문장 자르기 | little-gemma-tools의 clausecat |
| `chatup/policy.py` | 질문하면 턴 끝내기, 턴 길이 상한, 같은 말 반복 막기 | little-gemma의 `-end-on-question`, `SERVE_GEN` |
| `chatup/voice.py` | 인물별·감정별 dots.tts 참조 음성 고르기, 말하는 중 끊기(끼어들기) | little-gemma-tools의 `--route-emotion`, voicecat 끼어들기 |
| `chatup/llm.py` | 기존 LLM 서버 연결: 스트리밍, 취소, 멈춤 감지, 첫 토큰 확률 | 새로 작성(표준 라이브러리만) |
| `chatup/loop.py` | 위 부품을 묶은 참고용 루프. 프로젝트 루프에는 필요한 부품만 옮겨 붙임 | little-gemma 자율 대화 데모의 상한 규칙 |
| `python -m chatup probe` | 우리 LLM에서 판단이 제대로 되는지, 몇 ms 걸리는지 재는 점검 | |

## Jev가 무엇이고 어떻게 적용했나

[Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)는 TypeSafe AI의 "System One" 판단 모델입니다. 글을 쓰지 않고, 상태와 **정해진 형식의 질문**을 받아 **답과 확률**을 돌려줍니다. 규칙은 간단합니다. 답이 결정이면 판단 모델, 답이 글이면 LLM.

Jev 자체는 클라우드 API라서 로컬 영화 프로젝트에는 맞지 않습니다. 대신 [AnyJev](https://github.com/nokia-applied-research/AnyJev)가 보여 준 방법을 씁니다. **어떤 LLM이든 학습 없이** Jev처럼 쓸 수 있습니다.

1. 질문과 선택지를 `A. 하나 / B. 도윤 / C. 미래` 형식으로 보여 주고, 토큰을 **하나도 생성하지 않은 채** 첫 토큰 확률에서 A/B/C의 확률을 읽습니다. llama-server의 `logprobs`/`top_logprobs`를 씁니다.
2. LLM은 "A"나 먼저 나온 선택지를 좋아하는 버릇이 있습니다. 그래서 선택지 순서를 돌려 가며 여러 번 읽고 평균합니다. AnyJev 실험에서 순서를 바꾸면 답이 바뀌는 비율이 0.230에서 0.073으로 줄었습니다.
3. 답이 뚜렷하면 두 번만 읽고 멈춥니다(`adaptive`). 짧은 요청 두 번으로 끝납니다.
4. 결과는 `Decision(answer, confidence, level)`입니다. 코드는 확률이 기준 이상일 때만 판단을 따르고, 아니면 원래 규칙으로 돌아갑니다. 이것이 Jev식 사용법입니다(판단은 모델이, 결정 규칙은 코드가).

### 챗봇이 내리는 판단

| 판단 | 형식 | 판단을 쓰는 곳 | 확신이 없을 때 |
|---|---|---|---|
| `next_speaker` 다음에 누가 말할까 | 선택 | 자율 발화, 사용자 말 뒤 | 가장 오래 말 안 한 인물 |
| `addressed` 사용자가 누구에게 말했나 | 선택(+모두) | 사용자 말 뒤 | 이름이 나오면 그 인물 |
| `should_speak` 지금 먼저 말을 꺼내도 되나 | 예/아니오 | 자율 발화 시작 전 | 말함 |
| `wants_stop` 사용자가 그만하라고 했나 | 예/아니오 | 사용자 말 뒤 | 계속 |
| `stuck` 대화가 제자리를 도나 | 예/아니오 | 자율 발화 몇 턴마다(반복도가 높을 때만) | 그대로 |
| `route` 지금 할 일(대화 계속 / 이미지 / 시나리오 메모 / 사용자에게 묻기) | 선택 | 몇 턴마다 | 대화 계속 |
| `emotion` 이 대사의 감정(음성 고르기) | 선택 | 태그가 없을 때(선택 사항) | neutral |
| `reply_bad` 이 대답이 반복·대신 말하기인가 | 예/아니오 | 스트리밍 없이 만든 대답 검사 | 그대로 |

## 설계에서 정한 것

- **생각 끄기:** 판단 요청과 대사 요청 모두 `chat_template_kwargs={"enable_thinking": false}`를 보냅니다. 생각이 켜져 있으면 첫 토큰이 `<think>`가 되어 판단을 읽을 수 없습니다. 이때는 `level=none`이 되고 규칙으로 돌아갑니다. probe의 `label mass`가 낮으면 생각이 꺼지지 않은 것입니다.
- **감정 음성:** dots.tts에는 감정 설정이 없고 참조 음성의 말투를 따라 합니다. 그래서 `voices/<인물>/<감정>.wav`와 같은 이름의 `.txt`(그 음성에서 하는 말)를 두고 감정별로 참조 음성을 바꿉니다. 없는 감정은 neutral로 대신합니다. `dots.tts.edit`의 감정 태그는 한 번 더 돌려야 해서 실시간 대화에는 느립니다.
- **끼어들기:** 사용자가 말하면 생성과 음성을 바로 끊습니다. 기록에는 **실제로 들린 부분까지만** `(끼어듦)` 표시와 함께 남깁니다. 다음 턴에서 모델이 자기가 끝까지 말했다고 착각하지 않게 하기 위해서입니다.
- **자율 발화 상한:** 사용자 없이 이어지는 턴 수(기본 12)와 시간(기본 30분)에 상한을 둡니다. 빈 대답이나 멈춤이 3번 이어지면 쉽니다. 사용자가 말하면 다시 시작합니다.
- **슬롯:** 서버를 `-np 1`로 띄우면 판단 요청과 대사 요청이 한 슬롯을 번갈아 씁니다. 그러면 대사 쪽 캐시가 밀려 다시 계산됩니다. 슬롯 2개(`-np 2`) 이상이면 `LLMClient(slot_id=1)`로 판단 전용 슬롯을 쓸 수 있습니다.

## 쓰는 법

표준 라이브러리만 씁니다. 테스트에는 pytest가, 음성에는 dots.tts·numpy·sounddevice가 필요합니다.

```powershell
cd C:\Users\Administrator\Desktop\film_assistant\javisfilm\chat-upgrade
python -m pytest -q tests                                   # 50 passed
python -m chatup probe --url http://127.0.0.1:5678 --report reports\CHAT_PROBE.md
python -m chatup chat --url http://127.0.0.1:5678 --show-decisions   # 예시 인물 3명, 글자만
python -m chatup voices --bank D:\voices --personas hana,doyun      # 참조 음성 폴더 점검
```

프로젝트 코드에 붙일 때는 필요한 부품만 가져갑니다.

```python
from chatup.llm import LLMClient
from chatup.decide import Decider
from chatup.judge import ConversationJudge, Line

client = LLMClient("http://127.0.0.1:5678")
judge = ConversationJudge(Decider(client, log_path="logs/decisions.jsonl"), roster="하나: 촬영 감독\n...")
v = judge.next_speaker([Line("사용자", "..."), Line("하나", "...")], ["하나", "도윤", "미래"])
speaker = v.value or fallback_rule()        # v.decision.confidence, v.decision.level 로 근거 확인
```

`logs/decisions*.jsonl`에는 판단마다 상태·분포·답이 쌓입니다. 나중에 맞고 틀림을 표시하면 AnyJev의 L1/L2(보정, 가벼운 판단 머리)로 올릴 수 있는 재료가 됩니다. 로그에는 대화 내용이 들어가므로 git에 올리지 않습니다(`.gitignore`).
