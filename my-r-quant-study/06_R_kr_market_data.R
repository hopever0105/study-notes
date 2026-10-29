# =====================================================================
# 한국 시장 종목 목록과 업종 정보 수집
# 목적: 종목코드/종목명/시가총액 목록과 업종 목록을 표로 만들기
# 설계: 사이트 구조가 바뀌어도 덜 깨지도록
#       (1) 구조 점검 함수로 먼저 확인하고
#       (2) 특정 클래스명 대신 "가장 큰 표"와 링크 패턴을 이용한다
# 주의: 이 스크립트는 작성 시점에 대상 사이트 구조를 직접 확인하지 못했음.
#       실행 전 robots.txt, 이용약관 확인 + inspect_tables()로 구조 점검 필수
# =====================================================================

library(httr)
library(rvest)
library(dplyr)

BASE   <- "https://finance.naver.com"
UA     <- "study-bot/0.1 (personal learning; low rate)"
ENC    <- "EUC-KR"      # 한글이 깨지면 "UTF-8"로 바꿔 보기
WAIT   <- c(1, 2)       # 요청 사이 대기 범위(초)


# 1. 수집 전 점검: robots.txt ------------------------------------------
check_robots <- function(base = BASE) {
  txt <- tryCatch(readLines(paste0(base, "/robots.txt"), warn = FALSE),
                  error = function(e) NULL)
  if (is.null(txt)) {
    message("robots.txt를 읽지 못했습니다. 브라우저로 직접 확인하세요.")
    return(invisible(NULL))
  }
  cat(txt, sep = "\n")
  invisible(txt)
}
# check_robots()    # 실행해서 Disallow 경로에 수집 대상이 없는지 눈으로 확인


# 2. 공통 함수 ---------------------------------------------------------
# 2-1. 페이지 읽기: User-Agent, 타임아웃, 인코딩 지정, 대기
read_page <- function(url, enc = ENC) {
  Sys.sleep(runif(1, WAIT[1], WAIT[2]))
  res <- tryCatch(GET(url, add_headers(`User-Agent` = UA), timeout(15)),
                  error = function(e) NULL)
  if (is.null(res) || status_code(res) != 200) {
    message("요청 실패: ", url, " (", ifelse(is.null(res), "연결오류", status_code(res)), ")")
    return(NULL)
  }
  read_html(content(res, as = "raw"), encoding = enc)
}

# 2-2. 구조 점검: 페이지에 있는 표들의 크기와 머리글 출력
`%||%` <- function(a, b) if (is.null(a) || is.na(a)) b else a

inspect_tables <- function(url, enc = ENC) {
  pg <- read_page(url, enc)
  if (is.null(pg)) return(invisible(NULL))
  tabs <- pg |> html_elements("table")
  for (i in seq_along(tabs)) {
    t <- tryCatch(html_table(tabs[[i]]), error = function(e) NULL)
    if (is.null(t)) next
    cat(sprintf("[표 %d] class=%s  %d행 x %d열\n    열: %s\n",
                i, html_attr(tabs[[i]], "class") %||% "(none)",
                nrow(t), ncol(t), paste(names(t), collapse = " | ")))
  }
  invisible(pg)
}

# 2-3. 가장 행이 많은 표를 선택
biggest_table <- function(pg) {
  tabs <- pg |> html_elements("table")
  tl <- lapply(tabs, function(t) tryCatch(html_table(t), error = function(e) NULL))
  tl <- Filter(Negate(is.null), tl)
  if (length(tl) == 0) return(NULL)
  tl[[which.max(vapply(tl, nrow, integer(1)))]]
}

# 2-4. 숫자처럼 보이는 열을 숫자로 변환 (쉼표, %, 공백 제거)
#      except 열(기본: code)은 건드리지 않음 -> 종목코드 앞자리 0 보존
to_numeric_cols <- function(df, except = "code") {
  for (nm in setdiff(names(df), except)) {
    if (is.character(df[[nm]])) {
      cleaned <- gsub("[,%\\s]", "", df[[nm]])
      cleaned <- gsub("\\+", "", cleaned)
      num <- suppressWarnings(as.numeric(cleaned))
      # 값의 절반 이상이 숫자로 바뀌면 숫자 열로 판단
      if (mean(!is.na(num[!is.na(df[[nm]]) & df[[nm]] != ""])) > 0.5) df[[nm]] <- num
    }
  }
  df
}

# 2-5. 링크에서 6자리 종목코드 뽑기: name -> code 표
extract_code_map <- function(pg) {
  a <- pg |> html_elements("a")
  href <- html_attr(a, "href")
  txt  <- html_text2(a)
  has_code <- !is.na(href) & grepl("code=\\d{6}", href)
  tibble(
    name = txt[has_code],
    code = sub(".*code=(\\d{6}).*", "\\1", href[has_code])
  ) |> distinct(name, .keep_all = TRUE)
}


# 3. 시가총액 순 종목 목록 수집 ---------------------------------------
# sosok=0 코스피, 1 코스닥 (사이트의 파라미터 규칙. 점검 후 필요하면 수정)
market_sum_url <- function(sosok, page) {
  sprintf("%s/sise/sise_market_sum.naver?sosok=%d&page=%d", BASE, sosok, page)
}

