# bubble-doctor: ComfyUI-BubbleText 말풍선 진단과 수정

[ComfyUI-BubbleText](https://github.com/arturor1990/ComfyUI-BubbleText)를 Qwen Image 2.1 결과에 쓸 때 생기는 문제를 찾고 고치는 도구입니다. 사용자 PC에 설치된 노드 코드를 그대로 불러와 쓰기 때문에, 여기서 보이는 결과가 곧 ComfyUI에서 노드가 하는 동작입니다.

## 확인한 원인 (노드 소스와 재현으로 확인)

| 증상 | 원인 | 해결 |
|---|---|---|
| 한글이 □□로 나옴 | 노드가 보여 주는 글꼴이 Comic Sans, Impact 같은 영문 글꼴과 노드 `fonts/` 폴더뿐이고, 모자란 글자를 메우는 보조 글꼴도 이모지용뿐임 | 한글 글꼴을 노드 `fonts/` 폴더에 넣고 선택 |
| 검은 덩어리에 흰 글씨가 생기고, 한 문장이 두 곳으로 쪼개짐 | README는 검은 말풍선을 "흰 말풍선이 없을 때의 대비책"이라고 하지만, `find_bubbles()`는 항상 둘 다 찾음. 어두운 머리·옷·밤하늘 안에 작은 무늬가 4개 이상 있으면 말풍선으로 잡히고, 넓이가 더 크면 먼저 채워짐 | `patch_bubbletext.py`로 한 줄 수정(흰 말풍선이 있으면 검은 말풍선은 찾지 않음). 백업과 되돌리기 지원 |
| 결과가 완전히 검은 이미지 | 노드 두 번째 출력 `bubble mask`는 말풍선을 못 찾으면 전부 0인 마스크. 이걸 미리보기·저장에 연결하면 새까맣게 보임 | 첫 번째 출력 `IMAGE`를 연결 |
| 글자가 말풍선에 비해 작거나 답답함 | 글자 크기는 "넣을 수 있는 가장 큰 크기"인데 기본 상한이 64px. Qwen Image 출력(예: 1664×928)의 큰 말풍선에서는 작아 보임 | 최대 크기를 짧은 변의 12%(예: 928 → 111), 여백을 0.08 → 0.12로 |
| 말풍선 테두리에 닿은 AI 글자가 남음 | 테두리에 붙은 글자는 테두리의 일부로 인식되어 지워지지 않음 | 노드 구조상 한계. 프롬프트에서 큰 말풍선을 요청하면 줄어듦 |

재현 결과: 흰 말풍선과 검은 머리가 함께 있는 합성 장면에서 원래 노드는 "우리 여섯"을 말풍선에, "명, 다 모였네."를 머리 위에 흰 글씨로 썼습니다. 수정 후에는 문장 전체가 말풍선 하나에 들어가고 머리는 원본 그대로 남았습니다.

## 한글 글꼴

| 글꼴 | 한글 글자 수 (11,172자 중) | 비고 |
|---|---|---|
| NanumGothic-Bold (OFL, 무료) | 11,172 | 추천. 모든 한글 가능 |
| 맑은 고딕 Bold (`C:\Windows\Fonts\malgunbd.ttf`) | 11,172 | Windows 기본. 노드 `fonts/`로 복사해서 사용 |
| Jua, Do Hyeon (OFL) | 2,367 / 2,437 | 만화풍이지만 드문 글자는 빠짐. `fonts` 명령이 대사별로 빠진 글자를 알려 줌 |

## 설치와 사용

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
set BUBBLETEXT_DIR=<ComfyUI>\custom_nodes\ComfyUI-BubbleText
.venv\Scripts\python -m pytest tests -q          10개 통과해야 정상
```

| 명령 | 하는 일 |
|---|---|
| `fonts --node-dir N --text "대사"` (또는 `--text-file 대사.txt`) | 노드가 보는 글꼴마다 한글 글자 수와, 이 대사에서 빠지는 글자 |
| `workflow --node-dir N <json 또는 폴더>` | 워크플로 안 BubbleText 노드의 설정값과 연결. 마스크를 미리보기에 연결함, 한글 대사에 영문 글꼴 같은 문제 표시 |
| `scan --node-dir N --in 이미지폴더 --out 출력 --text "대사"` | 노드가 말풍선으로 보는 영역을 표시(초록 흰 말풍선, 빨강 검은 말풍선, 숫자는 채우는 순서) |
| `render --node-dir N --in 이미지폴더 --out 출력 --text "대사" --font 글꼴 [--current-font ... --current-max-size ... --current-margin ...]` | 원본 / 지금 설정 / 고친 설정을 나란히 붙인 `__compare.png` |
| `fix-workflow 원본.json 새파일.json --font 글꼴 --max-size N --margin M --no-uppercase` | 설정만 바꾼 워크플로 사본을 만듦. 원본은 건드리지 않음 |

`patch_bubbletext.py status|apply|revert --node-dir N`
- 노드 파일 한 줄을 고칩니다. 원본은 `bubble_text.py.orig`로 백업하고, 되돌리면 파일이 바이트 단위로 원래대로 돌아옵니다.
- ComfyUI Manager로 노드를 업데이트하기 전에는 `revert`하고, 업데이트한 뒤 다시 `apply`하세요.
- 적용하거나 되돌린 뒤에는 ComfyUI를 재시작해야 반영됩니다.

**Qwen Image 2.1과 쓸 때**
- `Bubble Text · Prompt` 노드의 `prompt style`은 `natural (Anima)`로 둡니다. Qwen 계열은 문장형 프롬프트를 따릅니다.
- 노드가 프롬프트에 "english text"를 붙이지만 AI가 쓴 글자는 지우고 다시 쓰므로 괜찮습니다.

**라이선스**
- BubbleText 저장소에는 라이선스 파일이 없어서 노드 코드를 이 저장소에 복사하지 않았습니다. 도구는 사용자 PC에 설치된 노드를 불러와 씁니다.

## 이 저장소에서 확인한 것

- **테스트:** 10개 통과. 리눅스 클라우드에서 BubbleText 최신 커밋 `30f16ff`로 실행했고, torch 대신 대체 모듈을 썼습니다.
- **패치:** LF·CRLF 파일 모두 적용 후 되돌리면 원본과 바이트가 같고, 버전이 달라 대상 줄이 없으면 아무것도 바꾸지 않습니다.
- **렌더 비교:** 원래 설정은 두 영역(그중 하나는 검은 영역)에 글자를 썼고, 고친 설정은 흰 말풍선 한 곳에만 썼습니다.
- **아직 확인 못 한 것:** 실제 Qwen Image 2.1 결과 이미지로는 시험하지 않았습니다. `GLM_TASK_BUBBLE.md`가 그 시험입니다.
