# h3-multicast: MiniMax H3로 5~6명이 나오는 장면 만들기

MiniMax H3(Hailuo 3.0)와 ComfyUI MiniMax H3 Extender로 영화를 만들 때, 인물이 5~6명 이상 나오는 장면에서 얼굴을 유지하기 위한 도구 두 개입니다.

| 파일 | 하는 일 |
|---|---|
| `h3_scene.py` | 캐스트 파일과 장면 파일을 읽어 클립마다 H3 공식 형식(여섯 구간) 프롬프트와 슬롯 배치표를 만들고, 규칙 위반을 검사 |
| `face_check.py` | 만들어진 영상의 얼굴을 인물 참조 얼굴과 비교해 샷마다 PASS / CHECK / REDO를 판정하고 다시 만들 클립을 뽑음 |
| `GLM_TASK_H3.md` | PC의 실행 담당(GLM)이 6인 시험을 돌리는 지시서 |

## 설계 근거 (원문 확인)

| 사실 | 출처 |
|---|---|
| Ref2VA 참조는 이미지 9장, 영상 3개, 오디오 3개, 파일 합계 12개까지 | [MiniMax-H3 README](https://github.com/MiniMax-AI/MiniMax-H3) |
| 프롬프트는 `subject_definitions` → `summary` → `retention_analysis` → `detailed_description` → `overall_soundscape` → `non_diegetic_music` 순서. 한 클립 안에서 `[Shot N] At MM:SS.mmm`으로 컷을 나눌 수 있고, 화자는 `<Subject N> (Sx)`, 대사는 `<d>[언어] ...</d>` | [공식 Ref2VA 가이드 ref-en.txt](https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/h3-prompt-writing/references/ref-en.txt) |
| Extender는 슬롯 9칸을 고정 번호로 관리하고, 생성할 때 채워진 슬롯만 순서대로 H3에 보내면서 프롬프트의 `<Picture N>`, `<Video N>`, `<Audio N>` 번호를 자동으로 바꿔 줌. 빈 슬롯 번호를 쓰면 바뀌지 않고 남아서 참조가 에러 없이 연결되지 않음 | Extender v2.9.1 소스 `extender.py`의 `_prepare_shared_refs`, `_remap_numbered_tags` |
| 전체 공통 참조는 모든 클립에 들어가고, 클립별 참조는 같은 번호의 공통 참조를 그 클립에서만 덮어씀 | 같은 소스, 클립 루프 |
| H3는 화면을 32배 축소한 격자로 처리함. 864×480 중간 샷에서 얼굴이 약 2칸 | [h3-studio README](https://github.com/CharlesMod/h3-studio) |
| 여러 명이 말하면 목소리가 다른 인물에게 섞이는 문제(해결 안 됨) | [MiniMax-H3 이슈 #17](https://github.com/MiniMax-AI/MiniMax-H3/issues/17) |

그래서 기본 방식은 이렇습니다.
- **슬롯 고정:** 영화 전체에서 인물마다 슬롯 번호를 고정합니다(1~6 인물, 7 장소, 8 단체 배치 이미지, 9 예비). Extender가 번호를 알아서 바꿔 주므로 가능합니다.
- **씬 단위 프로젝트:** 씬마다 Extender 프로젝트를 하나 만들고, 그 씬의 인물을 공통 참조로 넣습니다.
- **나눠 찍기:** 6명 샷은 옷·머리·위치로 구분하고, 얼굴이 중요한 샷은 2~3명 이하로 나눠 찍습니다.
- **대사는 클립당 2명까지:** 목소리 섞임 문제 때문입니다.

## 설치

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt      (Linux/macOS: .venv/bin/pip)
.venv\Scripts\python -m pytest tests -q            33개 통과해야 정상
```

`face_check.py`는 처음 실행할 때 InsightFace `buffalo_l` 모델(약 280MB)을 `~/.insightface`에 자동으로 받습니다.

## 1. 캐스트 파일 (`examples/cast.yaml`)

인물마다 한 번 적고 영화 전체에서 씁니다.

```yaml
characters:
  - id: A              # 장면 파일에서 쓰는 짧은 이름
    name: Minji
    slot: 1            # Extender <Picture N> 슬롯. 영화 전체에서 고정 (1~9, 중복 불가)
    look: a woman in her late twenties with a short silver bob, a red wool coat and round gold glasses
    short: the woman in the red coat
    sheet: assets/A_sheet.png   # 캐릭터 시트 (Qwen Image 2.1 등)
    face: assets/A_face.png     # 얼굴 클로즈업 (face_check 기준 얼굴)
    voice: assets/A_voice.wav   # 2~15초 음성 샘플 (대사가 있을 때 <Audio N>)
locations:
  - {id: diner, slot: 7, look: "...", short: "the diner", image: assets/diner.png}
```

- `look`과 `short`는 **영어 명사구**로 씁니다. H3 프롬프트는 영어여야 하고, 한국어는 대사(`<d>`) 안에만 들어갈 수 있습니다.
- 6명의 `look`은 머리색·길이, 옷 색 하나, 소품 하나가 서로 겹치지 않게 짓습니다. 와이드 샷에서는 이것만으로 인물을 구분합니다.
- 장소에 `image`가 없으면 슬롯을 쓰지 않고 글로만 묘사합니다.

## 2. 장면 파일 (`examples/S01_diner.yaml`)

```yaml
scene: S01
location: diner
resolution: [1344, 768]
blocking: [E, C, A, B, D, F]        # 씬 전체의 왼쪽→오른쪽 순서 (180도 규칙)
group_plate: {image: assets/S01_group.png, slot: 8, role: anchor}
policy: {slots: fixed, load: scene, unused: omit}
clips:
  - id: C01
    duration: 10
    seed: 1234                       # 선택
    shots:
      - framing: wide
        cast: [E, C, A, B, D, F]
        group_plate: true
        action: "{D} taps his glass and everyone turns toward {A}"   # {A} -> <Subject N>
      - at: 5.5
        framing: close-up
        cast: [A]
        lines:
          - {who: A, lang: Korean, text: 이제 다들 솔직하게 말할 때야., delivery: quietly}
```

- `framing`: `extreme-wide`, `wide`, `full`, `medium`, `over-the-shoulder`, `medium-close`, `close-up`, `extreme-close-up`
- `policy`는 씬 전체에 주고, 클립마다 덮어쓸 수 있습니다.
  - `slots: fixed`: `<Picture N>` = 캐스트 슬롯 번호 (Extender용, 기본값)
  - `slots: compact`: 클립마다 1부터 번호를 새로 매김 (번호를 바꿔 주지 않는 다른 워크플로용)
  - `load: scene`: 씬에 나오는 인물 전원을 공통 참조로 넣음 (씬당 Extender 프로젝트 1개)
  - `load: clip`: 그 클립에 나오는 인물만 넣음 (클립별 참조)
  - `unused: omit` / `define_absent`: 공통 참조로 들어갔지만 화면에 없는 인물을 설명하지 않을지, "이 클립에 나오지 않음"으로 적을지

## 실행

```
python h3_scene.py build examples/S01_diner.yaml --cast examples/cast.yaml --out out
python h3_scene.py check examples/S01_diner.yaml --cast examples/cast.yaml --check-files
python h3_scene.py build ... --llm http://127.0.0.1:5678     # 로컬 LLM으로 detailed_description 확장
```

`out/S01/`에 클립마다 세 파일이 생깁니다.
- `C01.prompt.txt`: Extender 클립 카드에 붙여 넣을 프롬프트
- `C01.refs.txt`: 어느 슬롯에 어떤 파일을 넣을지, 공통 참조인지 클립별 참조인지
- `report.md`: 오류·경고·참고 목록

**검사 항목**

| 구분 | 내용 |
|---|---|
| 오류 | 참조 한도 초과, 슬롯 충돌, 샷 시간 역순·범위 초과, 클립 길이 4~15초 밖, 샷에 없는 화자, 알 수 없는 `{자리표시}`, 로드되지 않은 `<Picture N>` 사용, 대사 밖의 한국어 |
| 경고 | 프레이밍에 비해 얼굴이 많은 샷(미디엄 3명, 미디엄 클로즈업 2명, 클로즈업 1명 초과), 클립당 화자 3명 이상, 샷 길이에 비해 긴 대사, 7,000자 초과 |
| 참고 | 얼굴이 3칸 미만이라 옷·머리로만 구분되는 샷, 로드됐지만 화면에 없는 인물, 공식 권장(350~500단어)보다 짧은 묘사 |

**`--llm`**
- llama.cpp 서버(예: Swift 1.5, 포트 5678)에 공식 가이드와 초안을 보내 `detailed_description`만 늘립니다.
- 결과에서 라벨, `(Sx)`, 대사, `[Shot N]` 시간 중 하나라도 바뀌면 한 번 다시 요청하고, 그래도 안 되면 템플릿 문장을 그대로 씁니다.
- 공식 가이드(`ref-en.txt`)는 라이선스 때문에 저장소에 넣지 않았습니다. 실행할 때 GitHub에서 받아 `out/.cache`에 저장합니다. `--guide`로 로컬 파일을 지정할 수도 있습니다.

## 3. 얼굴 일관성 검사

```
python face_check.py cast   --cast examples/cast.yaml
python face_check.py videos --cast examples/cast.yaml --scene examples/S01_diner.yaml --in renders --out out/face
```

**`cast`**
- 인물끼리 얼굴이 얼마나 닮았는지 보여 줍니다.
- 0.45 이상인 쌍은 H3도 이 검사기도 헷갈리니 머리나 옷을 더 다르게 바꾸세요.

**`videos`**
- 파일 이름에 클립 id(예: `S01_C01.mp4`)가 들어 있으면 장면 파일의 샷 시간대별로 등장해야 할 인물과 비교합니다.
- 컷 앞뒤 0.25초는 건너뜁니다.

| 판정 | 뜻 |
|---|---|
| PASS | 등장해야 할 인물이 대부분의 프레임에서 기준 이상으로 일치 |
| CHECK | 일치율이 낮거나 유사도가 기준에 가까움. 눈으로 확인 |
| REDO | 인물이 사라짐(30% 미만), 다른 인물이 나옴, 한 인물의 얼굴이 두 사람에게 복제됨 |
| SMALL | 얼굴이 너무 작아 판정 불가(와이드 샷). 옷과 위치를 눈으로 확인 |
| NOFACE | 인물이 있어야 하는데 얼굴이 하나도 안 잡힘 |

- 결과는 `face_report.md`, `face_report.csv`로 나옵니다.
- CHECK·REDO 샷은 `frames/`에 상자와 이름이 그려진 프레임이 저장됩니다(초록: 맞음, 빨강: 틀림, `2nd E`: E의 얼굴이 한 명 더 있음).

**한계**
- 실사 얼굴 인식 모델이라 애니메이션이나 강한 스타일 캐릭터는 점수가 낮게 나옵니다. 그런 작품은 먼저 `cast`로 참조 얼굴이 잡히는지 확인하세요.
- InsightFace `buffalo_l` 가중치는 비상업 연구용 라이선스입니다. 상업 제작에 점수를 쓰려면 라이선스를 확인하세요.

## 시험 결과 (클라우드에서 확인한 것)

- **프롬프트 생성기:** 테스트 22개가 통과했습니다.
  - 예제 식당 장면 3클립이 오류 없이 만들어졌습니다.
  - 가짜 LLM 서버로 두 경우를 확인했습니다. 규칙을 지킨 확장은 채택되고, 라벨을 망가뜨린 응답은 두 번 거절 후 원래 템플릿으로 돌아갑니다.
- **얼굴 검사:** 테스트 11개가 통과했습니다.
  - 실제 InsightFace 모델로 6인 단체 사진에서 만든 합성 영상 4개를 판정했습니다.

| 합성 영상 | 결과 |
|---|---|
| 6인 원본 | PASS, 6명 모두 100% (유사도 0.89~0.94) |
| C 얼굴을 E 얼굴로 바꿈 | REDO: C 사라짐, E 얼굴 복제 |
| A 클로즈업 → B 클로즈업 | 두 샷 모두 PASS |
| B 자리에 D가 나옴 | REDO: B 사라짐, D 등장 |

실제 H3 렌더로는 아직 확인하지 못했습니다. 그 시험이 `GLM_TASK_H3.md`입니다.
