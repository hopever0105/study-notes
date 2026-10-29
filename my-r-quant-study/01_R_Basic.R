# =====================================================================
#  R 기초와 환경 설정
# 목적: 퀀트 분석에 필요한 R 기본 문법 정리
# 실행: RStudio에서 Ctrl+Shift+Enter (전체) / Ctrl+Enter (한 줄)
# =====================================================================


# 1. 작업 환경 확인 ----------------------------------------------------
getwd()        # 현재 작업 폴더. RStudio Project를 쓰면 프로젝트 폴더로 고정됨
sessionInfo()  # R 버전과 로드된 패키지 확인


# 2. 변수와 기본 자료형 ------------------------------------------------
price <- 71500       # numeric
name  <- "삼성전자"   # character
is_up <- TRUE        # logical

class(price); class(name); class(is_up)


# 3. 벡터 --------------------------------------------------------------
# 같은 자료형을 묶은 R의 기본 단위. R의 인덱스는 1부터 시작
close <- c(100, 102, 101, 105, 110)

close[1]             # 첫 번째 값
close[2:4]           # 2~4번째
close[close > 103]   # 조건에 맞는 값만
close * 2            # 벡터 전체에 한 번에 연산
diff(close)          # 이전 값과의 차이

# 일간 수익률 = (오늘 - 어제) / 어제
ret <- diff(close) / head(close, -1)
round(ret, 4)


# 4. 리스트 ------------------------------------------------------------
# 서로 다른 자료형을 한 번에 담음. API(JSON) 응답이 이 형태로 들어옴
stock <- list(code = "005930", name = "삼성전자", prices = c(70000, 71500))

stock$name
stock[["prices"]]


# 5. 데이터프레임 ------------------------------------------------------
# 엑셀 표와 비슷한 구조. 열마다 자료형이 다를 수 있음
df <- data.frame(
  date  = as.Date(c("2026-10-26", "2026-10-27", "2026-10-28")),
  close = c(70000, 71000, 70500),
  vol   = c(1000, 1500, 1200)
)

str(df)                # 구조 확인
df$close               # 열 선택
df[df$vol > 1100, ]    # 행 필터링
df$ret <- c(NA, diff(df$close) / head(df$close, -1))   # 열 추가
summary(df)


# 6. 조건문과 반복문 ---------------------------------------------------
x <- 0.03
if (x > 0.02) {
  print("강한 상승")
} else if (x > 0) {
  print("약한 상승")
} else {
  print("하락")
}

for (i in 1:3) {
  cat("반복", i, "\n")
}

# R에서는 for보다 벡터 연산 / apply 계열을 우선 고려
nums <- list(a = 1:5, b = c(10, 20, 30))
sapply(nums, mean)   # 각 원소에 함수 적용 -> 벡터
lapply(nums, range)  # 각 원소에 함수 적용 -> 리스트


# 7. 함수 만들기 -------------------------------------------------------
calc_return <- function(p0, p1) {
  (p1 - p0) / p0
}
calc_return(100, 110)   # 0.1

# 기본값이 있는 인자
cum_ret <- function(ret, as_pct = FALSE) {
  r <- prod(1 + ret) - 1
  if (as_pct) r * 100 else r
}
cum_ret(c(0.01, -0.02, 0.03), as_pct = TRUE)


# 8. 파이프 ------------------------------------------------------------
# |> 는 R 4.1 이상의 기본 파이프. 앞의 결과를 다음 함수의 첫 인자로 전달
c(1, 4, 9, 16) |> sqrt() |> sum()


# 9. 패키지 설치와 로드 ------------------------------------------------
# 설치는 한 번, library()는 세션마다
pkgs <- c("dplyr", "tidyr", "lubridate", "httr", "jsonlite",
          "rvest", "xts", "quantmod", "PerformanceAnalytics")
to_install <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(to_install) > 0) install.packages(to_install)

library(dplyr)

trade <- data.frame(
  ticker = c("A", "A", "B", "B"),
  ret    = c(0.01, 0.02, -0.01, 0.03)
)

trade |>
  group_by(ticker) |>
  summarise(avg = mean(ret), n = n())


# =====================================================================
# 5일치 가상 종가 벡터로 일간 수익률과 누적 수익률을 구하는 함수 만들기
# =====================================================================

calc_returns <- function(close) {
  daily <- diff(close) / head(close, -1)   # 일간 수익률
  cum   <- prod(1 + daily) - 1             # 누적 수익률
  list(daily = daily, cumulative = cum)
}

close_5d <- c(100, 102, 101, 105, 110)
res <- calc_returns(close_5d)

