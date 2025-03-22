# modules/production.py
# ----------------------------
# 생산 관리 모듈
# - 생산 등록 및 공장별 계획/현황 관리
# - 추후 공장 위치 기반 시각화 포함 가능
# ----------------------------

import streamlit as st

def production_ui():
    st.title("🏭 생산 관리")
    st.info("여기에 생산 등록, 생산 계획, 공장별 현황 기능이 들어갈 예정입니다.")
    st.button("+ 생산 등록")
    st.dataframe([], use_container_width=True)
