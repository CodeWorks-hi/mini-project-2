# pages/dashboard.py
# ----------------------------
# 실적 대시보드
# - KPI 지표, 추이 차트 등 요약 정보를 시각화
# - 홈 진입 후 가장 먼저 확인하는 요약 정보
# ----------------------------

import streamlit as st

def dashboard_ui():
    st.title("📈 실적 대시보드")
    st.info("여기에 KPI, 월간 추이, 차트 등의 주요 요약 정보가 시각화될 예정입니다.")

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 누적 판매량", "23,500대", "+12%")
    col2.metric("🚚 재고 보유량", "7,200대", "-5%")
    col3.metric("🌍 수출 비중", "61%", "+3%")

    st.bar_chart(data=[])
