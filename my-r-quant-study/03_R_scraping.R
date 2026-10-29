# =====================================================================
# 크롤링 실습
# 순서: 한 페이지 성공 -> 함수화 -> 여러 페이지 -> 정리 -> 저장
# =====================================================================

library(rvest)
library(dplyr)


# 1. 한 페이지에서 먼저 성공시키기 -------------------------------------
url  <- "https://books.toscrape.com/catalogue/page-1.html"
page <- read_html(url)

# 반복되는 단위(책 카드)를 먼저 잡고, 그 안에서 값을 뽑는다
items <- page |> html_elements("article.product_pod")
length(items)    # 한 페이지의 책 수 (20)

book_df <- tibble(
  title = items |> html_element("h3 a") |> html_attr("title"),
  price = items |> html_element(".price_color") |> html_text2(),
  link  = items |> html_element("h3 a") |> html_attr("href")
)
head(book_df)

# 가격 문자열 -> 숫자, 링크 -> 전체 주소
book_df <- book_df |>
  mutate(
    price = as.numeric(gsub("[^0-9.]", "", price)),
    link  = paste0("https://books.toscrape.com/catalogue/", link)
  )
str(book_df)


# 2. 표(table)는 한 번에 -----------------------------------------------
detail <- read_html(book_df$link[1])

info <- detail |> html_element("table.table-striped") |> html_table()
info

all_tables <- detail |> html_elements("table") |> html_table()   # 페이지의 모든 표
length(all_tables)


# 3. 함수로 만들기 -----------------------------------------------------
scrape_list_page <- function(page_no) {
  url <- sprintf("https://books.toscrape.com/catalogue/page-%d.html", page_no)
  
  page <- tryCatch(read_html(url), error = function(e) NULL)
  if (is.null(page)) return(NULL)
  
  items <- page |> html_elements("article.product_pod")
  if (length(items) == 0) return(NULL)
  
  tibble(
    page   = page_no,
    title  = items |> html_element("h3 a") |> html_attr("title"),
    price  = items |> html_element(".price_color") |> html_text2(),
    rating = items |> html_element("p.star-rating") |> html_attr("class"),
    link   = items |> html_element("h3 a") |> html_attr("href")
  )
}

scrape_list_page(2) |> head(3)


# 4. 여러 페이지 수집 --------------------------------------------------
pages <- 1:5    # 연습이므로 5페이지만

out <- vector("list", length(pages))
for (i in seq_along(pages)) {
  out[[i]] <- scrape_list_page(pages[i])
  message("page ", pages[i], " 완료")
  Sys.sleep(runif(1, 1, 2))      # 서버 부담을 줄이는 대기
}

books <- bind_rows(out)
dim(books)


# 5. 후처리 ------------------------------------------------------------
books <- books |>
  mutate(
    price      = as.numeric(gsub("[^0-9.]", "", price)),
    rating     = sub("star-rating ", "", rating),    # "Three" 등만 남김
    rating_num = match(rating, c("One", "Two", "Three", "Four", "Five")),
    link       = paste0("https://books.toscrape.com/catalogue/", link)
  )

books |>
  group_by(rating_num) |>
  summarise(n = n(), avg_price = mean(price)) |>
  arrange(rating_num)


# 6. 저장 --------------------------------------------------------------
dir.create("data", showWarnings = FALSE)
saveRDS(books, "data/books.rds")
write.csv(books, "data/books.csv", row.names = FALSE, fileEncoding = "UTF-8")


# 7. 자주 나는 문제 ----------------------------------------------------
# 결과가 character(0)  -> 선택자 오타 또는 자바스크립트로 나중에 채워지는 값
#                         (개발자 도구 Network 탭에서 JSON 주소를 찾아 직접 호출)
# 한글 깨짐             -> read_html(url, encoding = "EUC-KR")
# 403 / 429             -> 요청이 잦음. 대기 시간을 늘리고 약관 확인
# 줄이 밀림             -> 카드 단위로 뽑지 않음. 반복 단위 안에서 값을 뽑기
# 숫자 계산 불가        -> 쉼표/통화기호 제거 (gsub)


# =====================================================================
# 책 목록을 가격순으로 정렬해 상위 10권을 CSV로 저장하기
# (위에서 만든 books 데이터프레임 사용)
# =====================================================================

top10 <- books |>
  arrange(desc(price)) |>          # 가격 높은 순
  slice_head(n = 10) |>            # 상위 10권
  select(title, price, rating_num, link)

top10

dir.create("data", showWarnings = FALSE)
write.csv(top10, "data/top10_expensive_books.csv",
          row.names = FALSE, fileEncoding = "UTF-8")

# 엑셀에서 한글이 깨지면 아래 방식으로 저장 (BOM 포함)
# readr::write_excel_csv(top10, "data/top10_expensive_books.csv")