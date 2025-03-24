# core/master_auth.py
# ----------------------------
# 관리자 로그인 / 로그아웃 기능 (화면 중앙 UI 버전)
# ----------------------------

import streamlit as st

MASTER_ID = "admin"
MASTER_PW = "admin123"

def master_login():
    st.markdown("## 🔐 관리자 로그인")
    with st.form("login_form"):
        user = st.text_input("아이디", placeholder="admin", key="master_id")
        pw = st.text_input("비밀번호", type="password", placeholder="admin123", key="master_pw")
        submitted = st.form_submit_button("로그인")

        if submitted:
            if user == MASTER_ID and pw == MASTER_PW:
                st.session_state["is_master"] = True
                st.success("✅ 로그인 성공!")
                st.rerun()
            else:
                st.error("❌ 아이디 또는 비밀번호가 틀렸습니다.")

def is_master_logged_in():
    return st.session_state.get("is_master", False)

def logout():
    st.markdown("#### ✅ 관리자 로그인됨")
    if st.button("🔓 로그아웃"):
        st.session_state.clear()
        st.rerun()
