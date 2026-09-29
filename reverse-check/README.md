# reverse-check: 역프롬프트 검증

잘 만든 예시 영상(예: 강좌 중간에 나오는 결과물)을 샷으로 자르고, **프로젝트의 역프롬프트 로직**으로 샷마다 프롬프트를 만든 뒤, 그 프롬프트가 맞는지 확인하는 도구입니다.

## 확인하는 방법

1. **화면과 맞는지:** 비전 모델(llama-server + mmproj)에 샷의 앞·가운데·뒤 프레임 3장과 프롬프트를 함께 보여 줍니다. 여섯 가지를 예/아니오로 묻고 확률을 받습니다.
   - 인물·대상, 행동, 카메라, 장소, 조명·색감, 화풍
   - 추가로 "화면에 없는 것을 지어냈는가"도 묻습니다.
2. **실제 프롬프트와 맞는지:** 영상 설명이나 강좌 화면에 실제로 쓴 프롬프트가 나오면 `truth.csv`에 적습니다. 그러면 여섯 가지마다 "두 프롬프트가 같은 말을 하는가"를 묻습니다. 가장 확실한 검증입니다.
3. **비교 기준:** 같은 샷을 비전 모델이 직접 쓴 프롬프트(`--vlm`)와 나란히 점수를 매깁니다. 그래서 프로젝트 로직이 어느 항목에서 약한지 보입니다.

한계: 1번은 채점도 같은 계열의 비전 모델이 합니다. 그래서 자기 말투에 후할 수 있습니다. 2번이 있으면 그쪽을 더 믿습니다. 다음 단계는 프롬프트로 다시 만들어서 원본과 비교하는 왕복 검증입니다.

## 쓰는 법

```powershell
python revcheck.py shots   src.mp4 --work W --start 0 --end 8:30     # 샷 자르기 → W\index.html 로 눈으로 확인
python revcheck.py classify --work W                                  # 예시 영상 / UI 녹화 / 설명하는 사람 / 제목 화면
python revcheck.py prompt   --work W --only showcase --cmd "python local\project_rp.py {frames}"   # 프로젝트 로직
python revcheck.py prompt   --work W --only showcase --vlm            # 비교 기준
python revcheck.py score    --work W --only showcase
python revcheck.py report   --work W --only showcase --offset 7:30 --with-prompts --out reports\REVCHECK.md
```

- `--cmd` 자리 표시: `{frame}` 가운데 프레임, `{frames}` 프레임 3장, `{clip}` 샷 영상(최대 10초), `{shot}` 샷 번호, `{out}` 결과 파일. 결과는 표준 출력으로 받거나, `{out}`을 쓰면 그 파일에서 읽습니다.
- 예시 영상이 화면 일부(창 안)에서만 나오면 `shots --crop w:h:x:y`로 그 부분만 잘라 씁니다.
- 영상, 프레임, 클립은 `work\`에만 두고 올리지 않습니다(`.gitignore`). 올리는 것은 점수 보고서뿐입니다.
- 판단 호출은 `chat-upgrade/chatup`의 Jev식 판단을 씁니다. 필요한 것은 표준 라이브러리와 ffmpeg입니다.
