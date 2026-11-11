# -*- coding: utf-8 -*-
# 조건문 문법: if·elif·else 순서, 비교 기호, and·or, % 나머지, return
# Spyder에서 F5로 실행

# %% 1. 기본 모양: 위에서부터 검사하고, 처음 참인 칸 하나만 실행한다
per = 8.5    # 주가수익비율(PER)

if per < 10:            # 8.5 < 10 → 참 → 여기만 실행하고 아래는 건너뜀
    print("저평가")
elif per < 20:          # 위가 참이었으므로 검사조차 안 함
    print("보통")
else:                   # else 뒤에는 조건을 쓰지 않는다! 그냥 else:
    print("고평가")
# 출력: 저평가

# %% 2. 순서가 중요한 이유: 숫자로 확인
volume = 1_500_000   # 거래량 150만 주

# (잘못된 순서) 작은 기준을 먼저 쓰면
if volume > 100_000:        # 150만 > 10만 → 참 → 여기서 끝남
    print("보통 거래")
elif volume > 1_000_000:    # 150만 > 100만도 참이지만 여기까지 오지 못함
    print("거래 폭발")
# 출력: 보통 거래  ← 틀림

# (올바른 순서) 큰 기준부터 쓰면
if volume > 1_000_000:      # 참 → "거래 폭발"
    print("거래 폭발")
elif volume > 100_000:
    print("보통 거래")
else:
    print("거래 적음")
# 출력: 거래 폭발

# %% 3. 비교 기호: 같다는 == (등호 두 개). 등호 하나(=)는 '값 넣기'
price = 50000
print(price == 50000)   # True  (같다)
print(price != 50000)   # False (다르다)
print(price >= 50000)   # True  (이상: 같아도 참)
print(price > 50000)    # False (초과: 같으면 거짓)

# %% 4. and / or: 조건 두 개를 묶기
per = 8
pbr = 1.5
if per < 10 and pbr < 1:     # 둘 다 참이어야 참 → True and False → False
    print("둘 다 싸다")
if per < 10 or pbr < 1:      # 하나만 참이면 참 → True or False → True
    print("하나는 싸다")
# 출력: 하나는 싸다

# %% 5. % (나머지): 짝수·홀수, 딱 나누어떨어지는지 판단
print(10 % 3)   # 1   (10 = 3×3 + 1)
print(12 % 4)   # 0   (나누어떨어짐)
lot = 7         # 주문 수량
if lot % 2 == 0:
    print("짝수")
else:
    print("홀수")
# 출력: 홀수

# %% 6. return과 함께 쓰기: return을 만나면 함수가 그 자리에서 바로 끝난다
def grade(score):
    if score >= 90:
        return "A"      # 95가 들어오면 여기서 끝, 아래는 실행 안 됨
    elif score >= 80:
        return "B"
    else:
        return "C"

print(grade(95))   # A
print(grade(80))   # B  (80 >= 80 참: '이상'이니까)
print(grade(79))   # C