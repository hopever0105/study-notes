# %%: 2 * [numbers]
numbers = [1, 2, 3]
print(2 * [numbers])     # [[1, 2, 3], [1, 2, 3]]
# [numbers] = 리스트를 상자에 한 번 더 넣은 것 → [[1, 2, 3]]
# 거기에 2를 곱함 → 그 상자를 두 번 반복 → 리스트 안에 리스트 2개

# %% ② 괄호를 빼도 안 됨: 2 * numbers
print(2 * numbers)       # [1, 2, 3, 1, 2, 3]   ← 이어 붙여서 두 번 반복
# 우리가 원하는 건 [2, 4, 6]: 원소 "하나하나"에 2를 곱한 것

# %% ③ 숫자 하나에 곱하는 건 됨
print(2 * 3)             # 6
# → 원소를 하나씩 꺼내서 곱해야 함 = for로 하나씩 꺼내기

#%% 코드:
def solution_codes(codes):
    answer = []
    for x in codes:                     # 하나씩 꺼내서
        answer.append(str(x).zfill(6))  # 바꾼 값을 붙임
    return answer
#    → append 괄호 안의 "바꾸는 부분"만 "2배"로 고치면 됨


#%% 정답
def solution(numbers):
    return [num*2 for num in numbers]
#%%
def solution(numbers):
    answer = []
    for x in numbers:
        answer.append(x * 2)   # ← 고친 곳: 괄호 안엔 "붙일 값"만. = 쓰지 않음
    return answer

print(solution([1, 2, 3, 4, 5]))           # [2, 4, 6, 8, 10]
print(solution([1, 2, 100, -99, 1, 2, 3])) # [2, 4, 200, -198, 2, 4, 6]

# 왜 append(x = x*2)가 안 되나
#   = 는 "상자에 넣어라"라는 명령이라 함수 괄호 안에 쓰면 뜻이 달라짐
#   → 파이썬이 "x라는 이름의 옵션에 값을 넣겠다"로 읽음
#   → append에는 그런 옵션이 없어서 TypeError: append() takes no keyword arguments
#   append 괄호 안에는 "붙일 값" 하나만: append(x * 2), append(str(x).zfill(6))

# 한 바퀴씩 ([1, 2, 3])
#   x=1 → append(2) → [2]
#   x=2 → append(4) → [2, 4]
#   x=3 → append(6) → [2, 4, 6]