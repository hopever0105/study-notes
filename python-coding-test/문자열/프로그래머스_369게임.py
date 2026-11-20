# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 14 · 369게임
# 문제: 정수 order에 들어 있는 3, 6, 9 글자 개수 = 박수 횟수
# Spyder: F5 전체 실행

# %% 정답
def solution(order):
    answer = 0
    for ch in str(order):            # 숫자 → 문자열로 바꿔야 한 글자씩 돌 수 있음
        if ch in '369':
            answer = answer + 1
    return answer

# %% 확인
print(solution(3))          # 1
print(solution(29423))      # 2
