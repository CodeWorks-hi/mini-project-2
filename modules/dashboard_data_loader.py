import pandas as pd
import streamlit as st
import os

@st.cache_data
def load_csv(path):
    base_dir = os.path.dirname(__file__)  # 현재 파일의 위치
    try:
        return pd.read_csv(os.path.join(base_dir, path))
    except Exception as e:
        st.error(f"CSV 파일 로드 중 오류 발생: {str(e)}")
        return None

def load_and_merge_export_data():
    df_h = load_csv("../data/processed/현대_지역별수출실적_전처리.CSV")
    df_k = load_csv("../data/processed/기아_지역별수출실적_전처리.CSV")
    if df_h is None or df_k is None:
        return None

    df_h["브랜드"] = "현대"
    df_k["브랜드"] = "기아"
    if "차량 구분" not in df_h.columns:
        df_h["차량 구분"] = "기타"
    return pd.concat([df_h, df_k], ignore_index=True)

def load_hyundai_factory_data():
    df = load_csv("data/processed/현대_해외공장판매실적_전처리.CSV")
    if df is not None:
        df["브랜드"] = "현대"
    return df

def load_kia_factory_data():
    df = load_csv("data/processed/기아_해외공장판매실적_전처리.CSV")
    if df is not None:
        df["브랜드"] = "기아"
    return df

def load_location_data():
    return load_csv("data/세일즈파일/지역별_위치정보.csv")
