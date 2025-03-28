import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import numpy as np

# 연도/월 컬럼 추출 함수
def extract_month_columns(df):
    return [col for col in df.columns if "-" in col and col[:4].isdigit()]

# 연도 컬럼 생성 함수
def extract_year_column(df):
    month_cols = extract_month_columns(df)
    if "연도" not in df.columns:
        def get_year(row):
            valid_years = [int(col.split("-")[0]) for col in month_cols if pd.notnull(row[col])]
            return max(valid_years) if valid_years else None
        df["연도"] = df.apply(get_year, axis=1)
    return df

# 데이터 필터링 함수
def apply_filters(df, year, brand):
    if "연도" not in df.columns:
        return pd.DataFrame()
    filtered_df = df[df["연도"] == year]
    if brand != "전체":
        filtered_df = filtered_df[filtered_df["브랜드"] == brand]
    return filtered_df

@st.cache_data
def load_data():
    # 파일 로드
    prod_h = pd.read_csv("data/processed/hyundai-by-plant.csv")
    prod_k = pd.read_csv("data/processed/kia-by-plant.csv")
    sales_h = pd.read_csv("data/processed/hyundai-by-car.csv")
    sales_k = pd.read_csv("data/processed/kia-by-car.csv")
    export_h = pd.read_csv("data/processed/hyundai-by-region.csv")
    export_k = pd.read_csv("data/processed/kia-by-region.csv")

    for df_, brand_ in [
        (prod_h, "현대"), (prod_k, "기아"),
        (sales_h, "현대"), (sales_k, "기아"),
        (export_h, "현대"), (export_k, "기아")
    ]:
        df_["브랜드"] = brand_

    # 병합
    prod_df = pd.concat([prod_h, prod_k], ignore_index=True)
    sales_df = pd.concat([sales_h, sales_k], ignore_index=True)
    export_df = pd.concat([export_h, export_k], ignore_index=True)

    return prod_df, sales_df, export_df

