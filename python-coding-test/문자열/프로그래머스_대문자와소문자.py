# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 14 · 대문자와 소문자
# 문제: 대문자는 소문자로, 소문자는 대문자로 바꾼 문자열
# Spyder: F5 전체 실행

# %% 정답
def solution(my_string):
    answer = ''
    for ch in my_string:
        if ch.isupper():               # 대문자면
            answer = answer + ch.lower()
        else:
            answer = answer + ch.upper()
    return answer

# %% 정답 2: 파이썬 함수 한 번
def solution2(my_string):
    return my_string.swapcase()

# %% 확인
print(solution('cccCCC'), solution2('cccCCC'))     # CCCccc
print(solution('abCdEfghIJ'))                       # ABcDeFGHij
