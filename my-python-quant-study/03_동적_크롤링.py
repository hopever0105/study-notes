# selenium 동적 크롤링과 정규표현식 연습
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from bs4 import BeautifulSoup

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))


#%%
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from bs4 import BeautifulSoup

driver = webdriver.Chrome()


#%%
url = 'https://www.naver.com/'
driver.get(url)
driver.page_source[1:1000]


#%%

driver.find_element(By.LINK_TEXT, value = '뉴스').click()


#%%
driver.switch_to.window(driver.window_handles[1])
driver.close()


#%%
driver = webdriver.Chrome()
url = 'https://www.naver.com/'
driver.get(url)
driver.page_source[1:1000]
search = driver.find_element(By.ID, value='query')
search.send_keys('이순신')
search.send_keys(Keys.ENTER)


#%%

search = driver.find_element(By.ID, value='nx_query')
search.clear()
search.send_keys('퀀트투자')
search.send_keys(Keys.ENTER)

#%%

driver.find_element(By.XPATH, value='//*[@id="lnb"]/div[1]/div/div[1]/div[3]/a').click()
driver.find_element(By.XPATH, value= '//*[@id="snb"]/div[1]/div/div[2]/a[2]').click()

driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')

#%%
prev_height= driver.execute_script('return document.body.scrolHeight')


while True:
    driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
    time.sleep(2)

    curr_height = driver.execute_script('return document.body.scrollHeight')
    if curr_height == prev_height:
        break
    prev_height = curr_height

html = BeautifulSoup(driver.page_source,'lxml')
txt= html.find_all(class_ = 'title_link')
txt_list = [i.get_text() for i in txt]

txt_list[0:10]

driver.quit()

#%% 준비 (맨 처음 한 번만 실행)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

driver = webdriver.Chrome()
driver.implicitly_wait(5)

#%% 브라우저 관련: get / back / forward / refresh / close
driver.get('https://quotes.toscrape.com/')
time.sleep(1)
print('제목:', driver.title)
print('주소:', driver.current_url)

driver.find_element(By.PARTIAL_LINK_TEXT, 'Next').click()
time.sleep(1)
print('이동 후 주소:', driver.current_url)

driver.back()
time.sleep(1)
print('back 후:', driver.current_url)

driver.forward()
time.sleep(1)
print('forward 후:', driver.current_url)

driver.refresh()
time.sleep(1)
print('새로고침 후:', driver.current_url)

driver.switch_to.new_window('tab')
driver.get('https://quotes.toscrape.com/login')
print('탭 개수:', len(driver.window_handles))
driver.close()
driver.switch_to.window(driver.window_handles[0])
print('close 후 탭 개수:', len(driver.window_handles))

#%% 엘리먼트 접근: By.* 모든 방법
driver.get('https://quotes.toscrape.com/')
time.sleep(1)

print('TAG_NAME:', driver.find_element(By.TAG_NAME, 'h1').text)

quotes = driver.find_elements(By.CLASS_NAME, 'quote')
print('CLASS_NAME 개수:', len(quotes))
print('CLASS_NAME 첫번째:', quotes[0].find_element(By.CLASS_NAME, 'text').text)

print('CSS_SELECTOR:', driver.find_element(By.CSS_SELECTOR, 'div.quote > span.text').text)

print('XPATH:', driver.find_element(By.XPATH, '//div[@class="quote"]/span[@class="text"]').text)

print('LINK_TEXT:', driver.find_element(By.LINK_TEXT, 'Login').get_attribute('href'))
print('PARTIAL_LINK_TEXT:', driver.find_element(By.PARTIAL_LINK_TEXT, 'Nex').text)

driver.get('https://quotes.toscrape.com/login')
time.sleep(1)
print('ID:', driver.find_element(By.ID, 'username').get_attribute('id'))
print('NAME:', driver.find_element(By.NAME, 'password').get_attribute('name'))

#%% 동작: click / clear / send_keys / 키 조합(Ctrl+A, C, V) / Enter
driver.get('https://quotes.toscrape.com/login')
time.sleep(1)

user = driver.find_element(By.ID, 'username')
pw = driver.find_element(By.ID, 'password')

user.send_keys('abc')
time.sleep(1)
user.clear()
user.send_keys('song')
time.sleep(1)

user.send_keys(Keys.CONTROL, 'a')
user.send_keys(Keys.CONTROL, 'c')
pw.send_keys(Keys.CONTROL, 'v')
print('붙여넣기 결과:', pw.get_attribute('value'))

pw.clear()
pw.send_keys('1234')
pw.send_keys(Keys.ENTER)
time.sleep(1)

print('로그인 후 링크:', driver.find_element(By.LINK_TEXT, 'Logout').text)
driver.find_element(By.LINK_TEXT, 'Logout').click()
time.sleep(1)
print('로그아웃 후 주소:', driver.current_url)