# 마지막 페이지 번호: 페이지 안의 'page=숫자' 링크 중 최댓값
get_last_page <- function(pg) {
  href <- html_attr(html_elements(pg, "a"), "href")
  href <- href[!is.na(href) & grepl("sise_market_sum.*page=\\d+", href)]
  if (length(href) == 0) return(1L)
  max(as.integer(sub(".*page=(\\d+).*", "\\1", href)), na.rm = TRUE)
}

scrape_market_sum <- function(sosok = 0, max_pages = 3,
                              cache = sprintf("data/market_sum_%d.rds", sosok)) {
  if (file.exists(cache)) { message("캐시 사용: ", cache); return(readRDS(cache)) }
  
  first <- read_page(market_sum_url(sosok, 1))
  stopifnot(!is.null(first))
  last_page <- min(get_last_page(first), max_pages)    # 상한으로 과도한 요청 방지
  message("수집 페이지 수: ", last_page)
  
  out <- vector("list", last_page)
  for (p in seq_len(last_page)) {
    pg <- if (p == 1) first else read_page(market_sum_url(sosok, p))
    if (is.null(pg)) next
    
    tb <- biggest_table(pg)
    if (is.null(tb)) next
    tb <- tb[rowSums(is.na(tb) | tb == "") < ncol(tb), ]   # 빈 구분행 제거
    
    codes <- extract_code_map(pg)
    # 종목명 열을 찾아 코드와 결합: 코드 표의 name과 일치하는 값이 가장 많은 열
    hit <- vapply(tb, function(col) sum(col %in% codes$name), integer(1))
    name_col <- names(tb)[which.max(hit)]
    tb <- tb |> left_join(codes, by = setNames("name", name_col))
    
    out[[p]] <- tb |> mutate(market = ifelse(sosok == 0, "KOSPI", "KOSDAQ"), page = p)
    message("page ", p, "/", last_page, " 완료")
  }
  
  res <- bind_rows(out) |> to_numeric_cols()
  dir.create("data", showWarnings = FALSE)
  saveRDS(res, cache)
  res
}


# 4. 업종 목록 수집 ----------------------------------------------------
# 업종 링크의 규칙(예: ...no=숫자)을 이용해 업종명과 번호를 표로 만든다
scrape_sectors <- function(cache = "data/sectors.rds") {
  if (file.exists(cache)) return(readRDS(cache))
  
  pg <- read_page(paste0(BASE, "/sise/sise_group.naver?type=upjong"))
  stopifnot(!is.null(pg))
  
  a <- pg |> html_elements("a")
  href <- html_attr(a, "href")
  ok <- !is.na(href) & grepl("type=upjong", href) & grepl("no=\\d+", href)
  
  res <- tibble(
    sector    = html_text2(a)[ok],
    sector_no = sub(".*no=(\\d+).*", "\\1", href[ok])
  ) |> distinct()
  
  dir.create("data", showWarnings = FALSE)
  saveRDS(res, cache)
  res
}


# 5. 실행 순서 (처음에는 한 줄씩 실행하며 눈으로 확인) ----------------
# check_robots()
# inspect_tables(market_sum_url(0, 1))    # 표 구조 확인
# kospi <- scrape_market_sum(sosok = 0, max_pages = 2)
# glimpse(kospi)
# sectors <- scrape_sectors()
# head(sectors)


# =====================================================================
# 아래 HTML 문자열을 파싱해 종목명, 코드, 시가총액(숫자) 표를 만들고
# 시가총액 상위 2개 종목을 뽑기. 코드는 링크의 code= 뒤 6자리.
# =====================================================================

mock_html <- '
<table class="list">
  <tr><th>종목명</th><th>현재가</th><th>시가총액</th></tr>
  <tr><td><a href="/item/main.naver?code=000001">에이전자</a></td><td>10,500</td><td>1,200</td></tr>
  <tr><td colspan="3"></td></tr>
  <tr><td><a href="/item/main.naver?code=000002">비화학</a></td><td>55,000</td><td>8,400</td></tr>
  <tr><td><a href="/item/main.naver?code=000003">씨금융</a></td><td>7,300</td><td>3,150</td></tr>
</table>'

pg <- read_html(mock_html)

tb <- biggest_table(pg)
tb <- tb[rowSums(is.na(tb) | tb == "") < ncol(tb), ]    # 빈 행 제거
codes <- extract_code_map(pg)

result <- tb |>
  left_join(codes, by = c("종목명" = "name")) |>
  to_numeric_cols()

top2 <- result |>
  arrange(desc(시가총액)) |>
  slice_head(n = 2) |>
  select(종목명, code, 시가총액)
top2
# 기대 결과: 비화학(000002, 8400), 씨금융(000003, 3150)

stopifnot(is.character(result$code),
          identical(top2$code, c("000002", "000003")),
          identical(top2$시가총액, c(8400, 3150)))

# inspect_tables 동작 점검용 (네트워크 없이): 문자열 HTML에서 표 요약 출력
tabs <- pg |> html_elements("table")
t1 <- html_table(tabs[[1]])
cat(sprintf("[표 1] class=%s  %d행 x %d열\n    열: %s\n",
            html_attr(tabs[[1]], "class") %||% "(none)",
            nrow(t1), ncol(t1), paste(names(t1), collapse = " | ")))