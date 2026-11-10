# 문제 2. 종목코드 6자리 맞추기
# 엑셀에서 불러온 종목코드가 앞의 0이 빠진 정수로 들어왔다.
# 정수 리스트 codes를 받아, 각 코드를 앞을 0으로 채운 6자리 "문자열"로 바꾼
# 리스트를 return 한다. 순서는 그대로.
# 제한: 1 ≤ len(codes) ≤ 100 / 1 ≤ codes[i] ≤ 999,999
# 쓸 문법: ② str(), zfill(), 빈 리스트 + append

def solution(codes):
    answer = []
    # 여기를 채우기
    return answer

print(solution([5930, 660, 35420]))  # ['005930', '000660', '035420']
print(solution([123456]))            # ['123456']



#%% 정답 2. 종목코드 6자리 맞추기
# 엑셀에서 불러온 종목코드가 앞의 0이 빠진 정수로 들어왔다.
# 정수 리스트 codes를 받아, 각 코드를 앞을 0으로 채운 6자리 "문자열"로 바꾼
# 리스트를 return 한다. 순서는 그대로.
# 제한: 1 ≤ len(codes) ≤ 100 / 1 ≤ codes[i] ≤ 999,999
# 쓸 문법: ② str(), zfill(), 빈 리스트 + append

def solution(codes):
    answer = []
    for x in codes:
        answer.append(str(x).zfill(6))
    return answer

print(solution([5930, 660, 35420]))  # ['005930', '000660', '035420']
print(solution([123456]))            # ['123456']



#%%