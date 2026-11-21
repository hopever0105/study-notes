# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 16 · 가장 큰 수 찾기
# 문제: 정수 배열 array에서 가장 큰 수와 그 인덱스를 [값, 인덱스]로 (같은 수는 없음)
# Spyder: F5 전체 실행

# %% 정답
def solution(array):
    big = max(array)              # 가장 큰 값
    idx = array.index(big)        # 그 값이 몇 번째 칸에 있는지
    return [big, idx]

# %% 정답 2: 반복문으로 직접 찾기
def solution2(array):
    big = array[0]                # 첫 칸을 일단 최댓값으로
    idx = 0
    for i in range(1, len(array)):
        if array[i] > big:        # 더 큰 값이 나오면 갈아끼움
            big = array[i]
            idx = i
    return [big, idx]

# %% 확인
print(solution([1, 8, 3]), solution2([1, 8, 3]))             # [8, 1]
print(solution([9, 10, 11, 8]), solution2([9, 10, 11, 8]))   # [11, 2]

# %% 포인트
# - 리스트.index(값) : 그 값이 처음 나오는 인덱스
# - 정답 2는 '지금까지 최댓값'을 들고 다니는 패턴 → 연속 상승 최장 길이 문제와 같은 틀
