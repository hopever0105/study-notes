# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 13 · 배열 원소의 길이
# 문제: 문자열 리스트 strlist → 각 원소의 길이 리스트
# Spyder: F5 전체 실행

# %% 정답
def solution(strlist):
    answer = []
    for word in strlist:
        answer.append(len(word))
    return answer

# %% 확인
print(solution(['We', 'are', 'the', 'world!']))     # [2, 3, 3, 6]
print(solution(['I', 'Love', 'Programmers.']))      # [1, 4, 12]
