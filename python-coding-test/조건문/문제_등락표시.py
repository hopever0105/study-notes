# -*- coding: utf-8 -*-
# 문제: 등락률 change를 보고 급등·상승·보합·하락·급락 글자 돌려주기 (if/elif/else)
# 틀렸던 것: answer = '"급등"' → 따옴표가 글자 안에 들어감. answer = "급등" 이 맞음

# %% 풀이
def label(change):
    if change >= 5:
        answer = "급등"
    elif change > 0:
        answer = "상승"
    elif change == 0:
        answer = "보합"
    elif change <= -5:
        answer = "급락"
    else:
        answer = "하락"
    return answer

# %% 확인
print(label(7.2), label(5), label(0), label(-1.5), label(-5))
# 급등 급등 보합 하락 급락
