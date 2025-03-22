# modules/sales.py
# ----------------------------
# 판매 관리 모듈
# - 판매 등록, 수정, 삭제 기능 구성 예정
# - 판매 데이터 시각화 및 관리 기능 포함
# ----------------------------

import streamlit as st

def sales_ui():
    st.title("🛒 판매 관리")
    st.info("여기에 판매 등록, 수정, 삭제 기능이 들어갈 예정입니다.")
    st.button("+ 신규 판매 등록")
    st.dataframe([], use_container_width=True)
