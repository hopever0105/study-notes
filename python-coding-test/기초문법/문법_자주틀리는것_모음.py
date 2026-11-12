# -*- coding: utf-8 -*-
# 자주 틀리는 것 모음 (11/9 ~ 11/12 채점에서 나온 실수만)
# Spyder: 구역(# %%)마다 Ctrl+Enter로 하나씩 실행해서 결과 확인

# %% 1. for 뒤의 이름은 '내가 정하는 이름표'. 매 바퀴 원소 하나가 담김
#  - 리스트를 돌리면 → 원소 하나
#  - 문자열을 돌리면 → 글자 하나
for x in [10, 20, 30]:
    print("이번 바퀴 x =", x)      # 10 → 20 → 30
for x in "abc":
    print("이번 바퀴 x =", x)      # a → b → c   (글자 하나씩)
for 아무이름 in "abc":
    print(아무이름)                 # 이름은 아무거나, 아래에서 같은 이름으로 쓰면 됨

# %% 2. 무엇을 돌리는지: 함수 입력 이름을 그대로 돌린다
def count_up(prices):
    cnt = 0
    for p in prices:               # ✗ for p in []   → 빈 리스트라 한 바퀴도 안 돎
        if p > 0:
            cnt = cnt + 1
    return cnt
print(count_up([1, -2, 3]))        # 2

# %% 3. 문자열을 '단어' 단위로 돌리려면 split 먼저 (split은 점 찍어 쓰는 메서드)
s = "매수,매도,매수"
for x in s:                        # ✗ 글자 단위: 매 / 수 / , / 매 ...
    pass
for x in s.split(","):             # ○ 단어 단위: 매수 / 매도 / 매수
    print(x)
# ✗ split(s, ",")  → split은 혼자 못 씀. 반드시 s.split(",")
# ✗ s.split("")    → 빈 칸으로는 못 쪼갬. 글자 하나씩이면 그냥 for x in s

# %% 4. 함수는 반드시 def 로 만들고, return 은 for 가 다 끝난 뒤 (for와 같은 높이)
def total(nums):
    s = 0
    for x in nums:
        s = s + x
        # return s  ← ✗ 여기 두면 첫 바퀴에서 바로 끝남
    return s                       # ○ for와 같은 높이 = 반복 다 끝나고 돌려줌
print(total([1, 2, 3]))            # 6
# ✗ total(nums) = s   → 함수를 이렇게 만들 수 없음

# %% 5. 곱하기: 리스트 × 숫자, 문자열 × 숫자 = '통째로 반복'
print([1, 2] * 2)                  # [1, 2, 1, 2]   원소에 2가 곱해지는 게 아님
print("he" * 3)                    # hehehe          글자마다가 아니라 통째로
# 원소마다 / 글자마다 하려면 for로 하나씩
out = []
for x in [1, 2]:
    out.append(x * 2)
print(out)                         # [2, 4]
word = ""
for ch in "he":
    word = word + ch * 3
print(word)                        # hhheee

# %% 6. 딕셔너리로 개수 세기 (틀: 빈 딕셔너리 → for → 있으면 +1, 없으면 1)
count = {}
for x in ["매수", "매도", "매수"]:
    if x in count:
        count[x] = count[x] + 1    # ✗ count[x+1] → 키에 1을 더함 (괄호 위치)
    else:
        count[x] = 1
print(count)                       # {'매수': 2, '매도': 1}

# %% 7. 값 넣는 방향: = 는 '오른쪽 값을 왼쪽에 넣기'
answer = 0
i = 5
answer = i                         # ○ answer에 5를 넣음
# i = answer  ← ✗ 거꾸로 하면 i가 0이 됨
print(answer)

# %% 8. if는 한 번만 검사, while은 조건 맞을 때까지 반복
i = 1
while 6 * i % 4 != 0:              # 6*i가 4로 나눠떨어질 때까지 i 늘리기
    i = i + 1
print(i)                           # 2  (6*2=12)

# %% 9. else 뒤엔 조건 없음. 조건이 필요하면 elif
x = 3
if x > 5:
    print("크다")
elif x == 5:
    print("같다")
else:                              # ✗ else x < 5:
    print("작다")

# %% 10. 문자열 값은 따옴표 한 겹
a = "급등"                          # ○ 급등
b = '"급등"'                        # ✗ "급등"  (따옴표 기호까지 글자로 들어감)
print(a, b)

# %% 11. 함수 괄호엔 재료를 넣는다
import math
print(math.gcd(12, 18))            # 6     ✗ math.gcd() → 재료 없음

# %% 12. range는 끝 숫자를 안 넣음 → n까지면 n + 1
for i in range(1, 3 + 1):          # 1, 2, 3
    print("*" * i)

# %% 13. return 문제 vs print 문제
# def solution(...): ... return answer   → 돌려준 값이 답
# n = int(input()) ... print(...)        → 화면에 찍힌 게 답 (input은 문자열이라 int로 바꿈)
