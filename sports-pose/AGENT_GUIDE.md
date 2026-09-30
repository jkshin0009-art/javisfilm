# 프롬프트 에이전트 지침: 스포츠 자세 자산 쓰는 법

이 지침은 장면 프롬프트를 쓰는 에이전트용입니다. 프로그램이 자동으로 자산을 넘겨줄 때(film_assistant의 `sportslook.py` 연결)는 같은 규칙이 영어 지시문(`guide`)으로 프롬프트 요청에 붙습니다. 콘티에 스포츠 동작이 나오면 자세를 직접 지어내지 말고, **자산을 찾아 그 몸 동작을 그대로 따릅니다.** 자산의 글과 OpenPose 이미지는 같은 3D 뼈대에서 나왔기 때문에, 둘 다 쓰면 서로 어긋나지 않습니다.

## 1. 자산 찾기

```
python sportspose.py find "배구 스파이크 타점"
python sportspose.py find "goalkeeper dive" --full     (파일 경로까지)
```

- 한국어와 영어 이름, 코드(`#VOLLEYBALL_SPIKE_CONTACT`)로 찾을 수 있습니다.
- 목록은 `library/index.json`에 있고, 사람이 볼 목록은 `library/CATALOG.md`입니다.
- 맞는 자산이 없으면 비슷한 자산을 억지로 쓰지 말고 "자산 없음"이라고 보고합니다. 새 자산은 README의 "자산 추가"를 따라 만듭니다.

## 2. 카메라 고르기

`prompt.md`의 `4. CINEMATIC_CAMERA`에 카메라가 2~3개 있습니다.

- 카메라마다 `openpose_<카메라>.png` 한 장이 있습니다. **프롬프트의 카메라 문구와 컨트롤 이미지는 같은 카메라의 것을 씁니다.**
- 생성 해상도는 컨트롤 이미지 크기(예: 896×1152, 1344×768)와 같게 합니다.
- 콘티가 목록에 없는 카메라를 요구하면 자산 JSON의 `cameras`에 한 줄을 더하고 `python sportspose.py build <코드>`로 다시 만듭니다. 이미지와 글이 함께 바뀝니다.

## 3. 프롬프트 채우기

`prompt.md`의 **Prompt** 블록을 복사해 두 자리만 채웁니다.

- `{SUBJECT}`: 인물 묘사. h3-multicast의 캐스트 `look`을 그대로 넣습니다. 예: `a woman in her late twenties with a short silver bob, wearing a red volleyball jersey`
- `{SETTING}`: 장소와 빛. 예: `Indoor arena, evening match, warm spotlights, packed stands`
- `{PARTNER_B}`: 두 사람 자산(권투, 태권도, 유도, 레슬링)에만 있습니다. 상대 선수의 외모를 캐스트 `look`으로 넣습니다.
  - 예: `a tall man in his thirties with a shaved head, wearing a blue judogi`
  - 두 사람의 유니폼 색은 규칙이 정한 대로 다르게 합니다. 유도는 흰색과 파란색, 레슬링·태권도·권투는 빨간색과 파란색입니다.

반드시 지킬 것:

- **몸 동작 문장은 고치지 않습니다.** 각도, 거리, 좌우, 손 모양, 발 접지는 검사를 통과한 값입니다. 다른 말로 바꾸면 뼈대 이미지와 어긋납니다.
- 자세를 바꾸는 말을 덧붙이지 않습니다. 예: "dynamic pose", "arms raised" 같은 말을 추가하지 않습니다.
- 자산은 **오른손잡이, 오른발잡이** 기준입니다. 왼손잡이 장면은 아직 좌우 반전 자산이 없으니 보고합니다. 권투·태권도·레슬링은 왼발이 앞인 자세(오소독스)입니다.
- **두 사람 장면:** `2. ANATOMICAL_BONES`의 `- B (...)` 줄이 상대 선수의 위치와 자세입니다. 이 줄도 고치지 않습니다. 잡는 손(깃, 소매, 무릎 뒤)과 맞는 부위(턱, 몸통 보호대)는 검사를 통과한 위치입니다.
- **수영:** 높이는 수면 기준으로 적혀 있습니다(예: "fingertips 0.25 m below the water surface"). 물 위와 물 아래가 나뉘는 장면이니 카메라 문구(수중, 수면 위)를 바꾸지 않습니다.
- 더 자세한 지시가 필요하면 5단 블록(`## Asset (5 sections)`)에서 해당 줄을 그대로 가져다 붙입니다.
- **Negative prompt:** SDXL 계열에만 넣습니다. Flux dev는 negative를 쓰지 않으므로, 본문에 이미 올바른 해부 구조가 적혀 있는 것으로 충분합니다.