round(res$daily, 4)    # 0.0200 -0.0098  0.0396  0.0476
res$cumulative         # 0.1  (= 110/100 - 1)

# 검증: 누적 수익률은 처음과 마지막 가격만으로도 계산 가능
stopifnot(isTRUE(all.equal(res$cumulative, tail(close_5d, 1) / close_5d[1] - 1)))

# ====================================================================
# 추가적인 기초사항
# =====================================================================

pkgs <- c("dplyr", "tidyr", "lubridate", "readxl", "writexl", "zoo")
to_install <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(to_install) > 0) install.packages(to_install)

library(dplyr)
library(tidyr)
library(lubridate)


# 1. 날짜 --------------------------------------------------------------
d <- as.Date("2026-10-28")
class(d)                              # "Date"

format(d, "%Y/%m/%d")                 # 출력 형식 바꾸기
as.Date("20261028", format = "%Y%m%d")   # 8자리 숫자 문자열 -> 날짜

d + 30                                # 날짜에 일수 더하기
seq(d, by = "month", length.out = 4)  # 한 달 간격 날짜열
as.numeric(as.Date("2026-12-31") - d) # 두 날짜 사이 일수

# lubridate: 읽기 쉬운 날짜 함수
ymd("20261028")
year(d); month(d); day(d)
wday(d, label = TRUE)                 # 요일
floor_date(d, "month")                # 해당 월의 첫날
ceiling_date(d, "month") - days(1)    # 해당 월의 마지막 날

# 주말 제외한 평일 날짜열 (wday: 일요일=1, 토요일=7)
all_days <- seq(as.Date("2026-10-01"), as.Date("2026-10-31"), by = "day")
weekdays_only <- all_days[wday(all_days) %in% 2:6]
length(weekdays_only)


# 2. 문자열 ------------------------------------------------------------
code <- 5930
sprintf("%06d", code)                 # "005930": 종목코드 6자리 맞추기

s <- "Samsung Electronics"
nchar(s); toupper(s); tolower(s)
substr(s, 1, 7)
paste("종목:", s)                      # 공백 포함 연결
paste0("A", 1:3)                      # 공백 없이 연결 -> "A1" "A2" "A3"
strsplit("2026-10-28", "-")[[1]]      # 구분자로 쪼개기
gsub("-", "", "2026-10-28")           # 치환
grepl("Elec", s)                      # 포함 여부 -> TRUE
sprintf("%.2f%%", 0.0345 * 100)       # "3.45%"


# 3. 숫자 형식 ---------------------------------------------------------
x <- 1234567.8912
round(x, 2); floor(x); ceiling(x); signif(x, 3)
format(x, big.mark = ",", nsmall = 2)       # 천 단위 쉼표 표시용


# 4. 결측치(NA) --------------------------------------------------------
v <- c(1, NA, 3, NA, 5)

is.na(v)                              # 위치 확인
sum(is.na(v))                         # 개수
mean(v)                               # NA가 있으면 결과도 NA
mean(v, na.rm = TRUE)                 # NA 제외하고 계산
v[!is.na(v)]                          # NA 제거
replace(v, is.na(v), 0)               # 0으로 대체
zoo::na.locf(v, na.rm = FALSE)        # 직전 값으로 채우기: 1 1 3 3 5

df_na <- data.frame(a = c(1, NA, 3), b = c("x", "y", NA))
complete.cases(df_na)                 # 완전한 행만 TRUE
drop_na(df_na)                        # NA 있는 행 삭제
replace_na(df_na, list(a = 0, b = "없음"))   # 열별로 다른 값으로 대체
coalesce(df_na$a, 99)                 # 첫 번째 non-NA 값


# 5. 파일 입출력 -------------------------------------------------------
dir.create("data", showWarnings = FALSE)

sample_df <- data.frame(
  ticker = c("A", "B", "C"),
  sector = c("IT", "금융", "IT"),
  per    = c(10.5, 7.2, 15.1)
)

# CSV
write.csv(sample_df, "data/sample.csv", row.names = FALSE, fileEncoding = "UTF-8")
read.csv("data/sample.csv", fileEncoding = "UTF-8")
# 한글 CSV를 엑셀에서 열 때 깨지면 EUC-KR(CP949)로 저장
# write.csv(sample_df, "data/sample_cp949.csv", row.names = FALSE, fileEncoding = "CP949")

# 엑셀 (시트 여러 개 저장 가능)
writexl::write_xlsx(list(stocks = sample_df), "data/sample.xlsx")
readxl::read_excel("data/sample.xlsx", sheet = "stocks")

