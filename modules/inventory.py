# modules/inventory.py
# ----------------------------
# 재고 관리 모듈
# - 재고 현황, 입출고 관리, 알림 기능
# - ERP 핵심 기능 중 하나
# ----------------------------

import streamlit as st

def inventory_ui():
    st.title("📦 재고 관리")
    st.info("여기에 재고 현황, 입출고 기록, 재고 조정 기능이 들어갈 예정입니다.")
    st.button("+ 재고 조정")
    st.dataframe([], use_container_width=True)
