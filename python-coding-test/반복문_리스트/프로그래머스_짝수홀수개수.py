# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 6 짝수 홀수 개수: 정수 리스트에서 [짝수 개수, 홀수 개수]

# %% 풀이
def solution(num_list):
    answer = [0, 0]                     # [짝수 개수, 홀수 개수]
    for x in num_list:
        if x % 2 == 0:
            answer[0] = answer[0] + 1
        else:
            answer[1] = answer[1] + 1
    return answer

print(solution([1, 2, 3, 4, 5]))        # [2, 3]
