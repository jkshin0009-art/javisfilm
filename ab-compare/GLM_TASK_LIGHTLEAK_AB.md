# 작업 지시서: "빛이 새고 엉망" 원인 확정 — 단일 변수 A/B (실행 담당용)

## 배경

앞선 감사(읽기 전용)의 결론은 이렇다.
- 프롬프트와 참조 이미지(앵커, 얼굴)는 깨끗하다.
- 강좌(E-eyEj3rMUY)와 우리의 차이는 샘플링 스택이다. 강좌는 4스텝 turbo를 쓰고, 우리는 taomate 3스텝 증류 LoRA ×1.0을 쓴다. 이것이 가장 유력한 용의자다.
- 레버 세 개가 이미 로컬에 있다.

이 문서는 그 결론을 **숫자와 블라인드 비교로 확정**한다. 한 번에 **하나만** 바꾼다.

분석 담당이 결론에 덧붙이는 점이 두 가지 있다.
1. **가사 "lights come on"을 용의자에서 빼면 안 된다.** 텍스트 인코더는 가사와 지시를 구분하지 못한다. 프롬프트에 그 문장이 있으면 "불이 켜진다"는 뜻으로 읽힐 수 있다. 그래서 가사 줄만 바꾼 칸(A3)을 넣는다.
2. **"차이는 샘플링 스택뿐"은 아직 확인되지 않았다.** 스텝, CFG, shift, 샘플러, 스케줄러, 해상도, 프레임 수, fps, LoRA 목록과 강도, 모델 정밀도를 강좌와 한 줄씩 대조해야 확정된다(B1).

## 반드시 지킬 규칙

1. **레인이 비었을 때만:** 주관 세션의 en_v12 굽기가 레인에서 돌고 있다. 끝났는지 확인하고, 사용자(또는 주관 세션)가 "해도 된다"고 한 뒤에만 렌더를 시작한다.
2. **전역 설정은 그대로 둘 것:** 워크플로 원본, 기본 환경변수, 모델 파일을 바꾸지 않는다. 칸마다 워크플로 **사본**을 만들어 쓰고, 환경변수는 그 렌더에만 준다. 끝나면 원래 상태인지 확인한다.
3. **하나만 바꿀 것:** 칸끼리는 아래 표에 적은 한 가지만 다르다. 시드, 프롬프트, 참조, 해상도, 길이는 모두 같게 한다.
4. **올리지 말 것:** 렌더한 영상과 프레임은 올리지 않는다. 올리는 것은 `RESULT.md`와 설정 대조표뿐이다.
5. 셸은 PowerShell 기준이다. 확인 기준을 못 넘으면 멈추고 보고한다.

## B1. 설정 대조표 (렌더 전, 읽기만)

클립 1~4를 만든 워크플로(JSON)와 강좌 설정을 항목별로 적는다. 강좌 쪽 값을 모르면 "확인 못 함"으로 적는다.

| 항목 | 우리 | 강좌 | 같음/다름 |
|---|---|---|---|
| 모델, 정밀도 (Singularity pruned int8 등) | | | |
| 스텝 수 | | | |
| CFG, guidance | | | |
| shift, 샘플러, 스케줄러 | | | |
| 해상도, 프레임 수, fps | | | |
| LoRA 목록과 강도 (노드 9010 포함) | | | |
| 참조 방식 (Ref2V, 앵커, 얼굴) | | | |
| 업스케일, 후처리 | | | |

## B2. 시험할 컷 정하기

- 클립 1~4 중 빛 번짐이 가장 심한 클립 하나를 고른다. 길면 같은 프롬프트로 3~5초만 만든다.
- 시드는 원래 렌더의 시드를 쓴다.
- 그 클립을 만든 **방법**(스크립트, 워크플로, 명령)을 그대로 기록한다. 모든 칸이 이 방법으로 렌더된다.

## B3. 칸 (각각 렌더 1회)

