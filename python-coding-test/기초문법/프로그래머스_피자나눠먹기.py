# -*- coding: utf-8 -*-
# 프로그래머스 코딩테스트 입문 Day 4 - 피자 나눠 먹기 (2)·(3)
# 쓰는 문법: 올림, while 반복, % 나머지 (문법_올림_최소공배수_평균.py)

# %% 피자 나눠 먹기 (2)
# 요약: 한 판 6조각. n명이 모두 같은 수의 조각을 남김없이 먹으려면 최소 몇 판?
#       → 6 × 판 수가 n으로 나누어떨어질 때까지 판 수를 늘린다.
def solution(n):
    i = 1
    while 6 * i % n != 0:   # 나누어떨어지지 않는 동안
        i = i + 1           # 판 수를 하나씩 늘림
    return i

print(solution(6))    # 1
print(solution(10))   # 5  (6, 12, 18, 24, 30 → 30에서 10으로 나누어떨어짐)
print(solution(4))    # 2

# 틀렸던 것
#   if 6*i % n != 0:   ✗ if는 한 번만 검사 → 될 때까지 반복은 while
#   i = answer         ✗ '='는 오른쪽 값을 왼쪽에 넣음. answer는 만든 적 없음 → return i
#   else: 아래 줄 들여쓰기 없음 → IndentationError

# %% 피자 나눠 먹기 (3)
# 요약: 한 판 slice조각(2~10). n명이 최소 한 조각씩 먹으려면 최소 몇 판? → n ÷ slice 올림
def solution(slice, n):
    return (n + slice - 1) // slice    # math 없이 올림

print(solution(7, 10))   # 2
print(solution(4, 12))   # 3

# 같은 뜻
import math
def solution(slice, n):
    return math.ceil(n / slice)
