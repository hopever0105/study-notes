# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 13 · 컨트롤 제트
# 문제: 숫자와 Z가 공백으로 구분된 문자열 s. 숫자는 더하고, Z는 바로 앞에 더한 숫자를 취소. 결과 합
# Spyder: F5 전체 실행

# %% 정답
def solution(s):
    stack = []                         # 더한 숫자를 차례로 쌓아 둠
    for x in s.split(' '):             # '1 2 Z 3' → ['1', '2', 'Z', '3']
        if x == 'Z':
            stack.pop()                # 마지막에 넣은 것 꺼내 버리기(취소)
        else:
            stack.append(int(x))       # '-1' 같은 음수도 int로 됨
    return sum(stack)

# %% 확인
print(solution('1 2 Z 3'))         # 4
print(solution('10 20 30 40'))     # 100
print(solution('10 Z 20 Z 1'))     # 1

# %% 포인트
# - 마지막 것부터 꺼내기 = 스택 (append로 넣고 pop으로 꺼냄). 주문 취소 처리와 같은 틀
