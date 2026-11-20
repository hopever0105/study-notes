# -*- coding: utf-8 -*-
# 프로그래머스 입문 · 순서쌍의 개수
# 문제: 자연수 n에 대해 a × b = n을 만족하는 순서쌍 (a, b)의 개수 반환
# Spyder: F5 전체 실행

# %%
def solution(n):
    count = 0
    for a in range(1, n + 1):
        if n % a == 0:          # a가 n의 약수이면 b = n // a 가 정해짐
            count = count + 1
    return count

# %%
print(solution(20))    # 6
print(solution(7))     # 2
