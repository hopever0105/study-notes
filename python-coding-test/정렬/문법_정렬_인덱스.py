# -*- coding: utf-8 -*-
# 문법: sorted, len, // 몫, 0부터 세는 인덱스
# Spyder에서 F5로 실행

# %% 1. sorted(): 작은 것부터 줄 세운 '새 리스트'를 돌려줌 (원래 리스트는 그대로)
prices = [300, 100, 500, 200]
a = sorted(prices)
print(a)        # [100, 200, 300, 500]
print(prices)   # [300, 100, 500, 200]  ← 원래 것은 안 바뀜

# 참고: prices.sort() 는 원래 리스트를 직접 바꾸고, 돌려주는 값은 None
# b = prices.sort()  → b는 None  ← 자주 하는 실수

# %% 2. len(): 원소 개수
print(len(a))   # 4

# %% 3. // (몫): 나눗셈에서 소수점 아래를 버림
print(7 // 2)   # 3   (7 / 2 = 3.5 → 3)
print(9 // 2)   # 4   (9 / 2 = 4.5 → 4)
print(7 / 2)    # 3.5 ← / 는 소수가 나와서 번호로 쓸 수 없음

# %% 4. 인덱스(번호)는 0부터 센다
days = ["월", "화", "수", "목", "금"]
#        0     1     2     3     4
print(days[2])   # 수
print(days[len(days) // 2])   # len=5 → 5 // 2 = 2 → days[2] = 수
