# -*- coding: utf-8 -*-
# 프로그래머스 코딩테스트 입문 Day 3 - 짝수는 싫어요
# 요약: n 이하의 홀수를 작은 것부터 리스트로 돌려준다.

#%% 
# 홀수뽑기1. 
n =10 
def solution(n):
    return list(range(1, n + 1, 2))
# range(시작, 끝, 간격) # 끝은 끝-1 까지 
#%%
# 홀수뽑기2.
n= 10 
def solution(n):
    return [i for i in range(1, n + 1) if i % 2 == 1]