### 공식 경기 규칙 지키기

- `prompt.md`의 **Official game rules** 표를 확인합니다. 자산 자세는 이 조항들을 모두 통과한 상태입니다.
  - 예: 네트에 닿지 않음, 공을 자기 코트에서 때림, 축발이 투수판에 닿음.
- `3. OBJECT_INTERACTION`의 `Legal under the … rules:` 줄은 그대로 둡니다.
- 여러 명이 나오는 장면(경기 전체, 관중석에서 본 장면)은 `python sportspose.py rules <종목>`의 **Scene** 목록을 따릅니다.
  - 예: 배구는 한 팀 6명에 리베로 1명(다른 색 유니폼), 축구는 골키퍼 유니폼 색이 달라야 하고 장신구를 쓰지 않습니다. 야구는 타자와 주자가 헬멧을 씁니다.
  - 격투기와 수영의 예: 권투는 마우스피스, 태권도는 전자 몸통 보호대와 헤드기어(빨강·파랑), 유도는 흰색·파란색 도복, 레슬링은 빨강·파랑 싱글렛, 수영은 무릎 위까지 오는 수영복입니다.
- 반칙 장면이 필요한 연출(일부러 반칙하는 장면)이 아니라면, 규칙 표의 반칙 모습이 들어가지 않게 합니다. negative에 이미 들어 있습니다.

## 4. ComfyUI 연결 (정지 이미지)

1. `Load Image` 노드로 `openpose_<카메라>.png`를 불러옵니다. 이미 뼈대 그림이므로 전처리기(DWPose 등)를 거치지 않습니다. 두 사람 자산은 한 장에 두 뼈대가 모두 들어 있습니다.
2. `Apply ControlNet`에 연결합니다. OpenPose ControlNet이나 Union 계열을 openpose 모드로 씁니다.
3. 강도와 적용 구간의 출발점:

   | 상황 | strength | end_percent |
   |---|---|---|
   | 기본 | 0.65~0.8 | 0.6~0.8 |
   | 손이 뭉개질 때 | 0.8~0.9 | 0.8~0.9 |

   손이 뭉개지면 강도와 구간을 올리는 것 외에 손만 다시 그리는 방법도 있습니다.
4. 빈 latent의 크기는 컨트롤 이미지 크기와 같게 합니다.
5. 필요하면 편집기에서 `openpose_<카메라>.json`을 불러와 손봅니다. 형식은 `people / pose_keypoints_2d / hand_*_keypoints_2d`, 픽셀 좌표입니다.

## 5. 영상 (MiniMax H3)

- 한 동작의 단계를 순서대로 뽑습니다.

  ```
  python sportspose.py sequence VOLLEYBALL_SPIKE
  ```

  출력 맨 아래의 한 문단("First: … Then: …")을 H3 `detailed_description`에 넣고, `{SUBJECT}` 자리는 `<Subject N>` 표기로 바꿉니다.
- 몸 동작이 정확해야 하는 컷은 먼저 4번 방식으로 핵심 단계(예: 타점)의 정지 이미지를 만듭니다. 그 이미지를 인물 참조나 시작 장면으로 넣으면 영상이 그 자세에서 벗어나지 않습니다.
- 동작 순서: `VOLLEYBALL_SPIKE`, `SOCCER_INSTEP_KICK`, `BASEBALL_PITCH`, `BASEBALL_SWING`, `BASKETBALL_JUMP_SHOT`, `TENNIS_SERVE`, `FISHING_CAST`, `BOXING_ONE_TWO`, `SWIMMING_RACE`, `JUDO_SEOI_NAGE_THROW` (전체는 `library/CATALOG.md`).

## 6. 결과 확인

- `prompt.md`의 **Negative prompt** 목록은 그 동작에서 이미지 모델이 자주 틀리는 것들입니다. 결과 그림에서 이 항목부터 봅니다(손가락 수, 공과 손 겹침, 뜬 발, 좌우 바뀐 다리).
- `preview.png`의 세 방향 뼈대가 기준 자세입니다. 결과 그림과 나란히 놓고 비교합니다.
