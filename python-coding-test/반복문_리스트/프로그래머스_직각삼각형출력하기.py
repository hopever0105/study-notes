# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 6 직각삼각형 출력하기: n을 입력 받아 i번째 줄에 * i개 출력 (print로 답하는 문제)

# %% 풀이 (실행하면 콘솔에 숫자 입력)
n = int(input())
for i in range(1, n + 1):     # 1부터 n까지 (끝은 n+1)
    print("*" * i)
