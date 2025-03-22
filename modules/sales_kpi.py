import streamlit as st
from datetime import datetime

SALES_GOAL = 10000  # 향후 설정 값으로 대체 가능

def show_kpi_cards(df):
    today = datetime.now().date().strftime('%Y-%m-%d')
    total_sales = df['수량'].sum()
    today_sales = df[df['판매일'] == today]['수량'].sum()
    top_model = df.groupby('모델명')['수량'].sum().idxmax() if not df.empty else "-"
    goal_rate = round((total_sales / SALES_GOAL) * 100, 1)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 누적 판매량", f"{total_sales:,}대")
    col2.metric("🗓️ 오늘 판매량", f"{today_sales:,}대")
    col3.metric("🚗 최다 판매 모델", top_model)
    col4.metric("🎯 목표 달성률", f"{goal_rate}%")
