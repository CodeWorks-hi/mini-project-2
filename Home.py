# 앱 로컬 실행 시 : streamlit run Home.py
# 앱 스트림릿 서버상 실행 시 : https://hyundai-kia-dashboard-codeworks.streamlit.app/
# ID: admin
# PW: admin123
# Home.py
# ----------------------------
# Streamlit 진입점 (메인 실행 파일)
# - 마스터 로그인, 네비게이션, 페이지 라우팅
# ----------------------------

import streamlit as st
from components.navbar import navbar
from core.master_auth import master_login, is_master_logged_in, logout

# 모듈 및 페이지 import
import modules.sales as sales
import modules.production as production
import modules.inventory as inventory
import modules.export as export
import modules.dashboard as dashboard
import modules.analytics as analytics
import modules.recommendations as recommendations
import modules.settings as settings

# ✅ 페이지 설정
st.set_page_config(page_title="ERP 차량 관리 시스템", layout="wide")

# ✅ 관리자 로그인
master_login()

if is_master_logged_in():
    logout()
    st.sidebar.image("images/hyunlogo.png", use_container_width=True)

    selected_page = navbar()

    if selected_page == "홈":
        st.title("🚗 ERP 차량 관리 시스템 - 관리자")
        st.write("판매, 생산, 재고, 수출 등 전체 업무를 통합 관리합니다.")

    elif selected_page == "대시보드":
        dashboard.dashboard_ui()

    elif selected_page == "판매 관리":
        sales.sales_ui()

    elif selected_page == "생산 관리":
        production.production_ui()

    elif selected_page == "재고 관리":
        inventory.inventory_ui()

    elif selected_page == "수출 관리":
        export.export_ui()

    elif selected_page == "추천 시스템":
        recommendations.recommendations_ui()

    elif selected_page == "분석 리포트":
        analytics.analytics_ui()

    elif selected_page == "설정":
        settings.settings_ui()
else:
    st.warning("🔐 관리자 로그인 후 사용 가능합니다.")
