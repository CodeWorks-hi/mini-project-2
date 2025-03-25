# modules/dashboard_filter.py
# ----------------------------
# 대시보드 필터링 시스템 전문 모듈
# - 동적 필터 UI 생성
# - 다중 조건 필터링 엔진
# ----------------------------

import streamlit as st
import pandas as pd
from typing import Tuple

def get_filter_options(df: pd.DataFrame) -> Tuple[int, str, str]:
    """
    데이터 필터 옵션을 제공하는 함수
    
    Args:
        df (pd.DataFrame): 필터링할 데이터프레임
        
    Returns:
        Tuple[int, str, str]: 선택된 연도, 국가, 차종
    """
    # 연도 필터
    years = sorted(df["연도"].dropna().unique(), reverse=True)
    selected_year = st.selectbox("연도 선택", years)

    # 국가 필터
    countries = ["전체"] + sorted(df["지역명"].dropna().unique())
    selected_country = st.selectbox("국가 선택", countries)

    # 차종 필터
    car_types = ["전체"] + sorted(df["차량 구분"].dropna().unique())
    selected_type = st.selectbox("차종 선택", car_types)

    return selected_year, selected_country, selected_type

def apply_filters(
    df: pd.DataFrame,
    year: int,
    brand: str = "전체",
    region: str = "전체",
    car_type: str = "전체"
) -> pd.DataFrame:
    """
    다중 조건 필터링 엔진
    
    Args:
        df (pd.DataFrame): 원본 데이터
        year (int): 선택 연도
        brand (str): 브랜드 필터
        region (str): 지역 필터
        car_type (str): 차종 필터
        
    Returns:
        pd.DataFrame: 필터링된 데이터프레임
    """
    try:
        # 기본 필터
        filtered = df[df["연도"] == year].copy()
        
        # 브랜드 필터
        if brand != "전체":
            filtered = filtered[filtered["브랜드"] == brand]
            
        # 지역 필터
        if region != "전체" and "지역" in filtered.columns:
            filtered = filtered[filtered["지역"] == region]
            
        # 차종 필터
        if car_type != "전체" and "차종" in filtered.columns:
            filtered = filtered[filtered["차종"] == car_type]
            
        # 인덱스 재설정
        return filtered.reset_index(drop=True).infer_objects()
    
    except KeyError as e:
        st.error(f"필터링 오류: {str(e)} 컬럼이 존재하지 않습니다")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"필터링 과정에서 오류 발생: {str(e)}")
        return df