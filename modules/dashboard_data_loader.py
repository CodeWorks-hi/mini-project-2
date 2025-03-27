import pandas as pd
import streamlit as st
import os

@st.cache_data
def load_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"csv 파일 로드 중 오류 발생: {str(e)}")
        return None

def load_and_merge_export_data(hyundai_path="data/processed/현대_지역별수출실적_전처리.csv", 
                                kia_path="data/processed/기아_지역별수출실적_전처리.csv"):
    base_path = os.path.join(os.getcwd(), 'data', 'processed')  # 절대 경로 설정
    hyundai_file = os.path.join(base_path, hyundai_path)
    kia_file = os.path.join(base_path, kia_path)
    
    df_h = load_csv(hyundai_file)
    df_k = load_csv(kia_file)
    
    if df_h is None or df_k is None:
        return None

    df_h["브랜드"] = "현대"
    df_k["브랜드"] = "기아"
    
    if "차량 구분" not in df_h.columns:
        df_h["차량 구분"] = "기타"
    
    # 데이터 병합 후 NaN 값 처리
    df_merged = pd.concat([df_h, df_k], ignore_index=True)
    
    return df_merged

def load_hyundai_factory_data():
    df = load_csv("data/processed/현대_해외공장판매실적_전처리.csv")
    if df is not None:
        df["브랜드"] = "현대"
    return df

def load_kia_factory_data():
    df = load_csv("data/processed/기아_해외공장판매실적_전처리.csv")
    if df is not None:
        df["브랜드"] = "기아"
    return df

def load_location_data():
    return load_csv("data/세일즈파일/지역별_위치정보.csv")
