import os
import pandas as pd
import streamlit as st

# ✅ 데이터 로드 함수 - 캐시 처리 및 경로 디버깅 포함
@st.cache_data
def load_csv(path):
    try:
        file_path = os.path.abspath(path)
        return pd.read_csv(file_path)
    except Exception as e:
        st.error(f"CSV 파일 로드 중 오류 발생: {str(e)}")
        return None

# ✅ 수출 데이터 병합 함수
def load_and_merge_export_data(hyundai_path="data/processed/hyundai-by-region.csv", 
                                kia_path="data/processed/kia-by-region.csv"):
    df_h = load_csv(hyundai_path)
    df_k = load_csv(kia_path)
    
    if df_h is None or df_k is None:
        return None

    df_h["브랜드"] = "현대"
    df_k["브랜드"] = "기아"
    
    df_merged = pd.concat([df_h, df_k], ignore_index=True)
    return df_merged

def load_and_merge_car_data(hyundai_path="data/processed/hyundai-by-car.csv", 
                                kia_path="data/processed/kia-by-car.csv"):
    df_h = load_csv(hyundai_path)
    df_k = load_csv(kia_path)
    
    if df_h is None or df_k is None:
        return None

    df_h["브랜드"] = "현대"
    df_k["브랜드"] = "기아"
    
    df_merged = pd.concat([df_h, df_k], ignore_index=True)
    return df_merged

def load_and_merge_plant_data(hyundai_path="data/processed/hyundai-by-plant.csv", 
                                kia_path="data/processed/kia-by-plant.csv"):
    df_h = load_csv(hyundai_path)
    df_k = load_csv(kia_path)
    
    if df_h is None or df_k is None:
        return None

    df_h["브랜드"] = "현대"
    df_k["브랜드"] = "기아"
    
    df_merged = pd.concat([df_h, df_k], ignore_index=True)
    return df_merged

# ✅ 현대차 공장 판매 실적 데이터 로드
def load_hyundai_factory_data():
    hyundai_file = "data/processed/hyundai-by-plant.csv"
    df = load_csv(hyundai_file)
    if df is not None:
        df["브랜드"] = "현대"
    return df

# ✅ 기아차 공장 판매 실적 데이터 로드
def load_kia_factory_data():
    kia_file = "data/processed/kia-by-plant.csv"
    df = load_csv(kia_file)
    if df is not None:
        df["브랜드"] = "기아"
    return df

