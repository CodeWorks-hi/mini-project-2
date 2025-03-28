import streamlit as st
import pandas as pd
import altair as alt

#                       ---------
#                      | 재고 관리 |
#                       ---------


# 모듈화된 기능 함수들
# -----------------------------------
# 1. 데이터 전처리 함수로 분리
#    예시: 생산/판매 데이터를 불러오고 처리하는 부분
def load_inventory_data():
    # 생산 데이터
    hyundai_prod = pd.read_csv("data/processed/hyundai-by-plant.csv")
    kia_prod = pd.read_csv("data/processed/kia-by-plant.csv")
    hyundai_prod["브랜드"] = "현대"
    kia_prod["브랜드"] = "기아"
    prod_df = pd.concat([hyundai_prod, kia_prod], ignore_index=True)

    # 판매 데이터
    hyundai_sales = pd.read_csv("data/processed/hyundai-by-car.csv")
    kia_sales = pd.read_csv("data/processed/kia-by-car.csv")
    hyundai_sales["브랜드"] = "현대"
    kia_sales["브랜드"] = "기아"
    sales_df = pd.concat([hyundai_sales, kia_sales], ignore_index=True)

    return prod_df, sales_df
# -----------------------------------

# 2. 재고 계산 함수
def calculate_inventory(prod_df, sales_df):
    month_cols_prod = [col for col in prod_df.columns if "-" in col and col[:4].isdigit()]
    prod_df[month_cols_prod] = prod_df[month_cols_prod].apply(pd.to_numeric, errors='coerce')
    prod_long = prod_df.melt(
        id_vars=[col for col in prod_df.columns if col not in month_cols_prod],
        var_name="연월",
        value_name="생산량"
    )
    prod_long["연도"] = prod_long["연월"].str[:4].astype(int)
    prod_sum = prod_long.groupby(["브랜드", "차종", "연도"])["생산량"].sum().reset_index()
    prod_sum["누적생산"] = prod_sum["생산량"]

    month_cols_sales = [col for col in sales_df.columns if "-" in col and col[:4].isdigit()]
    sales_df[month_cols_sales] = sales_df[month_cols_sales].apply(pd.to_numeric, errors='coerce')
    sales_long = sales_df.melt(
        id_vars=[col for col in sales_df.columns if col not in month_cols_sales],
        var_name="연월",
        value_name="판매량"
    )
    sales_long["연도"] = sales_long["연월"].str[:4].astype(int)
    sales_sum = sales_long.groupby(["브랜드", "차종", "연도"])["판매량"].sum().reset_index()
    sales_sum["누적판매"] = sales_sum["판매량"]

    inventory_df = pd.merge(
        prod_sum[["브랜드", "차종", "연도", "누적생산"]],
        sales_sum[["브랜드", "차종", "연도", "누적판매"]],
        on=["브랜드", "차종", "연도"],
        how="outer"
    ).fillna(0)
    inventory_df["재고변동"] = inventory_df["누적생산"] - inventory_df["누적판매"]
    return inventory_df
# -----------------------------------

# 3. KPI 계산 함수
# 3-1 총 누적량 관련 KPI
def get_kpi_summary(filtered_df):
    total_prod = int(filtered_df["누적생산"].sum())
    total_sales = int(filtered_df["누적판매"].sum())
    total_stock = int(filtered_df["재고변동"].sum())
    low_count = filtered_df[filtered_df["재고변동"] < 100]["차종"].nunique()
    high_count = filtered_df[filtered_df["재고변동"] > 10000]["차종"].nunique()
    return total_prod, total_sales, total_stock, low_count, high_count


# -----------------------------------

# 4. 연도별 재고 총합 추이 (선형 추이) - 차트 
# 목적: 연도별 전체 재고의 변화 흐름 파악 (시간 흐름에 따라 증가/감소)
# 4-1. 연도별 재고 총합 추이
def draw_inventory_trend_chart(inventory_df, brand_sel):
    df = inventory_df.copy()
    if brand_sel != "전체":
        df = df[df["브랜드"] == brand_sel]
    trend = df.groupby("연도")["재고변동"].sum().reset_index()

    return alt.Chart(trend).mark_line(point=True).encode(
        x=alt.X("연도:O", title="연도",axis=alt.Axis(labelAngle=-0)),
        y=alt.Y("재고변동:Q", title="총 재고량", axis=alt.Axis(format=",d")),
        tooltip=["연도", alt.Tooltip("재고변동", format=",")]
    ).properties(title="연도별 재고 추이", height=350)

