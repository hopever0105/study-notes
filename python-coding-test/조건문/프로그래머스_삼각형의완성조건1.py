# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 13 · 삼각형의 완성조건 (1)
# 문제: 세 변 길이 sides. 가장 긴 변 < 나머지 두 변의 합이면 1, 아니면 2
# Spyder: F5 전체 실행

# %% 정답
def solution(sides):
    longest = max(sides)
    others = sum(sides) - longest        # 나머지 두 변의 합
    if longest < others:
        return 1
    else:
        return 2

# %% 확인
print(solution([1, 2, 3]))        # 2  (3 < 3 아님)
print(solution([3, 6, 2]))        # 2
print(solution([199, 72, 222]))   # 1
