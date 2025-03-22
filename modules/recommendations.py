# pages/recommendations.py
# ----------------------------
# AI 추천 시스템
# - 차량 수요 예측, 고객별 추천 등 ML 기반 기능
# - 추천 결과 시각화 포함 예정
# ----------------------------

import streamlit as st

def recommendations_ui():
    st.title("🤖 AI 추천 시스템")
    st.info("여기에 차량 수요 예측 또는 모델 추천 결과가 표시될 예정입니다.")

    st.button("🔍 추천 실행")
    st.dataframe([], use_container_width=True)
