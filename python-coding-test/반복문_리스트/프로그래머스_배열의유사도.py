# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 16 · 배열의 유사도
# 문제: 문자열 배열 s1, s2에 둘 다 들어 있는 원소의 개수 (각 배열 안에 중복 없음)
# Spyder: F5 전체 실행

# %% 정답
def solution(s1, s2):
    answer = 0
    for x in s1:              # s1 원소를 하나씩
        if x in s2:           # s2에도 있으면
            answer = answer + 1
    return answer

# %% 정답 2: 집합(set)의 교집합
def solution2(s1, s2):
    return len(set(s1) & set(s2))     # & = 둘 다 있는 것만

# %% 확인
print(solution(['a', 'b', 'c'], ['com', 'b', 'd', 'p', 'c']),
      solution2(['a', 'b', 'c'], ['com', 'b', 'd', 'p', 'c']))   # 2
print(solution(['n', 'omg'], ['m', 'dot']))                      # 0

# %% 포인트
# - x in 리스트 : 들어 있으면 True
# - set(리스트) & set(리스트) : 공통 원소만 남는 집합 → len으로 개수
