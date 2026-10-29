# requests + BeautifulSoup 정적 크롤링 연습
import requests as rq

url = 'http://quotes.toscrape.com/'
quote = rq.get(url)

print(quote)

#%%
quote.content[:1000]

#%%
from bs4 import BeautifulSoup

quote_html = BeautifulSoup(quote.content,'html.parser')
quote_html.head()


#%% %
quote_div = quote_html.find_all('div',class_='quote')

quote_div[0]


quote_span = quote_div[0].find_all('span',class_='text')

quote_span

quote_span[0].text

quote_div = quote_html.find_all('div',class_ = 'quote')
[i.find_all('span', class_ = 'text')[0].text for i in quote_div]

#%%


quote_text = quote_html.select('div.quote>span.text')

quote_text


quote_text_list = [i.text for i in quote_text]

quote_text_list


quote_author = quote_html.select('div.quote > span > small.author')
quote_author_list= [i.text for i in quote_author]

quote_author_list


quote_link = quote_html.select('div.quote > span> a')
quote_link

quote_link[0]['href']

['https://quotes.toscrape.com' + i['href'] for i in quote_link]


#%%

import requests as rq
from bs4 import BeautifulSoup
import time

text_list = []
author_list = []
infor_list = []

for i in range(1,100) :
    url = f'https://quotes.toscrape.com/page/{i}/'
    quote = rq.get(url)
    quote_html = BeautifulSoup(quote.content,'html.parser')

    quote_text = quote_html.select('div.quote>span.text')
    quote_text_list= [i.text for i in quote_text]

    quote_author = quote_html.select('div.quote>span>small.author')
    quote_author_list = [i.text for i in quote_author]

    quote_link = quote_html.select('div.quote>span>a')
    quote_link_list = ['https://quotes.toscrape.com' + i['href'] for i in quote_link]

    if len(quote_text_list) > 0:

        text_list.extend(quote_text_list)
        author_list.extend(quote_author_list)
        infor_list.extend(quote_link_list)
        time.sleep(1)

    else:
        break


#%%
import pandas as pd
pd.DataFrame({'text': text_list, 'author': author_list, 'infor': infor_list})


#%%
from selenium import webdriver
from bs4 import BeautifulSoup
import time

url = 'https://stock.naver.com/news/flashnews'
driver = webdriver.Chrome()
driver.get(url)
time.sleep(3)
html = BeautifulSoup(driver.page_source, 'html.parser')
driver.quit()

html_select = html.select('dl > dd > div > div > a')
html_select[0:3]

html_select[0].select_one('h3').text
html_select[0]['href']

for i in html_select[0:10]:
    print(i.select_one('h3').text, i['href'])

#%%
import requests as rq

url = 'https://stock.naver.com/api/domestic/news/list?category=FLASHNEWS&page=1&pageSize=10&date=20261009'

data = rq.get(url, headers={'User-Agent': 'Mozilla/5.0'})

result = data.json()

articles = result['articles']

title_list = [a['title'] for a in articles]
print(title_list)

for a in articles:
    link = f"https://n.news.naver.com/article/{a['officeId']}/{a['articleId']}"
    print(a['title'])
    print(a['datetime'])
    print(a['officeHname'])
    print(link)
    print()


#%%
import pandas as pd

url = 'https://en.wikipedia.org/wiki/List_of_countries_by_stock_market_capitalization'

tbl = pd.read_html(url, storage_options={'User-Agent': 'Mozilla/5.0'})

tbl[0].head()


#%%
import requests as rq
from bs4 import BeautifulSoup
import pandas as pd

url = 'https://kind.krx.co.kr/disclosure/todaydisclosure.do'
payload = {
    'method': 'searchTodayDisclosureSub',
    'currentPageSize': '15',
    'pageIndex': '1',
    'orderMode': '0',
    'orderStat': 'D',
    'forward': 'todaydisclosure_sub',
    'chose':'S',
    'todayFlag': 'Y',
    'selDate': '2026-01-05'
}

data = rq.post(url, data=payload)
html = BeautifulSoup(data.content, 'html.parser' )


html_unicode= html.prettify()
tbl= pd.read_html(html.prettify())

tbl[0]
