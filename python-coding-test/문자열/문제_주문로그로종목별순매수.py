# -*- coding: utf-8 -*-
# 주문 로그로 종목별 순매수 수량 (Lv1)
# 문제: "종목코드 매수|매도 수량" 문자열 리스트 → {종목코드: 순매수}. 매수 +, 매도 -. 종목코드 앞자리 0 유지.
# 예: ["005930 매수 10", "000660 매도 5", "005930 매도 3"] → {'005930': 7, '000660': -5}
# Spyder: F5 전체 실행

# %% 정답
def net_buy_by_code(logs):
    total = {}
    for line in logs:                          # line = "005930 매수 10" 한 줄
        code, side, qty = line.split(' ')      # ['005930', '매수', '10'] → 세 이름에 나눠 담기
        qty = int(qty)                         # '10' → 10 (code는 문자열 그대로 → 앞자리 0 유지)
        if side == '매도':
            qty = -qty                         # 매도는 빼기
        if code in total:
            total[code] = total[code] + qty    # 있으면 더하기
        else:
            total[code] = qty                  # 없으면 새로 넣기
    return total

# %% 확인
print(net_buy_by_code(["005930 매수 10", "000660 매도 5", "005930 매도 3"]))   # {'005930': 7, '000660': -5}
print(net_buy_by_code([]))                                                       # {}

# %% 포인트
# - split(' ')은 '조각 리스트'를 돌려줌 → a, b, c = 리스트 로 한 번에 나눠 담을 수 있음
# - int('000660') 하면 660이 되어 0이 사라짐 → 종목코드는 int로 바꾸지 않음
