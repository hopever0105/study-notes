# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 11 · 팩토리얼
# 문제: i! ≤ n 을 만족하는 가장 큰 정수 i
# Spyder: F5 전체 실행

# %% 정답
def solution(n):
    i = 1
    fact = 1                       # 1! = 1
    while fact * (i + 1) <= n:     # 다음 팩토리얼이 n 이하인 동안 계속
        i = i + 1
        fact = fact * i            # i! = (i-1)! × i
    return i

# %% 확인
print(solution(3628800))   # 10  (10! = 3628800)
print(solution(7))         # 3   (3! = 6 ≤ 7 < 4! = 24)

# %% 포인트
# - 몇 번 돌지 모를 때는 while (if는 한 번만 검사)
