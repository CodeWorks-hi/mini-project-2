import streamlit as st
import pandas as pd
import os

# 파일 경로 함수
def get_processed_path(filename):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed", filename))

# CSV 로드
@st.cache_data
def load_csv(filepath):
    try:
        return pd.read_csv(filepath)
    except Exception as e:
        st.error(f"❗ {os.path.basename(filepath)} 로드 실패: {e}")
        return None

# 데이터 미리보기 UI
def data_preview_ui():
    st.title("원본 데이터 미리보기")

    # 파일 목록
    data_files = {
        "현대 - 차종별 판매": "hyundai-by-car.csv",
        "현대 - 공장별 판매": "hyundai-by-plant.csv",
        "현대 - 지역별 수출": "hyundai-by-region.csv",
        "기아 - 차종별 판매": "kia-by-car.csv",
        "기아 - 공장별 판매": "kia-by-plant.csv",
        "기아 - 지역별 수출": "kia-by-region.csv"
    }

    # 드롭다운
    selected_label = st.selectbox("확인할 원본 데이터를 선택하세요", list(data_files.keys()))
    selected_path = get_processed_path(data_files[selected_label])

    df = load_csv(selected_path)
    if df is not None:
        st.markdown(f"### ✅ `{os.path.basename(selected_path)}` 미리보기")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"총 {df.shape[0]:,} 행 × {df.shape[1]} 열")
