# ============================================================
# = 하나와 == 둘의 차이
#   =   : 넣기(대입).  "오른쪽 값을 왼쪽 상자에 넣어라"   → 명령
#   ==  : 같은지 묻기(비교). "왼쪽과 오른쪽이 같나?"      → 질문, 답은 True/False
# ============================================================


# %% ① = 하나: 상자에 값 넣기
price = 100          # price라는 상자에 100을 넣어라
print(price)         # 100
price = 105          # 같은 상자에 105를 다시 넣음 → 100은 사라짐
print(price)         # 105

answer = 0
answer = answer + 1  # 오른쪽(0 + 1 = 1)을 먼저 계산 → 왼쪽 answer에 넣음
print(answer)        # 1


# %% ② == 둘: 같은지 묻기 → True(참) / False(거짓)
print(3 == 3)        # True
print(3 == 5)        # False
print("B" == "S")    # False


# %% ③ if 뒤에는 항상 비교(질문)
p = "B10"
if p[0] == "B":      # "첫 글자가 B인가?" → True
    print("매수")
# if p[0] = "B":     # ← 넣기(=)를 쓰면 SyntaxError


# %% ④ 한 줄에 둘 다 — 오른쪽부터 읽기
num1, num2 = 11, 11
same = (num1 == num2)   # 1) 같은지 물어봄 → True  2) 그 답을 same에 넣음
print(same)             # True


# %% ⑤ 비교 기호 (전부 질문, 답은 True/False)
a, b = 7, 3
print(a == b, a != b, a > b, a < b, a >= b, a <= b)
# False True True False True False

# 외우는 법: =  "넣어라",  ==  "같나?"