| 칸 | 바꾸는 것 하나 | 확인하려는 것 |
|---|---|---|
| A0 base | 없음 (지금 설정: taomate 3스텝 ×1.0) | 기준 |
| A1 turbo4 | 노드 9010 LoRA를 `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16`으로 바꾸고, 스텝을 저자 권장값(4)으로 맞춤 | 증류 LoRA가 원인인가 |
| A2 turbo4+realism | A1에 더해 `h3-realism-people-t2v-i2v-r2v` ×0.5 | 피부 광택, 번짐이 더 줄어드는가 |
| A3 lyric | A0에서 프롬프트의 "lights come on" 가사 줄만 빛과 무관한 같은 길이의 가사로 바꿈 | 텍스트가 원인인가 |
| (선택) A4 lora-off | `FJ_LORA9010=off`, 스텝은 증류 없는 기본값으로 올림 | 증류 자체의 영향 (느림) |
| (선택) A5 refine | 가장 좋은 칸에 잠재 업스케일러 `minimax_h3_latent_upscaler_3d_fp16` 다듬기 패스 | 마지막 다듬기 효과 |

- 칸마다 결과를 `...\ab\A0_base.mp4`처럼 이름을 붙여 한 폴더(아래 `$AB`)에 모은다.
- 사용한 워크플로 사본도 `A0_base.json`처럼 같은 폴더에 둔다.
- A4는 증류 없이 3스텝으로 돌리면 공정한 비교가 아니다. 반드시 스텝을 올린다.

## B4. 비교

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$Py = "$R\chat-upgrade\.venv\Scripts\python.exe"
$AB = 'D:\ab\lightleak_1'          # B3 결과를 모은 폴더로 바꾼다
& $Py -m pip install -q pillow
git -C $R pull --rebase
& $Py "$R\ab-compare\abcompare.py" frames --out "$AB\compare" `
  --arm "A0_base=$AB\A0_base.mp4" --arm "A1_turbo4=$AB\A1_turbo4.mp4" `
  --arm "A2_turbo4_realism=$AB\A2_turbo4_realism.mp4" --arm "A3_lyric=$AB\A3_lyric.mp4" `
  --count 6 --vlm http://127.0.0.1:5678 --note "same clip and seed; one setting differs per arm"
```

- 렌더하지 않은 칸은 `--arm`에서 뺀다. 5678 모델이 바쁘면 `--vlm`을 빼고 돌린다(숫자와 사람 판정만으로도 된다).
- 확인 기준: 칸마다 `blown`, `glow` 줄이 나오고 `RESULT ... Blind page:` 줄이 나온다.
- **사용자에게 `$AB\compare\blind.html`을 열어 달라고 한다.** 이름이 가려진 A/B/C/D 중에서 줄마다 가장 좋은 것, 전체 1등과 꼴찌를 고르고 `votes.csv`를 내보내면 된다. 실행 담당은 투표가 끝나기 전에 `key.json`을 보여 주지 않는다.

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$Py = "$R\chat-upgrade\.venv\Scripts\python.exe"
$AB = 'D:\ab\lightleak_1'
& $Py "$R\ab-compare\abcompare.py" reveal --out "$AB\compare" --votes "$env:USERPROFILE\Downloads\votes.csv" `
  --report "$R\ab-compare\reports\LIGHTLEAK_AB_1.md"
```

## B5. 판정과 보고

`$R\ab-compare\reports\LIGHTLEAK_AB_1.md` 끝에 아래를 덧붙인다.
- B1 대조표
- B2에서 고른 클립 번호, 길이, 시드, 렌더 방법(명령·워크플로 이름)
- 칸마다 렌더 시간
- 해석. 규칙은 이렇다.
  - A3가 이기면: 원인은 프롬프트 텍스트다. 가사 처리 규칙을 바꿔야 한다.
  - A1이나 A2가 이기면: 원인은 샘플링 스택이다. 이긴 칸의 설정을 주관 세션에 넘긴다.
  - 칸 사이 차이가 작으면: 대조표에서 "다름"으로 나온 다른 항목을 다음 시험 칸으로 적는다.

사용자에게 보여 주고, 허락하면 `ab-compare/reports`만 커밋·push한다. push가 실패하면 보고서 전문을 출력한다. **이긴 설정을 실제 파이프라인에 넣는 일은 주관 세션 몫이다.** 이 문서의 실행 담당은 넣지 않는다.
