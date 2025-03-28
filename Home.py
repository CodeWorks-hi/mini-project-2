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
import logging
import traceback

# ✅ 페이지 설정
st.set_page_config(page_title="ERP 차량 관리 시스템", layout="wide", page_icon="./images/favicon.ico")

# 로그 설정
logging.basicConfig(filename='error_log.txt', level=logging.ERROR)

# ✅ 탭 UI 구성
tabs = st.tabs([
    " 대시보드", " 생산 관리", " 재고 관리",
    " 판매 관리",   "예측 시스템"," 분석 리포트", "AI 예측 및 분석"," 인트로"
])

tab_modules = [
    ("modules.dashboard", "dashboard_ui"), # 데쉬보드
    ("modules.production", "production_ui"), # 생산
    ("modules.inventory", "inventory_ui"), #재고
    ("modules.export", "export_ui"),  # 수출관리
    ("modules.prediction", "prediction_ui"), # 예측
    ("modules.analytics", "analytics_ui"), # 분석관리
    ("modules.recommendations", "recommendations_ui"), #추천 
    ("modules.intro", "intro_ui"), # 인트로


]

for i, (mod_path, ui_func_name) in enumerate(tab_modules):
    with tabs[i]:
        try:
            module = __import__(mod_path, fromlist=[ui_func_name])
            getattr(module, ui_func_name)()
        except Exception as e:
            error_message = f"❗ [{mod_path}] 실행 중 오류 발생: {e}"
            st.error(error_message)
            
            # 오류 상세 정보를 로그 파일에 기록
            logging.error(f"Module {mod_path}에서 오류 발생: {traceback.format_exc()}")
            st.text(f"오류에 대한 자세한 정보는 error_log.txt 파일에 기록되었습니다.")
