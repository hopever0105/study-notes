# =====================================================================
# 크롤링 기본: HTTP, HTML, rvest
# 목적: 요청/응답 구조 이해, HTML에서 원하는 값 뽑기
# =====================================================================

library(httr)
library(rvest)


# 1. HTTP 요청 기본 (GET) ----------------------------------------------
# httpbin.org: 보낸 요청을 그대로 돌려주는 테스트용 서비스
res <- GET("https://httpbin.org/get", query = list(q = "quant", page = 1))

status_code(res)               # 200이면 성공
headers(res)$`content-type`    # 응답 형식
cat(content(res, as = "text", encoding = "UTF-8"))


# 2. POST 요청 ---------------------------------------------------------
# 조건이 주소가 아니라 본문(body)에 담김. 로그인/검색 폼에서 흔함
res2 <- POST("https://httpbin.org/post",
             body = list(user = "test", value = 123),
             encode = "form")
cat(content(res2, as = "text", encoding = "UTF-8"))


# 3. 헤더 지정 ---------------------------------------------------------
res3 <- GET("https://httpbin.org/headers",
            add_headers(`User-Agent` = "study-bot/0.1 (personal learning)"))
cat(content(res3, as = "text", encoding = "UTF-8"))


# 4. HTML 파싱 기본 ----------------------------------------------------
# 사이트 변수 없이 선택자 연습을 하려고 HTML 문자열을 직접 사용
html_sample <- '
<div id="main">
  <h1>가격표</h1>
  <table class="price">
    <tr><th>날짜</th><th>종가</th></tr>
    <tr><td>10-27</td><td class="num">71,000</td></tr>
    <tr><td>10-28</td><td class="num">70,500</td></tr>
  </table>
  <a href="/next?page=2">다음</a>
</div>'

page <- read_html(html_sample)

page |> html_element("h1") |> html_text2()            # 첫 번째 일치 요소 텍스트
page |> html_elements("td.num") |> html_text2()       # 일치하는 모든 요소 텍스트
page |> html_element("a") |> html_attr("href")        # 속성값
page |> html_element("table.price") |> html_table()   # 표 -> 데이터프레임

# html_element()  : 첫 번째 하나
# html_elements() : 전부 (복수형 s 주의)


# 5. CSS 선택자 요약 ---------------------------------------------------
# h1               모든 h1 태그
# .num             class가 num인 요소
# #main            id가 main인 요소
# table.price td   class=price인 table 안의 td
# div > a          div의 바로 아래 자식 a
# a[href]          href 속성이 있는 a
# tr:nth-child(2)  두 번째 tr


# 6. 문자열 -> 숫자 정리 -----------------------------------------------
raw <- c("71,000", "70,500", "1,234,567")
as.numeric(gsub(",", "", raw))

txt <- "시가총액 427조 8,000억원"
as.numeric(gsub("[^0-9]", "", txt))    # 숫자 외 문자 제거


# 7. 인코딩 ------------------------------------------------------------
# 한글이 깨지면 인코딩을 명시. UTF-8이 안 되면 "EUC-KR" 시도
# res <- GET("https://example.com")
# txt <- content(res, as = "text", encoding = "EUC-KR")
# iconv(txt, from = "EUC-KR", to = "UTF-8")


# 8. 크롤링 매너 -------------------------------------------------------
# - 사이트주소/robots.txt 와 이용약관을 먼저 확인
# - 요청 사이에 대기 시간을 둔다
Sys.sleep(runif(1, 1, 2))   # 1~2초 사이 임의 대기


# ===================================================================
# 직접 HTML 문자열을 만들어 rvest로 표와 링크를 추출하기
# =====================================================================

my_html <- '
<html>
  <body>
    <h2>종목 리스트</h2>
    <table id="stocks">
      <tr><th>종목</th><th>종가</th><th>상세</th></tr>
      <tr>
        <td>종목A</td><td>10,500</td>
        <td><a href="/detail/A">보기</a></td>
      </tr>
      <tr>
        <td>종목B</td><td>23,200</td>
        <td><a href="/detail/B">보기</a></td>
      </tr>
    </table>
    <ul>
      <li><a href="https://example.com/news/1">뉴스1</a></li>
      <li><a href="https://example.com/news/2">뉴스2</a></li>
    </ul>
  </body>
</html>'

doc <- read_html(my_html)

# (1) 표 추출
tbl <- doc |> html_element("table#stocks") |> html_table()
tbl$종가 <- as.numeric(gsub(",", "", tbl$종가))   # 쉼표 제거 후 숫자로
tbl

# (2) 표 안의 링크만 추출
detail_links <- doc |> html_elements("table#stocks a") |> html_attr("href")
detail_links    # "/detail/A" "/detail/B"

# (3) 목록(ul)의 링크와 텍스트를 한 표로
news <- data.frame(
  title = doc |> html_elements("ul li a") |> html_text2(),
  url   = doc |> html_elements("ul li a") |> html_attr("href")
)
news