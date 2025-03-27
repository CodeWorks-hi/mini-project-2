import streamlit as st
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os

def intro_ui():
    st.title("📘 ERP 차량 관리 시스템 - 프로젝트 기획서")

    

    # ✅ 화면 표시용 요약 (Streamlit UI)
    st.markdown("""
    ### ✅ 개요 및 목적
    - 차량 생산부터 판매, 수출, 재고까지 전체 데이터를 통합 관리할 수 있는 ERP 시스템
    - 관리자 중심의 데이터 기반 경영 판단 도구 제공

    ### ✅ 핵심 기능
    - 판매 등록 / KPI / 이미지 로그 추적
    - 생산량 공장별 비교 / 지도 시각화
    - 수출 실적 및 성장률 분석
    - 재고 예측 / 위험 경고 시각화
    - 연도별 리포트 / PDF 다운로드 제공

    ### ✅ 배포 및 운영 정보
    - 주소: [https://hyundai-kia-dashboard-codeworks.streamlit.app](https://hyundai-kia-dashboard-codeworks.streamlit.app)
    - 관리자 계정: admin / admin123
    """)

    # ✅ PDF 생성 함수
    def generate_pdf():
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # ✅ 한글 폰트 등록
        pdfmetrics.registerFont(TTFont("NanumGothic", "fonts/NanumGothic.ttf"))
        c.setFont("NanumGothic", 16)
        c.drawString(50, height - 50, "ERP 차량 관리 시스템 - 프로젝트 기획서")

        c.setFont("NanumGothic", 11)
        y = height - 100
        spacing = 18

        contents = [
            "[1] 도입 및 목적",
            "- 생산/판매/수출/재고를 통합 관리하는 ERP 대시보드 시스템 구축",
            "- 관리자 중심으로 KPI 파악 및 예측 기반 의사결정 지원",
            "",
            "[2] 핵심 기능 요약",
            "- 판매 관리: 차량별 판매 등록, 로그 추적, KPI 카드",
            "- 생산 관리: 공장별 생산량 비교, 연도별 추이, 지도 시각화",
            "- 수출 관리: 국가별 실적, 성장률 분석",
            "- 재고 관리: 예측 재고량, 위험 경고, 시각화 차트",
            "- 분석 리포트: 연도별 통합 KPI, PDF/csv 다운로드",
            "",
            "[3] 기술 스택 및 구조",
            "- Backend: Python (Pandas, NumPy, ReportLab)",
            "- Frontend: Streamlit, Altair, Pydeck",
            "- 데이터 구조:",
            "    • data/raw/ : 원본 csv",
            "    • data/processed/ : 전처리 csv",
            "    • data/processed/ : 예시/위치정보/업로드용 파일",
            "",
            "[4] 배포 및 운영",
            "- 배포: Streamlit Cloud",
            "- 접속 주소: https://hyundai-kia-dashboard-codeworks.streamlit.app",
            "- 관리자 ID/PW: admin / admin123",
            "",
            "[5] 향후 확장 계획",
            "- AI 기반 수요 예측 / 생산 자동화",
            "- 계약자 관리 및 CRM 시스템 연동",
            "- ESG 지표 추적, 외부 물류/딜러사 API 연동",
            "- 탄소배출량/옵션/마케팅 효과 분석 등",
            "",
            f"[작성일] {datetime.today().strftime('%Y-%m-%d')}",
        ]

        for line in contents:
            c.drawString(50, y, line)
            y -= spacing
            if y < 60:
                c.showPage()
                c.setFont("NanumGothic", 11)
                y = height - 50

        c.save()
        buffer.seek(0)
        return buffer

    # ✅ PDF 다운로드 버튼
    pdf_file = generate_pdf()
    st.markdown("### 📥 기획서 PDF 다운로드")
    st.download_button(
        label="📄 ERP 기획서 PDF 다운로드",
        data=pdf_file,
        file_name="ERP_기획서.pdf",
        mime="application/pdf"
    )

    st.success("PDF 기획서가 성공적으로 생성되었습니다.")
