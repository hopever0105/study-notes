# -*- coding: utf-8 -*-
# 프로그래머스 코딩테스트 입문 Day 3 - 최빈값 구하기
# 요약: 정수 리스트에서 가장 많이 나온 값을 돌려준다. 그런 값이 여러 개면 -1.
# 단원: 조건문·딕셔너리 (값마다 개수 세기)
# Spyder에서 F5로 실행

# %% 완성본 (딕셔너리로 세기 - 가장 많이 쓰는 방법)
def solution(array):
    # 1. 값마다 몇 번 나왔는지 센다  → {값: 횟수}
    count = {}
    for x in array:
        count[x] = count.get(x, 0) + 1   # 처음 보는 값이면 0에서 시작해 +1

    # 2. 가장 많이 나온 횟수
    top = max(count.values())

    # 3. 그 횟수만큼 나온 값을 모은다
    modes = []
    for k, v in count.items():           # k = 값, v = 횟수
        if v == top:
            modes.append(k)

    # 4. 여러 개면 -1, 하나면 그 값
    if len(modes) > 1:
        return -1
    return modes[0]


print(solution([1, 2, 3, 3, 3, 4]))   # 3
print(solution([1, 1, 2, 2]))         # -1
print(solution([1]))                  # 1


# %% 설명
# [1, 2, 3, 3, 3, 4] 를 넣으면
#   1단계 count = {1: 1, 2: 1, 3: 3, 4: 1}
#   2단계 top   = 3
#   3단계 modes = [3]
#   4단계 1개뿐 → 3
#
# [1, 1, 2, 2] 를 넣으면
#   1단계 count = {1: 2, 2: 2}
#   2단계 top   = 2
#   3단계 modes = [1, 2]
#   4단계 2개 → -1
#
# count.get(x, 0) : x의 횟수를 꺼내고, 없으면 0을 꺼낸다.
#   아래 4줄과 같은 뜻.
#     if x in count:
#         count[x] = count[x] + 1
#     else:
#         count[x] = 1
#
# 틀렸던 것
#   count[x+1]    ✗ 키(값)에 1을 더함 → 없는 키를 꺼내 KeyError
#   count[x] + 1  ✓ 꺼낸 횟수에 1을 더함
#   들여쓰기 칸 수가 섞이면 IndentationError → 함수 안 4칸, for/if 안 8칸
#
# 계산량: 원소 n개면 세기 n번 + 모으기 최대 n번 → 약 2n번.
#   10만 개여도 20만 번이라 바로 끝남.
#   (리스트.count나 remove를 값마다 쓰면 n×n번 → 10만 개면 100억 번, 시간 초과)
#
# 다른 짧은 방법 (같은 원리, 표준 라이브러리 사용)
#   from collections import Counter
#   c = Counter(array).most_common()      # [(값, 횟수), ...] 많은 순
#   if len(c) > 1 and c[0][1] == c[1][1]: return -1
#   return c[0][0]
