# -*- coding: utf-8 -*-
# 프로그래머스 입문 · 특정 문자 제거하기
# 문제: 문자열 my_string에서 letter에 해당하는 글자를 모두 뺀 문자열을 반환
# Spyder: F5 전체 실행

# %%
def solution(my_string, letter):
    return my_string.replace(letter, '')

# %%
print(solution('banana', 'a'))   # bnn
