# pages/settings.py
# ----------------------------
# 시스템 설정 페이지
# - 테마, 환경 설정, 관리자 정보 변경 등 포함
# ----------------------------
import streamlit as st

# 시스템 설정 페이지
def settings_ui():
    st.title("⚙️ 시스템 설정")
    st.info("여기에 환경 설정, 테마 설정, 보고서 출력 옵션 등이 들어갈 예정입니다.")

    # 세션 상태에서 테마 저장 (기본값은 라이트 모드)
    if 'theme' not in st.session_state:
        st.session_state['theme'] = '라이트 모드'

    # 테마에 맞게 CSS 적용
    if st.session_state['theme'] == "다크 모드":
        st.markdown(
            """
            <style>
            .reportview-container {
                background-color: #2e2e2e;
                color: white;
            }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <style>
            .reportview-container {
                background-color: white;
                color: black;
            }
            </style>
            """, unsafe_allow_html=True)

    # 테마 변경 버튼
    if st.session_state['theme'] == "다크 모드":
        if st.button("라이트 모드"):
            st.session_state['theme'] = '라이트 모드'  # 라이트 모드로 변경
    else:
        if st.button("다크 모드"):
            st.session_state['theme'] = '다크 모드'  # 다크 모드로 변경

    # 시스템 관리자 이메일 입력 필드 및 저장 버튼
    st.text_input("시스템 관리자 이메일")
    st.button("저장")
