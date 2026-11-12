# -*- coding: utf-8 -*-
# 문제: 종가 리스트에서 큰 값 3개 (원래 리스트 순서는 그대로 → sort 말고 sorted)

# %% 풀이
def top3(closes):
    s = sorted(closes, reverse=True)   # 큰 순서 '새 리스트' (closes는 안 바뀜)
    return s[:3]                       # 앞에서 3개

# %% 확인
c = [70000, 72000, 69000, 75000, 71000]
print(top3(c))                   # [75000, 72000, 71000]
print(c)                         # 원래 순서 그대로
print(top3([500, 500, 300, 100]))  # [500, 500, 300]
