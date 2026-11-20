# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 9 · 구슬을 나누는 경우의 수
# 문제: 서로 다른 구슬 balls개 중 share개를 고르는 경우의 수 (조합 nCr). balls ≤ 30.
# Spyder: F5 전체 실행

# %% 정답 1: 공식 그대로  n! / ((n-r)! × r!)
import math

def solution(balls, share):
    answer = math.factorial(balls) // (math.factorial(balls - share) * math.factorial(share))
    return answer

# %% 정답 2: 파이썬에 조합 함수가 있음
def solution2(balls, share):
    return math.comb(balls, share)

# %% 확인
print(solution(3, 2), solution2(3, 2))      # 3   (구슬 a,b,c 중 2개: ab, ac, bc)
print(solution(5, 3), solution2(5, 3))      # 10  (5×4×3×2×1 / (2×1 × 3×2×1) = 120 / 12)
print(solution(30, 15))                     # 155117520

# %% 포인트
# - / 대신 //: 결과가 정수여야 해서 (/ 는 항상 소수로 나옴)
# - 통계학과 기본: 이항분포 확률 nCr p^r (1-p)^(n-r) 의 nCr
