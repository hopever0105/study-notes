# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 6 문자 반복 출력하기: 문자열의 각 글자를 n번씩 반복해 이어 붙이기
# 틀렸던 것: split(my_string, '') (split은 메서드, 빈 칸으로 못 쪼갬), 리스트 * n (통째 반복), 리스트를 돌려줌

# %% 풀이
def solution(my_string, n):
    answer = ""
    for ch in my_string:               # 문자열을 for로 돌리면 글자 하나씩
        answer = answer + ch * n
    return answer

print(solution("hello", 3))            # hhheeellllllooo
