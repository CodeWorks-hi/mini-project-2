# pages/settings.py
# ----------------------------
# 시스템 설정 페이지
# - 테마, 기능 ON/OFF, 다국어 설정, 버전 정보 등 포함
# ----------------------------

import streamlit as st
from core.i18n import get_text

lang = "en"  # or "ko", "ja"
st.title(get_text("설정", lang))
st.button(get_text("저장", lang))

def settings_ui():
    st.title("⚙️ 시스템 설정")

    # 언어 설정
    st.subheader("🌐 언어 및 테마 설정")
    st.selectbox("🗣️ 언어(Language)", ["한국어", "English", "日本語"])
    st.selectbox("🎨 테마 선택", ["라이트 모드", "다크 모드"])
    st.text_input("📧 시스템 관리자 이메일")

    # 기능 모듈 ON/OFF
    st.subheader("🧩 기능 모듈 설정")
    st.checkbox("🛒 판매 관리 모듈 사용", value=True)
    st.checkbox("🏭 생산 관리 모듈 사용", value=True)
    st.checkbox("📦 재고 관리 모듈 사용", value=True)
    st.checkbox("🚢 수출 관리 모듈 사용", value=True)
    st.checkbox("🤖 AI 추천 시스템 활성화", value=True)

    # 베타/테스트 기능
    st.subheader("🧪 테스트 기능 (베타)")
    st.checkbox("📊 새로운 차트 시각화 적용", value=False)
    st.checkbox("🧠 스마트 알림 기능 체험", value=False)

    # 버전 정보 및 시스템
    st.subheader("📜 버전 및 시스템 정보")
    st.markdown("""
    - **버전:** `v1.2.3`
    - **배포일:** 2025-03-23
    - **개발자:** `choenamho + GPT`
    - **환경:** Streamlit Web UI
    - **경로:** `mini-project-2/pages/settings.py`
    """)

    st.button("💾 저장")
