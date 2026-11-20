# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 12 · 모음 제거
# 문제: 영어 소문자 문자열 my_string에서 a e i o u 빼기
# Spyder: F5 전체 실행

# %% 정답
def solution(my_string):
    answer = ''
    for ch in my_string:            # 한 글자씩
        if ch not in 'aeiou':       # 모음이 아니면
            answer = answer + ch    #   이어 붙이기
    return answer

# %% 확인
print(solution('bus'))                 # bs
print(solution('nice to meet you'))    # nc t mt y
