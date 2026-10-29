# =====================================================================
# API로 데이터 수집하기
# 목적: REST API 호출, JSON 변환, 반복/재시도/페이지네이션
# 예제 API: jsonplaceholder (인증키 불필요한 연습용)
# =====================================================================

library(httr)
library(jsonlite)
library(dplyr)


# 1. 기본 호출 흐름 ----------------------------------------------------
# 요청 -> 상태 확인 -> 본문 텍스트 -> JSON을 R 객체로
res <- GET("https://jsonplaceholder.typicode.com/posts",
           query = list(userId = 1))

stop_for_status(res)    # 200대가 아니면 에러로 중단

body_txt <- content(res, as = "text", encoding = "UTF-8")
df <- fromJSON(body_txt)   # 같은 모양의 객체 배열 -> 데이터프레임

str(df)
head(df[, c("id", "title")])


# 2. 중첩된 JSON ------------------------------------------------------
json_txt <- '{"status":"ok","data":[{"date":"2026-10-27","close":71000},
                                     {"date":"2026-10-28","close":70500}]}'
x <- fromJSON(json_txt)
x$status
x$data                 # 데이터프레임
mean(x$data$close)
# 구조가 복잡하면 str(x)로 모양부터 확인하고 $ 로 한 층씩 내려간다


# 3. API 키 관리 -------------------------------------------------------
# 키를 코드에 직접 쓰지 않는다 (GitHub에 올리면 유출)
# 1회: ~/.Renviron 파일에 한 줄 추가 후 R 재시작
#      (usethis::edit_r_environ() 로 파일 열기)
#   MY_API_KEY=발급받은키
#
# api_key <- Sys.getenv("MY_API_KEY")
# if (api_key == "") stop("API 키가 설정되지 않았습니다.")


# 4. 재시도가 있는 호출 함수 -------------------------------------------
fetch_json <- function(url, query = list(), max_try = 3, wait = 1) {
  for (i in seq_len(max_try)) {
    res <- tryCatch(GET(url, query = query, timeout(10)),
                    error = function(e) NULL)
    
    if (!is.null(res) && status_code(res) == 200) {
      return(fromJSON(content(res, as = "text", encoding = "UTF-8")))
    }
    
    message("시도 ", i, " 실패 (상태: ",
            ifelse(is.null(res), "연결오류", status_code(res)), ")")
    Sys.sleep(wait * i)    # 실패할수록 더 오래 대기
  }
  NULL                     # 끝내 실패하면 NULL
}

posts <- fetch_json("https://jsonplaceholder.typicode.com/posts",
                    query = list(userId = 2))
nrow(posts)


# 5. 여러 건 반복 수집 -------------------------------------------------
ids <- 1:3

result <- lapply(ids, function(id) {
  d <- fetch_json("https://jsonplaceholder.typicode.com/posts",
                  query = list(userId = id))
  Sys.sleep(0.5)                       # 호출 간격
  if (!is.null(d)) d$userId <- id
  d
})

all_df <- bind_rows(result)   # NULL(실패 건)은 자동으로 건너뜀
table(all_df$userId)


# 6. 페이지네이션 ------------------------------------------------------
# 빈 응답이면 종료 + max_page 상한으로 무한 루프 방지
fetch_all_pages <- function(base_url, per_page = 20, max_page = 50) {
  out <- list()
  for (p in 1:max_page) {
    d <- fetch_json(base_url,
                    query = list(`_page` = p, `_limit` = per_page))
    if (is.null(d) || nrow(d) == 0) break
    out[[p]] <- d
    Sys.sleep(0.5)
  }
  bind_rows(out)
}

comments <- fetch_all_pages("https://jsonplaceholder.typicode.com/comments",
                            per_page = 100, max_page = 3)
nrow(comments)


# 7. 저장 --------------------------------------------------------------
dir.create("data", showWarnings = FALSE)

saveRDS(all_df, "data/posts.rds")    # R 전용, 자료형 보존
write.csv(all_df, "data/posts.csv", row.names = FALSE, fileEncoding = "UTF-8")

all_df2 <- readRDS("data/posts.rds")


# =====================================================================
# fetch_all_pages를 고쳐서 특정 조건에서만 수집을 중단하도록 만들기
# 아이디어: 호출하는 쪽이 "중단 조건 함수(stop_when)"를 넘기게 한다
# =====================================================================

fetch_pages_until <- function(base_url,
                              per_page  = 20,
                              max_page  = 50,
                              stop_when = function(d) FALSE) {
  out <- list()
  for (p in seq_len(max_page)) {
    d <- fetch_json(base_url,
                    query = list(`_page` = p, `_limit` = per_page))
    if (is.null(d) || nrow(d) == 0) break       # 데이터가 끝난 경우
    
    out[[p]] <- d
    if (stop_when(d)) {                         # 사용자가 정한 조건에서 중단
      message("조건 충족, ", p, "페이지에서 수집 종료")
      break
    }
    Sys.sleep(0.5)
  }
  bind_rows(out)
}

# 사용 예: 한 페이지에서 id가 250 이상인 행이 나오면 거기서 멈춤
got <- fetch_pages_until(
  "https://jsonplaceholder.typicode.com/comments",
  per_page  = 100,
  max_page  = 10,
  stop_when = function(d) max(d$id) >= 250
)

nrow(got)                 # 300 (3페이지까지 수집)
got <- got |> filter(id <= 250)    # 필요하면 조건에 맞게 잘라낸다
nrow(got)                 # 250