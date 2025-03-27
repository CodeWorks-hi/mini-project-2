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
st.set_page_config(
    page_title="ERP 차량 관리 시스템",
    layout="wide",
    page_icon="🚗"
)

# ✅ 에러 방지용 안전 로딩 함수
def safe_tab_import(tab, module_name, ui_function_name, tab_label):
    try:
        mod = __import__(f"modules.{module_name}", fromlist=[ui_function_name])
        getattr(mod, ui_function_name)()
    except Exception as e:
        with tab:
            st.error(f"❌ [{tab_label}] 모듈 실행 중 에러 발생:\n\n{e}")

# ✅ 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    " 대시보드", " 판매 관리", " 생산 관리", " 재고 관리",
    " 수출 관리", " 분석 리포트", " 인트로", " 설정", "추천 시스템"
])

# ✅ 각 탭에 안전하게 모듈 로딩
safe_tab_import(tab1, "dashboard", "dashboard_ui", "대시보드")
safe_tab_import(tab2, "sales", "sales_ui", "판매 관리")
safe_tab_import(tab3, "production", "production_ui", "생산 관리")
safe_tab_import(tab4, "inventory", "inventory_ui", "재고 관리")
safe_tab_import(tab5, "export", "export_ui", "수출 관리")
safe_tab_import(tab6, "analytics", "analytics_ui", "분석 리포트")
safe_tab_import(tab7, "intro", "intro_ui", "인트로")
safe_tab_import(tab8, "settings", "settings_ui", "설정")
safe_tab_import(tab9, "recommendations", "recommendations_ui", "추천 시스템")