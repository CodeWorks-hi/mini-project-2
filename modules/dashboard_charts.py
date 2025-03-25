# modules/dashboard_charts.py
# ----------------------------
# 대시보드용 주요 차트 시각화 모듈
# - 월별 생산/판매/수출 추이 시각화
# - 재고 상태 분석 및 경고 시스템
# - 공장별 생산량 비교 차트
# ----------------------------

import streamlit as st
import pandas as pd
import altair as alt
from typing import List, Dict

def show_monthly_trend(data: Dict[str, pd.DataFrame], month_cols: List[str], chart_height: int = 400) -> None:
    """
    월별 생산, 판매, 수출 추이를 비교하는 라인 차트 생성
    
    Args:
        data (Dict[str, pd.DataFrame]): 'prod', 'sales', 'export' 키를 가진 데이터프레임 딕셔너리
        month_cols (List[str]): 월별 컬럼 이름 리스트
        chart_height (int): 차트 높이 (기본값 400)
    """
    try:
        if any(df.empty for df in data.values()):
            st.warning("일부 데이터가 존재하지 않습니다")
            return

        st.subheader("📊 월별 생산 / 판매 / 수출 추이")
        
        merged = pd.DataFrame({
            key: df[month_cols].sum() for key, df in data.items()
        }).reset_index()
        melted = merged.melt(id_vars='index', var_name='구분', value_name='수량')
        melted.rename(columns={'index': '월'}, inplace=True)

        chart = alt.Chart(melted).mark_line(point=True).encode(
            x=alt.X('월:N', title=''),
            y=alt.Y('수량:Q', title='수량'),
            color='구분:N',
            tooltip=['월', '구분', alt.Tooltip('수량:Q', format=',')]
        ).properties(height=chart_height)
        
        st.altair_chart(chart, use_container_width=True)

    except Exception as e:
        st.error(f"차트 생성 중 오류 발생: {str(e)}")

def render_factory_chart(prod_df: pd.DataFrame, selected_year: int):
    """
    공장별 생산량 비교 차트 렌더링
    
    Args:
        prod_df (pd.DataFrame): 생산 데이터프레임
        selected_year (int): 선택된 연도
    """
    st.subheader("🏭 공장별 생산량 비교")
    
    try:
        yearly_data = prod_df[prod_df['연도'] == selected_year]
        if yearly_data.empty:
            st.warning(f"{selected_year}년 데이터가 없습니다.")
            return

        factory_production = yearly_data.groupby('공장')['생산량'].sum().reset_index()
        
        chart = alt.Chart(factory_production).mark_bar().encode(
            x='공장:N',
            y='생산량:Q',
            color='공장:N',
            tooltip=['공장', alt.Tooltip('생산량:Q', format=',')]
        ).properties(height=300)

        st.altair_chart(chart, use_container_width=True)

    except Exception as e:
        st.error(f"공장별 생산량 차트 생성 중 오류 발생: {str(e)}")

def show_stock_summary(inventory_df: pd.DataFrame, low_threshold: int = 100, high_threshold: int = 10000) -> None:
    """
    재고 상태 분석 및 경고 시스템
    
    Args:
        inventory_df (pd.DataFrame): 재고 데이터프레임
        low_threshold (int): 재고 부족 기준값 (기본값 100)
        high_threshold (int): 재고 과잉 기준값 (기본값 10000)
    """
    try:
        st.subheader("⚠️ 재고 상태 요약")
        
        low_stock = inventory_df[inventory_df["예상재고"] < low_threshold]
        high_stock = inventory_df[inventory_df["예상재고"] > high_threshold]

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### 🔻 재고 부족 차종 (< {low_threshold:,}대)")
            if not low_stock.empty:
                st.dataframe(
                    low_stock.style.applymap(
                        lambda x: 'color: red' if x < low_threshold else '', 
                        subset=['예상재고']
                    ),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("재고 부족 차종이 없습니다")
        
        with col2:
            st.markdown(f"#### 🔺 재고 과잉 차종 (> {high_threshold:,}대)")
            if not high_stock.empty:
                st.dataframe(
                    high_stock.style.applymap(
                        lambda x: 'color: blue' if x > high_threshold else '',
                        subset=['예상재고']
                    ),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("재고 과잉 차종이 없습니다")

        st.caption(f"📌 총 {len(low_stock)}개 차종 재고 부족, {len(high_stock)}개 차종 재고 과잉")

    except Exception as e:
        st.error(f"재고 분석 중 오류 발생: {str(e)}")

# 사용 예시
if __name__ == "__main__":
    st.title("대시보드 차트 테스트")
    
    # 샘플 데이터 생성
    sample_data = {
        'prod': pd.DataFrame({'월': range(1, 13), '생산량': [100, 120, 110, 130, 140, 135, 145, 150, 160, 155, 170, 180]}),
        'sales': pd.DataFrame({'월': range(1, 13), '판매량': [90, 100, 105, 115, 125, 130, 135, 140, 145, 150, 160, 170]}),
        'export': pd.DataFrame({'월': range(1, 13), '수출량': [80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135]})
    }
    
    month_cols = [str(i) + '월' for i in range(1, 13)]
    
    show_monthly_trend(sample_data, month_cols)
    
    sample_prod_df = pd.DataFrame({
        '연도': [2023] * 12 + [2024] * 12,
        '공장': ['A', 'B', 'C'] * 8,
        '생산량': [1000, 1200, 1100] * 8
    })
    
    render_factory_chart(sample_prod_df, 2023)
    
    sample_inventory_df = pd.DataFrame({
        '브랜드': ['A', 'B', 'C', 'D', 'E'],
        '차종': ['SUV', 'Sedan', 'Hatchback', 'SUV', 'Sedan'],
        '예상재고': [50, 200, 15000, 8000, 120]
    })
    
    show_stock_summary(sample_inventory_df)
