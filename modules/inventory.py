import streamlit as st
import pandas as pd
import altair as alt

# 재고 관리
def inventory_ui():
    # 생산 데이터 로드
    hyundai_prod = pd.read_csv("data/세일즈파일/00_해외공장판매실적.CSV")
    kia_prod = pd.read_csv("data/세일즈파일/00_해외공장판매실적.CSV")
    hyundai_prod["브랜드"] = "현대"
    kia_prod["브랜드"] = "기아"
    prod_df = pd.concat([hyundai_prod, kia_prod], ignore_index=True)

    # 판매 데이터 로드
    hyundai_sales = pd.read_csv("data/processed/현대_차종별판매실적_전처리.CSV")
    kia_sales = pd.read_csv("data/processed/기아_차종별판매실적_전처리.CSV")
    hyundai_sales["브랜드"] = "현대"
    kia_sales["브랜드"] = "기아"
    sales_df = pd.concat([hyundai_sales, kia_sales], ignore_index=True)

    # 공통 처리
    month_cols = [f"{i}월" for i in range(1, 13)]
    prod_df[month_cols] = prod_df[month_cols].apply(pd.to_numeric, errors='coerce')
    # 연-월 형식으로 되어 있는 컬럼만 선택
    month_cols = [col for col in sales_df.columns if "-" in col and col[:4].isdigit()]
    sales_df[month_cols] = sales_df[month_cols].apply(pd.to_numeric, errors='coerce')

    id_cols = [col for col in prod_df.columns if not "-" in col or not col[:4].isdigit()]
    prod_long = prod_df.melt(
        id_vars=id_cols,
        var_name="연월",
        value_name="생산량"
    )

    # 2. 연도 및 월 파생
    prod_long["연도"] = prod_long["연월"].str[:4].astype(int)
    prod_long["월"] = prod_long["연월"].str[5:].astype(int)

    # 3. groupby 수행
    prod_sum = prod_long.groupby(["브랜드", "차종", "연도"])["생산량"].sum().reset_index()
    prod_sum["누적생산"] = prod_sum.sum(axis=1)

    id_cols = [col for col in sales_df.columns if not "-" in col or not col[:4].isdigit()]
    sales_long = sales_df.melt(id_vars=id_cols, var_name="연월", value_name="판매량")
    sales_long["연도"] = sales_long["연월"].str[:4].astype(int)
    sales_long["월"] = sales_long["연월"].str[5:].astype(int)

    sales_sum = sales_long.groupby(["브랜드", "차종", "연도"])["판매량"].sum().reset_index()
    sales_sum["누적판매"] = sales_sum.sum(axis=1, numeric_only=True)

    # 병합 전, 인덱스 초기화
    prod_sum = prod_sum.reset_index()
    sales_sum = sales_sum.reset_index()

    # 병합 수행
    inventory_df = pd.merge(
        prod_sum[["브랜드", "차종", "연도", "누적생산"]],
        sales_sum[["브랜드", "차종", "연도", "누적판매"]],
        on=["브랜드", "차종", "연도"],
        how="outer"
    ).fillna(0)

    # 재고 계산
    inventory_df["예상재고"] = inventory_df["누적생산"] - inventory_df["누적판매"]
    inventory_df = inventory_df.reset_index()

    # 필터 슬라이서
    st.subheader("🔍 필터 선택")
    col1, col2 = st.columns(2)
    with col1:
        brand_sel = st.selectbox("브랜드 선택", ["전체"] + inventory_df["브랜드"].unique().tolist())
    with col2:
        # 연도 리스트 (정수로 변환)
        available_years = sorted(inventory_df["연도"].dropna().astype(int).unique(), reverse=True)

        # 2025가 있으면 해당 연도를 기본 선택, 없으면 첫 번째 연도 선택
        default_year = 2025 if 2025 in available_years else available_years[0]

        # 연도 선택 필터 UI
        year_sel = st.selectbox("연도 선택", available_years, index=available_years.index(default_year), key="year")

    filtered = inventory_df[inventory_df["연도"] == year_sel]
    if brand_sel != "전체":
        filtered = filtered[filtered["브랜드"] == brand_sel]

    # KPI 요약
    total_prod = int(filtered["누적생산"].sum())
    total_sales = int(filtered["누적판매"].sum())
    total_stock = int(filtered["예상재고"].sum())
    low_count = (filtered["예상재고"] < 100).sum()
    high_count = (filtered["예상재고"] > 10000).sum()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("총 생산량", f"{total_prod:,} 대")
    k2.metric("총 판매량", f"{total_sales:,} 대")
    k3.metric("총 재고량", f"{total_stock:,} 대")
    k4.metric("재고 부족 차종", f"{low_count} 종")
    k5.metric("재고 과잉 차종", f"{high_count} 종")

    # 양방향 재고 바 차트
    st.subheader("📊 예상 재고량 분포 (양방향)")
    chart_data = filtered.copy()
    chart_data["차종 (연도)"] = chart_data["차종"] + " (" + chart_data["연도"].astype(str) + ")"

    base_chart = alt.Chart(chart_data).mark_bar().encode(
        y=alt.Y("예상재고:Q", title="예상 재고량", axis=alt.Axis(format=",d")),
        x=alt.X("차종 (연도):N", sort="-y", title="차종", axis=alt.Axis(
        labelAngle=-50,
        labelLimit=1000,
        labelOverlap=False)),
        color="브랜드:N",
        tooltip=[
            alt.Tooltip("브랜드", title="브랜드"),
            alt.Tooltip("차종", title="차종"),
            alt.Tooltip("연도", title="연도"),
            alt.Tooltip("예상재고", title="예상 재고량", format=",")
        ]
    ).properties(height=700)

    zero_line = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="gray", strokeDash=[4,2]).encode(y="y")

    final_chart = alt.layer(base_chart, zero_line)
    final_chart = final_chart.configure_view(stroke=None).configure_axis(grid=True).interactive()

    st.altair_chart(final_chart, use_container_width=True)

    # 상/하위 랭킹
    st.subheader("📈 재고 Top/Bottom 차종")
    top10 = filtered.sort_values("예상재고", ascending=False).head(10)
    bottom10 = filtered.sort_values("예상재고").head(10)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🔝 재고 많은 차종 TOP 10")
        st.dataframe(top10[["브랜드", "차종", "연도", "예상재고"]], use_container_width=True, hide_index=True)
    with col2:
        st.markdown("#### 🔻 재고 적은 차종 BOTTOM 10")
        st.dataframe(bottom10[["브랜드", "차종", "연도", "예상재고"]], use_container_width=True, hide_index=True)

    # 브랜드 필터별 보기
    st.subheader("📋 필터 결과 상세 데이터")
    st.dataframe(filtered.sort_values("예상재고"), use_container_width=True, hide_index=True)