# R 전용 형식 (자료형이 그대로 보존됨)
saveRDS(sample_df, "data/sample.rds")
readRDS("data/sample.rds")


# 6. tidyr: 표 모양 바꾸기 ---------------------------------------------
wide <- data.frame(
  date = as.Date(c("2026-10-26", "2026-10-27")),
  A = c(100, 102),
  B = c(50, 49)
)

# 넓은 표 -> 긴 표 (분석, ggplot에 유리)
long <- pivot_longer(wide, cols = -date,
                     names_to = "ticker", values_to = "close")
long

# 긴 표 -> 넓은 표 (종목을 열로 펼칠 때)
pivot_wider(long, names_from = ticker, values_from = close)

# 열 쪼개기 / 합치기
tmp <- data.frame(id = c("2026-10", "2026-11"))
tmp2 <- separate(tmp, id, into = c("year", "month"), sep = "-")
tmp2
unite(tmp2, "ym", year, month, sep = "")


# 7. dplyr: 자주 쓰는 동사 ---------------------------------------------
stocks <- data.frame(
  ticker = c("A", "B", "C", "D", "E"),
  sector = c("IT", "금융", "IT", "소재", "금융"),
  per    = c(10.5, 7.2, 15.1, 9.0, 6.1),
  pbr    = c(1.2, 0.5, 2.3, 0.8, 0.4),
  cap    = c(500, 300, 800, 200, 400)
)

stocks |> select(ticker, per)                       # 열 선택
stocks |> filter(per < 10, sector == "금융")         # 행 필터
stocks |> mutate(ep = 1 / per)                      # 열 생성
stocks |> arrange(desc(cap))                        # 정렬
stocks |> rename(시가총액 = cap)                     # 이름 변경
stocks |> distinct(sector)                          # 고유값
stocks |> slice_head(n = 2)                         # 위에서 n개

stocks |>
  group_by(sector) |>
  summarise(n = n(), avg_pbr = mean(pbr), total_cap = sum(cap))

# 순위, 분위수, 조건부 라벨
stocks |>
  mutate(
    rank_pbr = row_number(pbr),                     # 오름차순 순위
    quint    = ntile(pbr, 2),                       # 2분위 (예시)
    label    = case_when(pbr < 0.6 ~ "저평가",
                         pbr < 1.5 ~ "보통",
                         TRUE      ~ "고평가")
  )

# 결합 (join)
info <- data.frame(ticker = c("A", "B", "C"), name = c("에이", "비", "씨"))
left_join(stocks, info, by = "ticker")   # stocks 기준으로 이름 붙이기


# =====================================================================
# 가상의 긴 형태 가격 데이터(결측 포함)를 다음 순서로 처리하기
#  (1) 넓은 표로 펼치기  (2) 결측을 직전 값으로 채우기
#  (3) 다시 긴 표로 바꿔 종목별 일간 수익률 계산
#  (4) 종목별 누적 수익률 요약  (5) 엑셀(시트 2개)로 저장
# =====================================================================

dates <- seq(as.Date("2026-10-19"), as.Date("2026-10-30"), by = "day")
dates <- dates[wday(dates) %in% 2:6]
n <- length(dates)

set.seed(42)
px <- data.frame(
  date   = rep(dates, times = 3),
  ticker = rep(c("A", "B", "C"), each = n),
  close  = round(100 + c(cumsum(rnorm(n)), cumsum(rnorm(n)), cumsum(rnorm(n))), 2)
)
px$close[c(3, 15)] <- NA             # 결측 만들기

# (1) 넓은 표
wide_px <- px |>
  pivot_wider(names_from = ticker, values_from = close) |>
  arrange(date)

# (2) 직전 값으로 채우기 (첫 행이 NA면 남을 수 있어 na.rm = FALSE)
wide_filled <- wide_px |>
  mutate(across(-date, ~ zoo::na.locf(.x, na.rm = FALSE)))

# (3) 긴 표 + 종목별 일간 수익률
long_ret <- wide_filled |>
  pivot_longer(-date, names_to = "ticker", values_to = "close") |>
  arrange(ticker, date) |>
  group_by(ticker) |>
  mutate(ret = close / lag(close) - 1) |>
  ungroup()

# (4) 종목별 누적 수익률
summary_tbl <- long_ret |>
  group_by(ticker) |>
  summarise(cum_ret = prod(1 + ret, na.rm = TRUE) - 1)
summary_tbl

# (5) 저장
dir.create("output", showWarnings = FALSE)
writexl::write_xlsx(list(prices = wide_filled, returns = long_ret),
                    "output/ch01b_result.xlsx")