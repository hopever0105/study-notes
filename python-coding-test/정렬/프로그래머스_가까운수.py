# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 14 · 가까운 수
# 문제: 정수 리스트 array에서 n과 가장 가까운 수. 거리가 같으면 더 작은 수
# Spyder: F5 전체 실행

# %% 정답
def solution(array, n):
    s = sorted(array)                       # 작은 순서로 먼저 정렬 → 거리가 같으면 작은 수가 먼저 나옴
    answer = s[0]
    for x in s:
        if abs(x - n) < abs(answer - n):    # 더 가까우면 바꾸기 (같으면 안 바꿈 → 작은 수 유지)
            answer = x
    return answer

# %% 확인
print(solution([3, 10, 28], 20))     # 28
print(solution([10, 11, 12], 13))    # 12
print(solution([4, 6], 5))           # 4  (둘 다 거리 1 → 작은 4)

# %% 포인트
# - abs(): 절댓값. 거리 = abs(x - n)
