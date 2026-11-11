# -*- coding: utf-8 -*-
# 딕셔너리 문법: 꺼내기·추가·in, 개수 세기, 값 더해 가기, items()
# Spyder에서 F5로 실행

# %% 1. 만들기·꺼내기·바꾸기·추가
close = {"삼성전자": 70000, "NAVER": 200000}   # {키: 값, 키: 값}

print(close["삼성전자"])        # 70000  (대괄호에 키를 넣어 꺼냄)
close["삼성전자"] = 71000       # 이미 있는 키 → 값이 바뀜
close["카카오"] = 40000         # 없던 키 → 새로 추가됨
print(close)   # {'삼성전자': 71000, 'NAVER': 200000, '카카오': 40000}

# %% 2. 없는 키를 꺼내면 에러 → in으로 먼저 확인
print("LG화학" in close)    # False
print("NAVER" in close)     # True
# print(close["LG화학"])    # KeyError: 'LG화학'  ← 주석 풀면 에러

# %% 3. 개수 세기 틀 (가장 많이 쓰는 모양)
sectors = ["반도체", "은행", "반도체", "자동차", "반도체", "은행"]

count = {}                      # 빈 딕셔너리에서 시작
for s in sectors:               # 리스트 원소를 하나씩 꺼냄
    if s in count:              # 이미 나온 적 있으면
        count[s] = count[s] + 1     # 원래 개수 + 1
    else:                       # 처음 나왔으면
        count[s] = 1                # 1로 시작
print(count)   # {'반도체': 3, '은행': 2, '자동차': 1}

# 한 바퀴씩 따라가 보기
# s="반도체" → 없음 → {'반도체':1}
# s="은행"   → 없음 → {'반도체':1, '은행':1}
# s="반도체" → 있음 → {'반도체':2, '은행':1}
# s="자동차" → 없음 → {'반도체':2, '은행':1, '자동차':1}
# s="반도체" → 있음 → {'반도체':3, ...}
# s="은행"   → 있음 → {'반도체':3, '은행':2, '자동차':1}

# %% 4. 1씩 말고 '값을 더해 가기' (개수 세기와 같은 틀, +1 대신 +금액)
deposits = [("철수", 100), ("영희", 50), ("철수", 30)]   # (이름, 입금액)

total = {}
for name, amount in deposits:       # 묶음을 두 변수로 나눠 받음
    if name in total:
        total[name] = total[name] + amount
    else:
        total[name] = amount
print(total)   # {'철수': 130, '영희': 50}

# 빼야 할 때는 -amount를 더하면 된다:  total[name] = total[name] - amount

# %% 5. 딕셔너리 돌기: .items()는 (키, 값)을 한 쌍씩 꺼냄
for name, money in total.items():
    print(name, money)
# 철수 130
# 영희 50
