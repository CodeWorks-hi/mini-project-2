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


# ✅ 페이지 설정
st.set_page_config(page_title="ERP 차량 관리 시스템", layout="wide")


# ✅ 로그인 후에는 탭 UI로 구성
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📊 대시보드", "🛒 판매 관리", "🏭 생산 관리", "📦 재고 관리",
    "🚢 수출 관리", "🤖 추천 시스템", "📈 분석 리포트", "📘 인트로", "⚙️ 설정"
])

with tab1:
    import modules.dashboard as dashboard
    dashboard.dashboard_ui()

with tab2:
    import modules.sales as sales
    sales.sales_ui()

with tab3:
    import modules.production as production
    production.production_ui()

with tab4:
    import modules.inventory as inventory
    inventory.inventory_ui()

with tab5:
    import modules.export as export
    export.export_ui()

with tab6:
    import modules.recommendations as recommendations
    recommendations.recommendations_ui()

with tab7:
    import modules.analytics as analytics
    analytics.analytics_ui()

with tab8:
    import modules.intro as intro
    intro.intro_ui()

with tab9:
    import modules.settings as settings
    settings.settings_ui()
