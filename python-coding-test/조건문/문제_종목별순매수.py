# -*- coding: utf-8 -*-
# 문제: "종목명 방향 수량" 문자열 리스트 → 종목별 순매수(매수 합 - 매도 합) 딕셔너리
# 문자열 split(순매수수량 문제) + 딕셔너리 더해 가기(주문종류세기 문제)를 합친 것

# %% 풀이
def net_by_stock(trades):
    net = {}
    for t in trades:
        name, side, qty = t.split()   # "삼성전자 매수 10" → "삼성전자", "매수", "10"
        qty = int(qty)                # 문자열 "10" → 숫자 10
        if side == "매도":
            qty = -qty                # 매도는 빼야 하니 음수로
        if name in net:
            net[name] = net[name] + qty
        else:
            net[name] = qty
    return net

# %% 확인
print(net_by_stock(["삼성전자 매수 10", "SK하이닉스 매수 5", "삼성전자 매도 3"]))  # {'삼성전자': 7, 'SK하이닉스': 5}
print(net_by_stock(["NAVER 매도 4", "NAVER 매수 4"]))   # {'NAVER': 0}
print(net_by_stock(["카카오 매도 2"]))                  # {'카카오': -2}
