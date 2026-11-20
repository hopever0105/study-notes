# -*- coding: utf-8 -*-
# 프로그래머스 입문 · 각도기
# 문제: 각도 angle이 예각(1), 직각(2), 둔각(3), 평각(4) 중 무엇인지 번호로 반환
# Spyder: F5 전체 실행

# %%
def solution(angle):
    if angle < 90:
        answer = 1
    elif angle == 90:
        answer = 2
    elif angle < 180:
        answer = 3
    else:
        answer = 4
    return answer

# %%
print(solution(70))    # 1
print(solution(90))    # 2
print(solution(135))   # 3
print(solution(180))   # 4
