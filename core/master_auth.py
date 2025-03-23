import streamlit as st

MASTER_ID = "admin"
MASTER_PW = "admin123"

def master_login():
    st.sidebar.subheader("🔐 관리자 로그인")
    user = st.sidebar.text_input("아이디 : admin ", key="master_id")
    pw = st.sidebar.text_input("비밀번호 :  admin123", type="password", key="master_pw")

    if st.sidebar.button("로그인"):
        if user == MASTER_ID and pw == MASTER_PW:
            st.session_state["is_master"] = True
            st.success("✅ 관리자 로그인 성공!")
        else:
            st.error("❌ 아이디 또는 비밀번호가 잘못되었습니다.")

def is_master_logged_in():
    return st.session_state.get("is_master", False)

def logout():
    if st.sidebar.button("로그아웃"):
        st.session_state.clear()
        st.success("🔓 로그아웃 완료")
