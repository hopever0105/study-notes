# =====================================================================
# 주가 일괄 수집, DART 재무제표, 가치지표 계산
# 구성: (A) 주가 일괄 수집(캐시)  (B) DART 호출 도구(호출 제한)
#       (C) 재무제표 수집  (D) 가치지표 계산
# 주의: 수집 함수는 맨 아래에서 주석으로 막아둠. 한 단계씩 풀어서 실행
# =====================================================================

library(httr)
library(jsonlite)
library(xml2)
library(dplyr)
library(quantmod)


# ---------------------------------------------------------------------
# A. 주가 일괄 수집
# ---------------------------------------------------------------------

# 1. 종목 한 개의 수정종가를 받아 캐시하기 -----------------------------
get_adj_close <- function(code, suffix = ".KS",
                          from = "2024-01-01", to = Sys.Date(),
                          cache_dir = "data/prices") {
  dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)
  f <- file.path(cache_dir, paste0(code, suffix, ".rds"))
  if (file.exists(f)) return(readRDS(f))              # 이미 받았으면 재사용
  
  x <- tryCatch(
    getSymbols(paste0(code, suffix), src = "yahoo",
               from = from, to = to, auto.assign = FALSE),
    error = function(e) NULL
  )
  Sys.sleep(1)                                         # 요청 간격
  if (is.null(x)) return(NULL)
  
  px <- Ad(x)
  colnames(px) <- code
  saveRDS(px, f)
  px
}

# 2. 여러 종목을 한 표(xts)로 -------------------------------------------
collect_prices <- function(codes, suffix = ".KS", max_n = 20, ...) {
  codes <- head(codes, max_n)                          # 한 번에 받는 개수 상한
  lst <- lapply(codes, function(cd) {
    message("가격 수집: ", cd)
    get_adj_close(cd, suffix = suffix, ...)
  })
  lst <- Filter(Negate(is.null), lst)
  if (length(lst) == 0) return(NULL)
  do.call(merge, lst)
}


# ---------------------------------------------------------------------
# B. DART 호출 도구 (호출 제한 포함)
# ---------------------------------------------------------------------

DART_BASE      <- "https://opendart.fss.or.kr/api"
DART_MAX_CALLS <- 200L      # 한 번 실행(세션)에서 허용할 최대 호출 수
DART_WAIT      <- 0.6       # 호출 사이 대기(초)

.dart <- new.env()
.dart$calls <- 0L

dart_key <- function() {
  k <- Sys.getenv("DART_API_KEY")
  if (k == "") stop("DART_API_KEY가 .Renviron에 설정되지 않았습니다.")
  k
}

# 호출 카운트와 대기를 한곳에서 관리
dart_throttle <- function() {
  if (.dart$calls >= DART_MAX_CALLS)
    stop("이번 실행의 호출 상한(", DART_MAX_CALLS, ")에 도달했습니다. 캐시를 쓰고 나중에 이어서 실행하세요.")
  Sys.sleep(DART_WAIT)
  .dart$calls <- .dart$calls + 1L
}

dart_get <- function(endpoint, query = list()) {
  dart_throttle()
  res <- tryCatch(
    GET(paste0(DART_BASE, "/", endpoint),
        query = c(list(crtfc_key = dart_key()), query), timeout(20)),
    error = function(e) NULL
  )
  if (is.null(res) || status_code(res) != 200) {
    message("DART 요청 실패: ", endpoint); return(NULL)
  }
  x <- fromJSON(content(res, as = "text", encoding = "UTF-8"))
  if (identical(x$status, "020"))                      # 서버가 알려주는 한도 초과
    stop("DART 호출 한도 초과(020). 즉시 중단합니다.")
  x
}

# 3. 기업 고유번호 표 (종목코드 <-> corp_code) --------------------------
get_corp_codes <- function(cache = "data/dart_corp_codes.rds") {
  if (file.exists(cache)) return(readRDS(cache))
  dir.create("data", showWarnings = FALSE)
  
  dart_throttle()
  tmp <- tempfile(fileext = ".zip")
  res <- GET(paste0(DART_BASE, "/corpCode.xml"),
             query = list(crtfc_key = dart_key()),
             write_disk(tmp, overwrite = TRUE), timeout(60))
  stopifnot(status_code(res) == 200)
  
  files <- unzip(tmp, exdir = tempdir())
  doc   <- read_xml(files[1])
  nodes <- xml_find_all(doc, "//list")
  
  pick <- function(tag) trimws(xml_text(xml_find_first(nodes, tag)))
  df <- tibble(
    corp_code  = pick("corp_code"),
    corp_name  = pick("corp_name"),
    stock_code = pick("stock_code")
  ) |> filter(stock_code != "")                        # 상장사만
  
  saveRDS(df, cache)
  df
}

# 4. 공시 검색 -----------------------------------------------------------
search_disclosures <- function(corp_code, bgn_de, end_de, page_count = 20) {
  x <- dart_get("list.json", list(corp_code = corp_code,
                                  bgn_de = bgn_de, end_de = end_de,
                                  page_no = 1, page_count = page_count))
  if (is.null(x) || !identical(x$status, "000")) return(tibble())
  as_tibble(x$list) |> select(any_of(c("rcept_dt", "corp_name", "report_nm", "rcept_no")))
}


