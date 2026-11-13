# -*- coding: utf-8 -*-
# 문법: sorted와 .sort() 차이, 슬라이싱, sum·len 평균, key·lambda, 딕셔너리 값 기준 정렬
# Spyder에서 F5로 실행

# %% 1. sorted: 정렬된 '새 리스트'를 돌려줌, 원래 리스트는 그대로
scores = [80, 95, 70, 88]
a = sorted(scores)                  # 작은 순서
b = sorted(scores, reverse=True)    # 큰 순서
print(a)       # [70, 80, 88, 95]
print(b)       # [95, 88, 80, 70]
print(scores)  # [80, 95, 70, 88]  ← 그대로

# %% 2. .sort(): 원래 리스트를 직접 바꾸고, 돌려주는 값은 None
scores2 = [80, 95, 70, 88]
x = scores2.sort()
print(scores2)  # [70, 80, 88, 95]  ← 원래 리스트가 바뀜
print(x)        # None  ← 그래서 answer = 리스트.sort() 로 쓰면 안 됨

# %% 3. 슬라이싱: 리스트[시작:끝] → 시작부터 끝 '바로 앞'까지
nums = [10, 20, 30, 40, 50]
print(nums[:2])    # [10, 20]       앞에서 2개 (0번, 1번)
print(nums[1:4])   # [20, 30, 40]   1번부터 3번까지 (4번은 안 들어감)
print(nums[-2:])   # [40, 50]       뒤에서 2개 (-1이 마지막, -2가 그 앞)
print(nums[::-1])  # [50, 40, 30, 20, 10]  거꾸로
#%%
nums = [10, 20, 30, 40, 50]
print(nums[0:5:1])   # [10, 20, 30, 40, 50]  0번부터 끝까지 1칸씩 (기본값)
print(nums[::2])     # [10, 30, 50]          처음부터 끝까지 2칸씩 건너뛰며
print(nums[::-1])    # [50, 40, 30, 20, 10]  처음부터 끝까지, -1칸씩 = 뒤에서부터
# %% 4. 합·개수·평균
print(sum(nums))              # 150
print(len(nums))              # 5
print(sum(nums) / len(nums))  # 30.0  ← / 나눗셈은 항상 소수(float)로 나옴

# %% 5. key: '무엇을 기준으로' 정렬할지 정함
words = ["banana", "kiwi", "apple"]
print(sorted(words, key=len))   # ['kiwi', 'apple', 'banana']  글자 수 기준

# %% 6. lambda: 한 줄짜리 이름 없는 함수
# lambda x: x[1]  =  "x를 받아서 x[1]을 돌려줘"
pairs = [("민수", 80), ("지영", 95), ("철호", 70)]
print(sorted(pairs, key=lambda x: x[1]))
# [('철호', 70), ('민수', 80), ('지영', 95)]  ← 두 번째 칸(점수) 기준

# %% 7. 딕셔너리를 값 기준으로 정렬
score_dict = {"민수": 80, "지영": 95, "철호": 70}
print(score_dict.items())
# dict_items([('민수', 80), ('지영', 95), ('철호', 70)])  ← (키, 값) 쌍들
ranked = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
print(ranked)  # [('지영', 95), ('민수', 80), ('철호', 70)]

# 이름만 뽑기: 앞에서 배운 for + append
names = []
for name, s in ranked:
    names.append(name)
print(names)   # ['지영', '민수', '철호']




# %% 8. key를 def로 먼저 써 보기
def get_score(x):        # x = ("민수", 80) 같은 묶음 하나
    return x[1]          # x[0] = "민수", x[1] = 80 → 점수만 돌려줌

pairs = [("민수", 80), ("지영", 95), ("철호", 70)]
print(sorted(pairs, key=get_score))
# [('철호', 70), ('민수', 80), ('지영', 95)]

# %% 9. def와 lambda는 같은 뜻
# def get_score(x):
#     return x[1]
#            ↓ 똑같음
# lambda x: x[1]       (lambda 받는값: 돌려줄값)

print(sorted(pairs, key=lambda x: x[1]))   # 결과 위와 같음


# %% 10. 딕셔너리를 그냥 sorted에 넣으면 '키(이름)'만 나옴
score_dict = {"민수": 80, "지영": 95, "철호": 70}
print(sorted(score_dict))
# ['민수', '지영', '철호']  ← 점수는 사라지고 이름 가나다순

# %% 11. .items()로 (이름, 점수) 묶음 리스트로 바꾸면 → 위 pairs와 같은 모양
print(list(score_dict.items()))
# [('민수', 80), ('지영', 95), ('철호', 70)]   ← 3번 pairs와 똑같음

# 그래서 3번과 똑같이 key=lambda x: x[1] (점수 칸 기준), reverse=True (큰 순서)
ranked = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
print(ranked)
# [('지영', 95), ('민수', 80), ('철호', 70)]

# %% 12. for name, s in ranked: 묶음을 두 변수에 나눠 담기
for name, s in ranked:
    print(name, s)
# 1바퀴: ('지영', 95) → name='지영', s=95
# 2바퀴: ('민수', 80) → name='민수', s=80
# 3바퀴: ('철호', 70) → name='철호', s=70
