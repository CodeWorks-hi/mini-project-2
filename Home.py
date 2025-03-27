# 앱 로컬 실행 시 : streamlit run Home.py
# 앱 스트림릿 서버상 실행 시 : https://hyundai-kia-dashboard-codeworks.streamlit.app/
# ID: admin
# PW: admin123
# Home.py
# ----------------------------
# Streamlit 진입점 (메인 실행 파일)
# - 마스터 로그인, 네비게이션, 페이지 라우팅
# ----------------------------

# Home.py
# ----------------------------
# 첫 진입 시 로그인 화면 → 로그인 성공 시 탭 UI로 전환
# ----------------------------

import streamlit as st
from core.master_auth import master_login, is_master_logged_in

import streamlit as st

# ✅ 페이지 설정
st.set_page_config(
    page_title="ERP 차량 관리 시스템",
    layout="wide",
    page_icon="🚗"
)

# ✅ 탭 UI 정의
TABS = [
    " 대시보드", " 판매 관리", " 생산 관리", " 재고 관리",
    " 수출 관리", " 분석 리포트", " 인트로", " 설정", "추천 시스템"
]

# ✅ 탭 생성
tabs = st.tabs(TABS)

# ✅ 각 탭에 해당하는 기능 모듈 import
import modules.dashboard as dashboard
import modules.sales as sales
import modules.production as production
import modules.inventory as inventory
import modules.export as export
import modules.analytics as analytics
import modules.intro as intro
import modules.settings as settings
import modules.recommendations as recommendations

# ✅ 각 탭에 해당하는 UI 실행
with tabs[0]:
    dashboard.dashboard_ui()

with tabs[1]:
    sales.sales_ui()

with tabs[2]:
    production.production_ui()

with tabs[3]:
    inventory.inventory_ui()

with tabs[4]:
    export.export_ui()

with tabs[5]:
    analytics.analytics_ui()

with tabs[6]:
    intro.intro_ui()

with tabs[7]:
    settings.settings_ui()

with tabs[8]:
    recommendations.recommendations_ui()
