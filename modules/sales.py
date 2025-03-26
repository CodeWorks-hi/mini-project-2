# modules/sales.py
# ----------------------------
# 판매 관리 메인 UI + 등록, 삭제, KPI, 로그, 차트 연동
# ----------------------------

import streamlit as st
import pandas as pd
import os
from datetime import datetime

from modules.sales_kpi import show_kpi_cards
from modules.sales_log import show_sales_log_table
from modules.sales_chart import show_sales_charts

# 📁 파일 경로 상수
CSV_PATH = "data/세일즈파일/현대/sales_records.csv"
CAR_INFO_PATH = "data/세일즈파일/현대/차량정보.csv"
SAMPLE_PATH = "data/세일즈파일/현대/판매기록_샘플_차정보포함.xlsx"

# 🔹 차량 정보 로드
def load_car_info():
    if os.path.exists(CAR_INFO_PATH):
        return pd.read_csv(CAR_INFO_PATH).dropna().drop_duplicates()
    return pd.DataFrame()

# 🔹 판매 데이터 저장
def save_sale_record(data: dict):
    new_df = pd.DataFrame([data])
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        for col in ["판매일", "모델명", "수량", "지역", "담당자", "차종", "가격"]:
            if col not in df.columns:
                df[col] = None
        duplicate = df[(df['판매일'] == data['판매일']) & (df['모델명'] == data['모델명']) &
                       (df['지역'] == data['지역']) & (df['담당자'] == data['담당자'])]
        if not duplicate.empty:
            st.warning("⚠️ 동일한 판매 기록이 이미 존재합니다.")
            return
        df = pd.concat([df, new_df], ignore_index=True)
    else:
        df = new_df
    df.to_csv(CSV_PATH, index=False)
    st.success("✅ 판매 등록 완료")

# 🔹 판매 데이터 삭제
def delete_sale_record(del_data: dict):
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        df = df[~((df['판매일'] == del_data['판매일']) &
                  (df['모델명'] == del_data['모델명']) &
                  (df['지역'] == del_data['지역']) &
                  (df['담당자'] == del_data['담당자']))]
        df.to_csv(CSV_PATH, index=False)
        st.success("✅ 판매 기록 삭제 완료")
        st.experimental_rerun()

# 🔹 메인 판매 UI
def sales_ui():
    st.title("🛒 판매 관리 시스템")
    car_info = load_car_info()
    available_models = sorted(car_info['모델명'].dropna().unique()) if '모델명' in car_info.columns else []

    selected_model = st.selectbox("모델명 선택", available_models) if available_models else None

    차종, 가격, 이미지 = "-", 0, None
    if selected_model and not car_info.empty:
        row = car_info[car_info['모델명'] == selected_model].iloc[0]
        차종 = row.get('차종') or row.get('차량구분', '-')
        가격 = row.get('가격', 0)
        이미지 = row.get('이미지URL') if '이미지URL' in row else None

    col_img, col_info = st.columns(2)
    with col_img:
        if 이미지:
            st.image(이미지, caption=f"{selected_model} 이미지", use_container_width=True)
    with col_info:
        st.text_input("차종", 차종, disabled=True)
        st.number_input("가격 (기본값)", value=int(가격), step=100000, disabled=True)

    # 🔸 판매 등록 폼
    with st.form("판매 등록 폼"):
        col1, col2 = st.columns(2)
        with col1:
            판매일 = st.date_input("판매일")
        with col2:
            지역 = st.selectbox("판매 지역", ["서울", "부산", "대구", "해외"])

        col3, col4 = st.columns(2)
        with col3:
            st.text_input("모델명", selected_model if selected_model else "", disabled=True)
        with col4:
            담당자 = st.text_input("판매 담당자")

        col5, col6 = st.columns(2)
        with col5:
            st.text_input("차종", 차종, disabled=True)
        with col6:
            수량 = st.number_input("판매 수량", min_value=1, step=1)

        col7 = st.columns(1)[0]
        가격입력 = col7.number_input("가격", value=int(가격), step=100000)

        if st.form_submit_button("판매 등록"):
            record = {
                "판매일": str(판매일),
                "모델명": selected_model,
                "수량": 수량,
                "지역": 지역,
                "담당자": 담당자,
                "차종": 차종,
                "가격": 가격입력
            }
            save_sale_record(record)

    # 🔸 판매 기록, KPI, 차트
    if os.path.exists(CSV_PATH):
        sales_df = pd.read_csv(CSV_PATH)
        show_kpi_cards(sales_df)
        show_sales_log_table(sales_df)
        show_sales_charts(sales_df)

    # 샘플 다운로드 제공
    if os.path.exists(SAMPLE_PATH):
        st.download_button(
            label="📥 차량정보 포함 샘플 다운로드",
            data=open(SAMPLE_PATH, "rb").read(),
            file_name="판매기록_샘플_차정보포함.xlsx"
        )
