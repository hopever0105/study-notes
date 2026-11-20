# -*- coding: utf-8 -*-
# 프로그래머스 입문 · 짝수의 합
# 문제: 1 이상 n 이하의 짝수를 모두 더한 값 반환
# Spyder: F5 전체 실행

# %%
def solution(n):
    answer = 0
    for i in range(1, n + 1):
        if i % 2 == 0:
            answer = answer + i
    return answer

# %%
print(solution(10))    # 2+4+6+8+10 = 30
print(solution(4))     # 2+4 = 6
