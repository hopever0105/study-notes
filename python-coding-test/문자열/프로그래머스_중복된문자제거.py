# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 13 · 중복된 문자 제거
# 문제: 문자열 my_string에서 중복 글자는 처음 나온 것만 남기기 (공백도 글자)
# Spyder: F5 전체 실행

# %% 정답
def solution(my_string):
    answer = ''
    for ch in my_string:
        if ch not in answer:        # 아직 안 넣은 글자면
            answer = answer + ch
    return answer

# %% 확인
print(solution('people'))              # peol
print(solution('We are the world'))    # We arthwold
