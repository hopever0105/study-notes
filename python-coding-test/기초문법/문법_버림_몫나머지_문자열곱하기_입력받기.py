# -*- coding: utf-8 -*-
# 문법: 버림(int), 몫·나머지(//, %), 결과 두 개를 리스트로, 거꾸로([::-1]), 문자열 곱하기, input()으로 입력 받기
# 프로그래머스 '코딩테스트 입문' Day 5~6 풀기 전 준비 (예시는 일부러 다른 소재)

# %% 1. int(): 소수점 아래를 버림 (반올림 아님)
print(int(9.9))        # 9
print(int(1234.56))    # 1234
pay = 30000 * 0.9      # 10% 할인 → 27000.0 (곱하면 소수가 됨)
print(pay, int(pay))   # 27000.0 27000  ← 정수로 돌려달라면 int()

# %% 2. 큰 기준부터 if/elif (기준이 겹칠 때)
def grade(score):
    if score >= 90:      # 큰 기준을 먼저: 95점은 여기서 끝
        return "A"
    elif score >= 80:    # 여기 오면 이미 90 미만
        return "B"
    else:
        return "C"
print(grade(95), grade(85), grade(10))   # A B C
# 작은 기준(>= 80)을 먼저 쓰면 95점도 B가 돼 버림

# %% 3. // 몫, % 나머지 → 두 값을 리스트 하나로 돌려주기
money = 10000
price = 3000
print(money // price)   # 3     ← 몇 개 살 수 있나
print(money % price)    # 1000  ← 거스름돈
result = [money // price, money % price]
print(result)           # [3, 1000]

# %% 4. 짝수·홀수 판단: % 2
for x in [4, 7, 10]:
    if x % 2 == 0:
        print(x, "짝수")
    else:
        print(x, "홀수")
# 개수를 [짝수 개수, 홀수 개수]로 세려면 칸 두 개짜리 리스트를 만들어 칸을 +1
cnt = [0, 0]
cnt[0] = cnt[0] + 1     # 0번 칸에 1 더하기
print(cnt)              # [1, 0]

# %% 5. 거꾸로: [::-1] 은 리스트에도 문자열에도 됨
print([1, 2, 3][::-1])  # [3, 2, 1]
print("abc"[::-1])      # cba

# %% 6. 문자열 곱하기 = 그 글자를 반복 (리스트 곱하기와 같은 원리)
print("ab" * 3)         # ababab
print("=" * 10)         # ==========

# 글자 하나씩 꺼내 반복해서 새 문자열로 이어 붙이기
word = "hi"
answer = ""             # 빈 문자열에서 시작
for ch in word:         # 문자열을 for로 돌리면 한 글자씩: "h", "i"
    answer = answer + ch * 2   # "hh" 붙이고 → "hhii"
print(answer)           # hhii

# %% 7. 줄마다 개수가 늘어나게 출력: range(1, n+1)
for i in range(1, 4):   # i = 1, 2, 3  (끝 숫자 4는 안 들어감)
    print("#" * i)
# #
# ##
# ###

# %% 8. input(): 키보드로 입력 받기 (return 대신 print로 답하는 문제에서 씀)
# input()은 항상 '문자열'로 받음 → 숫자로 쓰려면 int()
# Spyder에서 F9로 아래 두 줄 실행 → IPython 콘솔에 숫자 치고 Enter
# n = int(input())
# print(n * 2)
# 프로그래머스에서는 채점기가 숫자를 대신 넣어 줌 (n = int(input()) 줄은 문제에 이미 적혀 있기도 함)
