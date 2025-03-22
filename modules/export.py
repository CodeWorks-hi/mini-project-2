# modules/export.py
# ----------------------------
# 수출 관리 모듈
# - 국가별/지역별 수출 실적 관리
# - 수출 일정 및 국가 정책 분석 기반 확장 가능
# ----------------------------

import streamlit as st

def export_ui():
    st.title("🌍 수출 관리")
    st.info("여기에 수출 일정, 지역별 수출 실적, 국가별 요약 기능이 들어갈 예정입니다.")
    st.button("+ 수출 데이터 등록")
    st.dataframe([], use_container_width=True)
