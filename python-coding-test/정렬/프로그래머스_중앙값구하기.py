# -*- coding: utf-8 -*-
# 프로그래머스 코딩테스트 입문 Day 3 - 중앙값 구하기
# 요약: 길이가 홀수인 정수 리스트를 크기순으로 세웠을 때 가운데 값을 돌려준다.
# 계산량: 정렬 n×log n → 100만 개여도 약 2,000만 번

# %% 방법 1: median 함수 사용
import statistics

def solution(array):
    return statistics.median(array)

print(solution([1, 2, 7, 10, 11]))   # 7
print(solution([9, -1, 0]))          # 0

# %% 방법 2: 직접 계산 
def solution(array):
    a = sorted(array)          # [1, 2, 7, 10, 11]
    return a[len(a) // 2]      # 길이 5 → 5 // 2 = 2 → a[2] = 7
