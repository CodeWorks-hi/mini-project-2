# pages/analytics.py
# ----------------------------
# 분석 리포트 페이지
# - 다양한 시각화 기반 비교 분석, 추이 분석
# - 차종, 지역, 기간별 분석 중심
# ----------------------------

import streamlit as st

def analytics_ui():
    st.title("📊 분석 리포트")
    st.info("여기에 판매 분석, 비교 분석, 시계열 분석 등의 리포트가 시각화될 예정입니다.")

    st.selectbox("분석 유형 선택", ["차종별 분석", "지역별 분석", "기간별 분석"])
    st.dataframe([], use_container_width=True)
