# pages/settings.py
# ----------------------------
# 시스템 설정 페이지
# - 테마, 환경 설정, 관리자 정보 변경 등 포함
# ----------------------------

import streamlit as st

def settings_ui():
    st.title("⚙️ 시스템 설정")
    st.info("여기에 환경 설정, 테마 설정, 보고서 출력 옵션 등이 들어갈 예정입니다.")

    st.selectbox("테마 선택", ["라이트 모드", "다크 모드"])
    st.text_input("시스템 관리자 이메일")
    st.button("저장")