# 4-2. 재고 수준 분포 히스토그램
def draw_inventory_distribution_chart(filtered_df):
    return alt.Chart(filtered_df).mark_bar().encode(
        x=alt.X("재고변동:Q", bin=alt.Bin(maxbins=30), title="재고변동 분포"),
        y=alt.Y("count()", title="차종 수"),
        tooltip=[alt.Tooltip("count()", title="차종 수")]
    ).properties(title="재고량 분포", height=350)


# -----------------------------------
# 🖥️ 메인 UI 함수
# -----------------------------------

def inventory_ui():
    prod_df, sales_df = load_inventory_data()
    inventory_df = calculate_inventory(prod_df, sales_df)

  
    # KPI + 필터 전체를 하나의 카드 스타일 박스로 감싸기


    # 컬럼 구성
    col1, col2, col3 = st.columns([4, 1.5, 1.5])

    # ✅ 필터 UI - 브랜드
    with col2:
        st.markdown("####브랜드 필터")
        brand_list = ["전체"] + inventory_df["브랜드"].dropna().unique().tolist()
        brand_sel = st.selectbox("브랜드 선택", brand_list, key="inventory_brand")

    # ✅ 필터 UI - 연도
    with col3:
        st.markdown("#### 연도 필터")
        available_years = sorted(inventory_df["연도"].dropna().unique(), reverse=True)
        year_sel = st.selectbox("연도 선택", available_years, key="inventory_year")


    # 필터링
    filtered = inventory_df[inventory_df["연도"] == year_sel]
    if brand_sel != "전체":
        filtered = filtered[filtered["브랜드"] == brand_sel]
    
    # ✅ KPI 카드
    with col1:
        st.markdown("#### 주요 지표")
        prod, sales, stock, low, high = get_kpi_summary(filtered)
        k1, k2, k3 = st.columns(3)
        k1.metric("총 생산량", f"{prod:,} 대")
        k2.metric("총 판매량", f"{sales:,} 대")
        k3.metric("총 재고량", f"{stock:,} 대")
        
        k4, k5, k6 = st.columns(3)
        k4.metric("재고 부족 차종", f"{low} 종")
        k5.metric("재고 과잉 차종", f"{high} 종")
        k6
    st.markdown("</div>", unsafe_allow_html=True)


    # 구분선
    st.markdown("---")
  

    # 차트 구현
    col1, col2, = st.columns(2)
    with col1:
        st.altair_chart(draw_inventory_trend_chart(inventory_df, brand_sel), use_container_width=True)
    with col2:
        st.altair_chart(draw_inventory_distribution_chart(filtered), use_container_width=True)

    
    # 전체 필터 결과 테이블
    
    filtered_sorted = filtered.sort_values("재고변동").reset_index(drop=True)

    # 재고 랭킹
    
    top10 = filtered.sort_values("재고변동", ascending=False).head(10).reset_index(drop=True)
    bottom10 = filtered.sort_values("재고변동").head(10).reset_index(drop=True)
    with st.expander(" 재고 상세 데이터 보기", expanded=False):
        col1, col2, col3 = st.columns([3, 2, 2])
        
        with col1:
            with st.container():
                st.subheader("필터 결과 상세 데이터")
        
                st.dataframe(filtered_sorted, use_container_width=True, hide_index=True)
    
        
        with st.container():
            with col2:
                st.subheader("재고 과잉 차종")
                st.dataframe(top10[["브랜드", "차종", "연도", "재고변동"]], use_container_width=True, hide_index=True)
            with col3:
                st.subheader("재고 부족 차종")
                st.dataframe(bottom10[["브랜드", "차종", "연도", "재고변동"]], use_container_width=True, hide_index=True)




