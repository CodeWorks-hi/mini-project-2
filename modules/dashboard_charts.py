# modules/dashboard_charts.py
# ----------------------------
# 대시보드용 주요 차트 시각화
# - 월별 생산/판매/수출 추이
# - 재고 상태 경고 요약
# ----------------------------

import streamlit as st
import pandas as pd
import altair as alt

def show_monthly_trend(prod_df, sales_df, export_df, month_cols):
    st.subheader("📊 월별 생산 / 판매 / 수출 추이")
    prod_m = prod_df[month_cols].sum().reset_index(name="생산량").rename(columns={"index": "월"})
    sales_m = sales_df[month_cols].sum().reset_index(name="판매량").rename(columns={"index": "월"})
    export_m = export_df[month_cols].sum().reset_index(name="수출량").rename(columns={"index": "월"})

    merged = prod_m.merge(sales_m, on="월").merge(export_m, on="월")
    melted = merged.melt(id_vars="월", var_name="구분", value_name="수량")

    chart = alt.Chart(melted).mark_line(point=True).encode(
        x=alt.X("월:N", title="월"),
        y=alt.Y("수량:Q", title="수량"),
        color="구분:N"
    ).properties(width=800, height=400)

    st.altair_chart(chart, use_container_width=True)

def show_stock_summary(prod_df, sales_df, month_cols):
    st.subheader("⚠️ 재고 상태 요약")

    inventory_df = pd.merge(
        prod_df.groupby(["브랜드", "차종"])[month_cols].sum().sum(axis=1).rename("누적생산"),
        sales_df.groupby(["브랜드", "차종"])[month_cols].sum().sum(axis=1).rename("누적판매"),
        left_index=True, right_index=True, how="outer"
    ).fillna(0).reset_index()

    inventory_df["예상재고"] = inventory_df["누적생산"] - inventory_df["누적판매"]

    low_stock = inventory_df[inventory_df["예상재고"] < 100]
    high_stock = inventory_df[inventory_df["예상재고"] > 10000]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🔻 재고 부족 차종")
        st.dataframe(low_stock, use_container_width=True, hide_index=True)
    with col2:
        st.markdown("#### 🔺 재고 과잉 차종")
        st.dataframe(high_stock, use_container_width=True, hide_index=True)
