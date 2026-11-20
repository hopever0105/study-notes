# -*- coding: utf-8 -*-
# 프로그래머스 입문 · 외계행성의 나이
# 문제: 나이 age의 각 자리 숫자를 0→a, 1→b, ... 9→j로 바꿔 이어 붙인 문자열 반환
# Spyder: F5 전체 실행

# %%
def solution(age):
    alpha = 'abcdefghij'
    answer = ''
    for ch in str(age):
        answer = answer + alpha[int(ch)]
    return answer

# %%
print(solution(23))     # cd
print(solution(51))     # fb
print(solution(100))    # baa