def analytics_ui():
    # 데이터 로드
    prod_df, sales_df, export_df = load_data()

    # 연도 컬럼 생성
    prod_df = extract_year_column(prod_df)
    sales_df = extract_year_column(sales_df)
    export_df = extract_year_column(export_df)

    # 실제 월 컬럼 (yyyy-mm 형식)
    month_cols = extract_month_columns(prod_df)

    # 필터 UI
    col1, col2 = st.columns(2)
    with col1:
        brand_options = ["전체"] + sorted(prod_df["브랜드"].dropna().unique())
        brand = st.selectbox("브랜드 선택", brand_options, key="analytics_brand")
    with col2:
        year_options = sorted(prod_df["연도"].dropna().unique(), reverse=True)
        if not year_options:
            st.warning("❗ 분석할 연도가 없습니다.")
            return
        year = st.selectbox("연도 선택", year_options, key="analytics_year")

    # 데이터 필터링
    prod_filtered = apply_filters(prod_df, year, brand)
    sales_filtered = apply_filters(sales_df, year, brand)
    export_filtered = apply_filters(export_df, year, brand)

    total_prod = int(prod_filtered[month_cols].sum(numeric_only=True).sum(skipna=True))
    total_sales = int(sales_filtered[month_cols].sum(numeric_only=True).sum(skipna=True))
    total_export = int(export_filtered[month_cols].sum(numeric_only=True).sum(skipna=True))
    total_stock = total_prod - total_sales

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("총 생산량", f"{total_prod:,} 대")
    k2.metric("총 판매량", f"{total_sales:,} 대")
    k3.metric("총 수출량", f"{total_export:,} 대")
    k4.metric("예상 재고량", f"{total_stock:,} 대")

    # AI 분석 결과 표시
    if 'analysis_result' in st.session_state:
        st.subheader("AI 분석 결과")
        analysis_text = st.session_state.analysis_result
        
        # 텍스트에서 표 추출
        table_start = analysis_text.find("|")
        table_end = analysis_text.rfind("|")
        if table_start != -1 and table_end != -1:
            table_text = analysis_text[table_start:table_end+1]
            rows = [row.strip().split("|") for row in table_text.split("\n")]
            headers = [cell.strip() for cell in rows[0] if cell.strip()]
            data = [[cell.strip() for cell in row if cell.strip()] for row in rows[2:]]
            df = pd.DataFrame(data, columns=headers)
            st.table(df)
        
        st.markdown(analysis_text)

    # 시나리오 데이터 시각화
    st.subheader(" 2025 시장 시나리오 분석")
    scenario_data = {
        '시나리오': ['낙관적', '중립적', '비관적'],
        '선점 가능성': [90, 60, 30],
        '리스크 수준': [20, 50, 80]
    }
    scenario_df = pd.DataFrame(scenario_data)

    # 시나리오 버블 차트
    bubble_chart = alt.Chart(scenario_df).mark_circle(size=300).encode(
        x=alt.X('시나리오:N', title=None),
        y=alt.Y('선점 가능성:Q', title='선점 가능성 (%)', scale=alt.Scale(domain=[0, 100])),
        size=alt.Size('리스크 수준:Q', legend=None),
        color=alt.Color('시나리오:N', legend=None),
        tooltip=['시나리오', '선점 가능성', '리스크 수준']
    ).properties(height=300)
    st.altair_chart(bubble_chart, use_container_width=True)

    # 경쟁사 비교 분석
    st.subheader(" 주요 경쟁사 비교 분석")
    competitor_data = {
        '브랜드': ['현대', '기아', 'BYD', '테슬라'],
        '시장점유율': [8.2, 7.5, 12.3, 37.9],
        '평균가격(만원)': [4500, 4200, 2800, 6500],
        '충전속도(km/10분)': [120, 115, 90, 150]
    }
    competitor_df = pd.DataFrame(competitor_data)

    # 경쟁사 레이더 차트
    radar_chart = alt.Chart(competitor_df).transform_fold(
        ['시장점유율', '평균가격(만원)', '충전속도(km/10분)'],
        as_=['metric', 'value']
    ).mark_line().encode(
        x=alt.X('metric:N', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('value:Q', scale=alt.Scale(zero=False)),
        color='브랜드:N',
        strokeDash='브랜드:N'
    ).properties(height=350)
    st.altair_chart(radar_chart, use_container_width=True)

    # 월별 추이 분석 강화
    st.subheader(" 월별 생산-판매-수출 상관관계 분석")
    # 월별 합계 계산 함수 정의
    def sum_by_month(df_):
        existing_cols = [c for c in month_cols if c in df_.columns]
        summed = df_[existing_cols].sum(numeric_only=True).reset_index(name="값").rename(columns={"index": "월"})
        return summed

    prod_m = sum_by_month(prod_filtered).rename(columns={"값": "생산량"})
    sales_m = sum_by_month(sales_filtered).rename(columns={"값": "판매량"})
    export_m = sum_by_month(export_filtered).rename(columns={"값": "수출량"})
    
    merged = prod_m.merge(sales_m, on="월", how="outer").merge(export_m, on="월", how="outer").fillna(0)
    
    # 히트맵 시각화
    heatmap = alt.Chart(merged.melt(id_vars="월")).mark_rect().encode(
        x=alt.X('month(월):O', title='월'),
        y=alt.Y('variable:N', title='지표'),
        color=alt.Color('value:Q', legend=alt.Legend(title="수량"))
    ).properties(height=250)
    st.altair_chart(heatmap, use_container_width=True)

    # 재고 분석 시각화 강화
    st.subheader(" 재고 분석 (차종별)")
    prod_group = prod_filtered.groupby(["브랜드", "차종"])[month_cols].sum(numeric_only=True).sum(axis=1).rename("누적생산")
    sales_group = sales_filtered.groupby(["브랜드", "차종"])[month_cols].sum(numeric_only=True).sum(axis=1).rename("누적판매")

    inventory_df = pd.merge(prod_group, sales_group, left_index=True, right_index=True, how="outer").fillna(0).reset_index()
    inventory_df["예상재고"] = inventory_df["누적생산"] - inventory_df["누적판매"]
    inventory_df["재고위험도"] = np.where(
        inventory_df["예상재고"] < 100, "위험", 
        np.where(inventory_df["예상재고"] > 10000, "과잉", "정상")
    )
    
    # 재고 분포 히스토그램
    hist = alt.Chart(inventory_df).mark_bar().encode(
        alt.X("예상재고:Q", bin=True, title="재고량"),
        alt.Y('count()', title="차종 수"),
        color=alt.Color('재고위험도:N', scale=alt.Scale(
            domain=['위험', '정상', '과잉'],
            range=['#ff4b4b', '#0068c9', '#ffa600']
        ))
    ).properties(height=300)
    st.altair_chart(hist, use_container_width=True)

    # 인사이트 시각화 강화
    st.subheader("주요 인사이트 시각화")
    
    # 상위 5개 모델 시각화
    if not sales_filtered.empty:
        top_models = sales_filtered.groupby("차종")[month_cols].sum(numeric_only=True).sum(axis=1).nlargest(5)
        model_chart = alt.Chart(top_models.reset_index()).mark_bar().encode(
            x=alt.X('차종:N', sort='-y'),
            y=alt.Y('0:Q', title='판매량'),
            color=alt.value('#0068c9')
        ).properties(height=300, title="TOP 5 인기 모델")
        st.altair_chart(model_chart, use_container_width=True)
    
    # 브랜드 비교 시각화
    if brand == "전체":
        brand_comparison = prod_df.groupby("브랜드")[month_cols].sum(numeric_only=True).sum(axis=1)
        brand_chart = alt.Chart(brand_comparison.reset_index()).mark_arc(innerRadius=50).encode(
            theta='0:Q',
            color='브랜드:N',
            tooltip=['브랜드', alt.Tooltip('0:Q', title='생산량')]
        ).properties(height=300, title="브랜드별 생산 비중")
        st.altair_chart(brand_chart, use_container_width=True)

    # 재고 경고 요약
    st.subheader("재고 경고 요약")
    low_stock = inventory_df[inventory_df["예상재고"] < 100]
    high_stock = inventory_df[inventory_df["예상재고"] > 10000]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 재고 부족 차종 (미만 100)")
        st.dataframe(low_stock, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("#### 재고 과잉 차종 (초과 10,000)")
        st.dataframe(high_stock, use_container_width=True, hide_index=True)

    # 인사이트 요약
    st.subheader("인사이트 요약")
    if not sales_filtered.empty:
        top_model = sales_filtered.groupby("차종")[month_cols].sum(numeric_only=True).sum(axis=1).sort_values(ascending=False).index[0]
        st.info(f"가장 많이 팔린 차종은 **{top_model}** 입니다.")
    else:
        st.info("판매 데이터가 없어, 가장 많이 팔린 차종을 알 수 없습니다.")

    if not inventory_df.empty:
        top_stock = inventory_df.sort_values("예상재고", ascending=False).iloc[0]["차종"]
        st.info(f"가장 많이 재고가 쌓인 차종은 **{top_stock}** 입니다.")
    else:
        st.info("재고 데이터가 없어, 재고가 가장 많은 차종을 알 수 없습니다.")

    st.subheader("리포트 다운로드")
    csv_bytes = inventory_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("재고 리포트 다운로드", data=csv_bytes, file_name="재고리포트.csv", mime="text/csv")

    def create_pdf():
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        font_path = "fonts/NanumGothic.ttf"
        if not os.path.exists(font_path):
            c.setFont("Helvetica", 12)
            c.drawString(30, height - 50, "[주의] 폰트 파일이 없어 기본 폰트를 사용합니다.")
        else:
            pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
            c.setFont("NanumGothic", 14)
            c.drawString(30, height - 50, f"ERP 분석 리포트 - {brand} {year}년")
