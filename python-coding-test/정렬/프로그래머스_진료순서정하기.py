# -*- coding: utf-8 -*-
# 프로그래머스 입문 · 진료순서 정하기
# 문제: 응급도 리스트 emergency에서 각 값이 응급도 높은 순서로 몇 번째인지 순위 리스트 반환 (응급도 값 중복 없음)
# Spyder: F5 전체 실행

# %%
def solution(emergency):
    sorted_list = sorted(emergency, reverse=True)    # 응급도 큰 순서로 정렬
    answer = []
    for x in emergency:
        rank = sorted_list.index(x) + 1              # 0부터 세므로 +1
        answer.append(rank)
    return answer

# %%
print(solution([3, 76, 24]))    # [3, 1, 2]