#%% execute_script: 자바스크립트 실행
driver.get('https://quotes.toscrape.com/')
driver.delete_all_cookies()

driver.get('https://quotes.toscrape.com/scroll')
time.sleep(2)
print('처음 개수:', len(driver.find_elements(By.CLASS_NAME, 'quote')))

driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
time.sleep(2)
print('1번 스크롤 후:', len(driver.find_elements(By.CLASS_NAME, 'quote')))

last_h = driver.execute_script('return document.body.scrollHeight;')
same = 0
while same < 3:
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    time.sleep(2)
    new_h = driver.execute_script('return document.body.scrollHeight;')
    if new_h == last_h:
        same += 1
    else:
        same = 0
        last_h = new_h
print('끝까지 스크롤 후:', len(driver.find_elements(By.CLASS_NAME, 'quote')))

print('페이지 제목:', driver.execute_script('return document.title;'))

first = driver.find_element(By.CLASS_NAME, 'quote')
driver.execute_script('arguments[0].scrollIntoView();', first)

driver.get('https://quotes.toscrape.com/')
time.sleep(1)
link = driver.find_element(By.LINK_TEXT, 'Login')
driver.execute_script('arguments[0].click();', link)
time.sleep(1)
print('JS 클릭 후 주소:', driver.current_url)

user = driver.find_element(By.ID, 'username')
driver.execute_script("arguments[0].value = 'jsvalue';", user)
print('JS로 넣은 값:', user.get_attribute('value'))

#%% 크롬 전체 종료
driver.quit()


#%%

import re
data= '동 기업의 매출액은 전년 대비 50.2% 증가했다'
re.findall('\d+.\d+%',data)


#%% . 문자 클래스 : 대괄호 안의 문자 중 한 글자와 매치
p = re.compile('[abc]')
print(p.match('a'))
print(p.match('before'))
print(p.match('dude'))

print(re.findall('[a-z]', 'aB3c'))
print(re.findall('[^0-9]', 'a1b2'))
print(re.findall(r'\d', 'a1b22'))


#%% 모든 문자 . : 줄바꿈(\n)을 제외한 아무 한 글자
print(re.search('a.b', 'a0b'))
print(re.search('a.b', 'ab'))
print(re.search('a[.]b', 'a.b'))
print(re.search('a.b', 'a\nb'))
print(re.search('a.b', 'a\nb', re.DOTALL))

#%% 반복 * + ? {m,n}
p = re.compile('ca*t')
for s in ['ct', 'cat', 'caaat', 'cbt']:
    print('ca*t', s, '->', p.match(s))

p = re.compile('ca+t')
for s in ['ct', 'cat', 'caaat']:
    print('ca+t', s, '->', p.match(s))

p = re.compile('ab?c')
for s in ['ac', 'abc', 'abbc']:
    print('ab?c', s, '->', p.match(s))

p = re.compile('ca{2,3}t')
for s in ['cat', 'caat', 'caaat', 'caaaat']:
    print('ca{2,3}t', s, '->', p.match(s))

#%% 기타 메타문자 ^ $ | \b () \
print(re.search('^Life', 'Life is short'))
print(re.search('^Life', 'My Life'))
print(re.search('short$', 'Life is short'))
print(re.search('short$', 'short life'))
print(re.search('Crow|Servo', 'CrowHill'))
print(re.search(r'\bclass\b', 'no class at all'))
print(re.search(r'\bclass\b', 'the declassified'))

m = re.search(r'(\w+)\s+(\d+)', 'Park 010')
print(m.group(), '/', m.group(1), '/', m.group(2))
print(re.search(r'\.', 'a.b'))

#%% match : 문자열 "처음"부터 정규식과 매치되는지 검사 + compile
p = re.compile('[a-z]+')
m = p.match('python')
print(m)
print(m.group())
print(m.start())
print(m.end())
print(m.span())

print(p.match('3 python'))

m = re.match('[a-z]+', 'python')
print(m)

m = p.match('3 python')
if m:
    print('매치:', m.group())
else:
    print('매치 안 됨')

#%% search : match와 사용법 동일, 문자열 "전체"를 훑어서 처음 매치되는 것
p = re.compile('[a-z]+')
print(p.match('3 python'))
m = p.search('3 python')
print(m)
print(m.group(), m.start(), m.end(), m.span())

#%% findall : 매치되는 모든 문자열을 리스트로
p = re.compile('[a-z]+')
result = p.findall('life is too short')
print(result)

#%% finditer : 매치되는 모든 것을 반복 가능한 객체로 (예시 2개)
p = re.compile('[a-z]+')
result = p.finditer('life is too short')
print(result)
for r in result:
    print(r)

for r in re.finditer(r'\d+', 'a1 b22 c333'):
    print(r.group(), r.start(), r.end())
