# 작업 지시서: 빛 번짐 — B 설정으로 한 번 렌더 (실행 담당용)

A(지금 설정) 결과는 이미 있다. **B 설정으로 같은 컷을 한 번만** 렌더해서, A 결과 옆에 놓고 사용자에게 보여 준다. 여러 칸 비교는 하지 않는다.

## 규칙
1. 주관 세션의 굽기가 끝나 레인이 빈 뒤, 사용자가 "해도 된다"고 하면 시작한다.
2. 원본 워크플로와 기본 설정은 바꾸지 않는다. B는 그 렌더에만 적용한다.
3. 렌더 결과는 올리지 않는다.

## 할 일
1. 빛이 가장 심하게 샌 A 클립 하나를 고른다. 같은 프롬프트, 같은 시드, 같은 참조를 쓴다.
2. B 설정으로 한 번 렌더한다. B는 주관 세션이 정한 설정이다(4스텝 turbo 쪽). 렌더 시간을 적는다.
3. A와 B를 나란히 사용자에게 보여 준다. 판정은 사용자가 눈으로 한다.
4. 숫자도 원하면 아래 명령을 1분 정도 돌린다. 빛이 날아간 픽셀과 번진 픽셀의 비율을 A와 B로 비교한다.

```powershell
$R = 'C:\Users\Administrator\Desktop\film_assistant\javisfilm'
$Py = "$R\chat-upgrade\.venv\Scripts\python.exe"
& $Py -m pip install -q pillow
& $Py "$R\ab-compare\abcompare.py" frames --out 'D:\ab\lightleak\compare' --arm 'A=<A 클립 경로>' --arm 'B=<B 클립 경로>' --count 6
```

## B로도 빛이 새면
다음 용의자는 프롬프트의 가사 "lights come on"이다. 텍스트 인코더는 가사와 연출 지시를 구분하지 못한다. 그 한 줄만 빛과 무관한 가사로 바꿔 한 번 더 렌더해 본다.
