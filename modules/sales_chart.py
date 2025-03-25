# modules/sales_chart.py

import streamlit as st
import pandas as pd
import altair as alt

def show_sales_charts(df: pd.DataFrame):
    """
    판매 데이터 기반 월별 판매 추이 시각화
    """
    st.subheader("📈 월별 판매 추이")

    if df.empty:
        st.info("판매 데이터가 없습니다.")
        return

    # 월 컬럼 자동 감지
    month_cols = [col for col in df.columns if '월' in col]
    if not month_cols:
        st.warning("월별 수량 정보가 없습니다.")
        return

    monthly_total = df[month_cols].sum().reset_index()
    monthly_total.columns = ['월', '수량']

    chart = alt.Chart(monthly_total).mark_line(point=True).encode(
        x='월:N',
        y=alt.Y('수량:Q', title='판매량'),
        tooltip=['월', '수량']
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)
