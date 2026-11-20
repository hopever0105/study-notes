# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 11 · 주사위의 개수
# 문제: 상자 가로·세로·높이 box=[w, l, h], 주사위 한 변 n → 상자에 들어가는 주사위 최대 개수
# Spyder: F5 전체 실행

# %% 정답
def solution(box, n):
    answer = (box[0] // n) * (box[1] // n) * (box[2] // n)   # 방향마다 몇 개 들어가는지(몫) 곱하기
    return answer

# %% 확인
print(solution([1, 1, 1], 1))      # 1
print(solution([10, 8, 6], 3))     # 12  (3 × 2 × 2)
