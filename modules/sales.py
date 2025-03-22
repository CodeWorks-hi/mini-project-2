import streamlit as st
import pandas as pd
import os
from datetime import datetime
from modules.sales_kpi import show_kpi_cards
from modules.sales_log import show_sales_log_table
from modules.sales_chart import show_sales_charts

CSV_PATH = "data/세일즈파일/sales_records.csv"
CAR_INFO_PATH = "data/세일즈파일/차량정보.csv"
SAMPLE_PATH = "data/세일즈파일/판매기록_샘플_차정보포함.xlsx"

# 차량 정보 로딩
def load_car_info():
    if os.path.exists(CAR_INFO_PATH):
        return pd.read_csv(CAR_INFO_PATH).dropna().drop_duplicates()
    return pd.DataFrame()

# 판매 저장
def save_sale_record(data: dict):
    new_df = pd.DataFrame([data])
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        expected_cols = ["판매일", "모델명", "수량", "지역", "담당자", "차종", "가격"]
        for col in expected_cols:
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

# 삭제 함수 (입력된 판매기록과 일치하는 행 삭제 후 리런)
def delete_sale_record(del_data: dict):
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        # 해당 조건에 맞는 행을 제외
        df = df[~((df['판매일'] == del_data['판매일']) &
                  (df['모델명'] == del_data['모델명']) &
                  (df['지역'] == del_data['지역']) &
                  (df['담당자'] == del_data['담당자']))]
        df.to_csv(CSV_PATH, index=False)
        st.success("✅ 판매 기록 삭제 완료")
        st.experimental_rerun()  # 삭제 후 페이지 자동 새로고침

# 메인 판매 UI
def sales_ui():
    st.title("🛒 판매 관리")
    car_info = load_car_info()
    available_models = sorted(car_info['모델명'].dropna().unique()) if '모델명' in car_info.columns else []

    if available_models:
        selected_model = st.selectbox("모델명 선택", available_models, key="selected_model")
    else:
        selected_model = None

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
        st.number_input("가격 (기본값)", value=int(가격), step=100000, key="price_display", disabled=True)

    # 판매 등록 폼
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

        col7, col8 = st.columns(2)
        with col7:
            price_input = st.number_input("가격", value=int(가격), step=100000)

        submitted = st.form_submit_button("판매 등록")
        if submitted:
            record = {
                "판매일": str(판매일),
                "모델명": selected_model,
                "수량": 수량,
                "지역": 지역,
                "담당자": 담당자,
                "차종": 차종,
                "가격": price_input
            }
            save_sale_record(record)

    # 판매 기록, KPI, 차트 표시
    if os.path.exists(CSV_PATH):
        sales_df = pd.read_csv(CSV_PATH)
        show_kpi_cards(sales_df)
        show_sales_log_table(sales_df)
        show_sales_charts(sales_df)

    # 삭제 UI: 삭제할 판매 기록 정보를 입력받고 삭제 버튼 클릭 시 자동 새로고침
    with st.expander("판매 기록 삭제"):
        st.info("삭제할 판매 기록의 정보를 입력하세요.")
        del_판매일 = st.date_input("삭제할 판매일")
        del_모델명 = st.text_input("삭제할 모델명")
        del_지역 = st.text_input("삭제할 지역")
        del_담당자 = st.text_input("삭제할 담당자")
        if st.button("삭제"):
            delete_sale_record({
                "판매일": str(del_판매일),
                "모델명": del_모델명,
                "지역": del_지역,
                "담당자": del_담당자
            })

    st.download_button("📥 차량정보 포함 샘플 다운로드",
        data=open(SAMPLE_PATH, "rb").read(),
        file_name="판매기록_샘플_차정보포함.xlsx")

if __name__ == "__main__":
    sales_ui()
