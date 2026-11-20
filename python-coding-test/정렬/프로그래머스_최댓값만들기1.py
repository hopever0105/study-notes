# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 11 · 최댓값 만들기 (1)
# 문제: 자연수 리스트 numbers에서 두 원소를 곱해 만들 수 있는 최댓값
# Spyder: F5 전체 실행

# %% 정답
def solution(numbers):
    s = sorted(numbers, reverse=True)      # 큰 순서로 정렬
    answer = s[0] * s[1]                   # 제일 큰 두 개 곱하기
    return answer

# %% 확인
print(solution([1, 2, 3, 4, 5]))           # 20
print(solution([0, 31, 24, 10, 1, 9]))     # 744

# %% 포인트
# - 전부 0 이상이라 큰 두 개 곱이 최대 (음수가 섞이면 '가장 작은 두 개 곱'도 따져야 함)
