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

# ✅ 페이지 설정
st.set_page_config(page_title="ERP 차량 관리 시스템", layout="wide", page_icon="🚗")

# ✅ 탭 UI 구성
tabs = st.tabs([
    " 대시보드", " 판매 관리", " 생산 관리", " 재고 관리",
    " 수출 관리", " 분석 리포트", " 인트로", " 설정", "예측 시스템", "추천 시스템"
])

tab_modules = [
    ("modules.dashboard", "dashboard_ui"),
    ("modules.sales", "sales_ui"),
    ("modules.production", "production_ui"),
    ("modules.inventory", "inventory_ui"),
    ("modules.export", "export_ui"),
    ("modules.analytics", "analytics_ui"),
    ("modules.intro", "intro_ui"),
    ("modules.settings", "settings_ui"),
    ("modules.prediction", "prediction_ui"),
    ("modules.recommendations", "recommendations_ui"),
]

for i, (mod_path, ui_func_name) in enumerate(tab_modules):
    with tabs[i]:
        try:
            module = __import__(mod_path, fromlist=[ui_func_name])
            getattr(module, ui_func_name)()
        except Exception as e:
            st.error(f"❗ [{mod_path}] 실행 중 오류 발생: {e}")