# ---------------------------------------------------------------------
# C. 재무제표 수집
# ---------------------------------------------------------------------

# reprt_code: 11011 사업보고서, 11012 반기, 11013 1분기, 11014 3분기
get_dart_fs <- function(corp_code, year, reprt = "11011",
                        cache_dir = "data/dart") {
  dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)
  f <- file.path(cache_dir, sprintf("%s_%s_%s.rds", corp_code, year, reprt))
  if (file.exists(f)) return(readRDS(f))
  
  for (div in c("CFS", "OFS")) {                       # 연결 -> 없으면 별도
    x <- dart_get("fnlttSinglAcntAll.json",
                  list(corp_code = corp_code, bsns_year = year,
                       reprt_code = reprt, fs_div = div))
    if (!is.null(x) && identical(x$status, "000")) {
      df <- as_tibble(x$list) |> mutate(fs_div = div)
      saveRDS(df, f)
      return(df)
    }
  }
  saveRDS(tibble(), f)                                 # '없음'도 캐시해서 재호출 방지
  tibble()
}


# ---------------------------------------------------------------------
# D. 가치지표 계산
# ---------------------------------------------------------------------

# 계정명은 회사마다 조금씩 다름 -> 후보 패턴을 순서대로 시도
pick_amount <- function(fs, sj, patterns) {
  d <- fs |> filter(sj_div %in% sj)
  for (p in patterns) {
    hit <- d |> filter(grepl(p, account_nm))
    if (nrow(hit) > 0)
      return(as.numeric(gsub(",", "", hit$thstrm_amount[1])))
  }
  NA_real_
}

# 시가총액은 '원' 단위로 맞춰서 넣기 (억원이면 * 1e8)
calc_value <- function(fs, mktcap_won) {
  ni  <- pick_amount(fs, c("IS", "CIS"), c("^당기순이익", "^연결당기순이익", "당기순이익"))
  eq  <- pick_amount(fs, "BS", c("^자본총계"))
  rev <- pick_amount(fs, c("IS", "CIS"), c("^매출액", "^수익\\(매출액\\)", "^영업수익"))
  
  tibble(
    net_income = ni, equity = eq, revenue = rev,
    PER = ifelse(!is.na(ni)  & ni  > 0, mktcap_won / ni,  NA_real_),
    PBR = ifelse(!is.na(eq)  & eq  > 0, mktcap_won / eq,  NA_real_),
    PSR = ifelse(!is.na(rev) & rev > 0, mktcap_won / rev, NA_real_)
  )
}

# 여러 종목 일괄 계산 (상한 포함)
collect_value <- function(stock_codes, mktcap_won, year, max_n = 30) {
  corp <- get_corp_codes()
  n <- min(length(stock_codes), max_n)
  out <- vector("list", n)
  
  for (i in seq_len(n)) {
    cd <- corp$corp_code[match(stock_codes[i], corp$stock_code)]
    if (is.na(cd)) next
    message(sprintf("[%d/%d] %s", i, n, stock_codes[i]))
    fs <- get_dart_fs(cd, year)
    if (nrow(fs) == 0) next
    out[[i]] <- calc_value(fs, mktcap_won[i]) |> mutate(stock_code = stock_codes[i])
  }
  bind_rows(out)
}


# ---------------------------------------------------------------------
# 실행 예 (한 단계씩 주석을 풀어 실행)
# ---------------------------------------------------------------------
# px <- collect_prices(c("005930", "000660", "035420"), suffix = ".KS", max_n = 3)
# tail(px)
#
# corp <- get_corp_codes()
# head(corp)
#
# fs <- get_dart_fs(corp$corp_code[corp$stock_code == "005930"], year = 2025)
# calc_value(fs, mktcap_won = 400e12)       # 시가총액은 직접 입력(원 단위)
#
# search_disclosures(corp$corp_code[corp$stock_code == "005930"],
#                    bgn_de = "20261001", end_de = "20261028")
#
# cat("이번 실행 DART 호출 수:", .dart$calls, "\n")


# =====================================================================
# DART 응답과 같은 모양의 JSON 문자열에서 PER, PBR, PSR을 계산하기
# 시가총액은 7,200억원 (원 단위로 변환해서 사용)
# =====================================================================

mock_json <- '{
  "status": "000",
  "list": [
    {"sj_div": "BS", "account_nm": "자본총계",   "thstrm_amount": "500,000,000,000"},
    {"sj_div": "IS", "account_nm": "매출액",     "thstrm_amount": "900,000,000,000"},
    {"sj_div": "IS", "account_nm": "당기순이익", "thstrm_amount": "60,000,000,000"}
  ]
}'

x  <- fromJSON(mock_json)
fs <- as_tibble(x$list)

mktcap_won <- 7200 * 1e8                      # 억원 -> 원
res <- calc_value(fs, mktcap_won)
res
# 기대 결과: PER = 12, PBR = 1.44, PSR = 0.8

stopifnot(isTRUE(all.equal(res$PER, 12)),
          isTRUE(all.equal(res$PBR, 1.44)),
          isTRUE(all.equal(res$PSR, 0.8)))