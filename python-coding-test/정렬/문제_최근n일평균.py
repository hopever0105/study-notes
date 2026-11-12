# -*- coding: utf-8 -*-
# 문제: 날짜순 종가 리스트에서 마지막 n개 평균 (뒤에서 자르기 = 음수 슬라이싱)

# %% 풀이
def recent_mean(closes, n):
    last = closes[-n:]          # 뒤에서 n개. n=2면 [-2:] → 마지막 2개
    return sum(last) / n        # / 는 항상 소수 → 125.0

# %% 확인
print(recent_mean([100, 110, 120, 130], 2))  # 125.0
print(recent_mean([100, 110, 120, 130], 4))  # 115.0
print(recent_mean([50], 1))                  # 50.0
