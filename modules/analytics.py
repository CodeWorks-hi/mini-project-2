# modules/analytics.py
# ----------------------------
# 분석 리포트 페이지
# - 다양한 시각화 기반 비교 분석, 추이 분석
# - 차종, 지역, 기간별 분석 중심
# ----------------------------

import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def analytics_ui():
    st.title("📊 분석 리포트")

    # 데이터 로드
    @st.cache_data
    def load_data():
        prod_h = pd.read_csv("data/processed/현대_해외공장판매실적_전처리.CSV")
        prod_k = pd.read_csv("data/processed/기아_해외공장판매실적_전처리.CSV")
        sales_h = pd.read_csv("data/processed/현대_차종별판매실적_전처리.CSV")
        sales_k = pd.read_csv("data/processed/기아_차종별판매실적_전처리.CSV")
        export_h = pd.read_csv("data/processed/현대_지역별수출실적_전처리.CSV")
        export_k = pd.read_csv("data/processed/기아_지역별수출실적_전처리.CSV")

        for df, brand in [(prod_h, "현대"), (prod_k, "기아"), (sales_h, "현대"), (sales_k, "기아"), (export_h, "현대"), (export_k, "기아")]:
            df["브랜드"] = brand

        prod_df = pd.concat([prod_h, prod_k], ignore_index=True)
        sales_df = pd.concat([sales_h, sales_k], ignore_index=True)
        export_df = pd.concat([export_h, export_k], ignore_index=True)

        month_cols = [f"{i}월" for i in range(1, 13)]
        for df in [prod_df, sales_df, export_df]:
            df[month_cols] = df[month_cols].apply(pd.to_numeric, errors='coerce')

        return prod_df, sales_df, export_df

    prod_df, sales_df, export_df = load_data()
    month_cols = [f"{i}월" for i in range(1, 13)]

    col1, col2 = st.columns(2)
    with col1:
        brand = st.selectbox("브랜드 선택", ["전체"] + sorted(prod_df["브랜드"].unique()), key="analytics_brand")
    with col2:
        year = st.selectbox("연도 선택", sorted(prod_df["연도"].dropna().unique(), reverse=True), key="analytics_year")

    def apply_filters(df):
        df = df[df["연도"] == year]
        if brand != "전체":
            df = df[df["브랜드"] == brand]
        return df

    prod_filtered = apply_filters(prod_df)
    sales_filtered = apply_filters(sales_df)
    export_filtered = apply_filters(export_df)

    total_prod = int(prod_filtered[month_cols].sum().sum())
    total_sales = int(sales_filtered[month_cols].sum().sum())
    total_export = int(export_filtered[month_cols].sum().sum())
    total_stock = total_prod - total_sales

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("총 생산량", f"{total_prod:,} 대")
    k2.metric("총 판매량", f"{total_sales:,} 대")
    k3.metric("총 수출량", f"{total_export:,} 대")
    k4.metric("예상 재고량", f"{total_stock:,} 대")

    st.subheader("📈 월별 판매 / 생산 / 수출 추이")
    prod_m = prod_filtered[month_cols].sum().reset_index(name="생산량").rename(columns={"index": "월"})
    sales_m = sales_filtered[month_cols].sum().reset_index(name="판매량").rename(columns={"index": "월"})
    export_m = export_filtered[month_cols].sum().reset_index(name="수출량").rename(columns={"index": "월"})

    merged = prod_m.merge(sales_m, on="월").merge(export_m, on="월")
    melted = merged.melt(id_vars="월", var_name="구분", value_name="수량")

    chart = alt.Chart(melted).mark_line(point=True).encode(
        x="월",
        y=alt.Y("수량:Q", title="수량"),
        color="구분:N"
    ).properties(width=800, height=400)
    st.altair_chart(chart, use_container_width=True)

    st.subheader("⚠️ 재고 경고 요약")
    inventory_df = pd.merge(
        prod_filtered.groupby(["브랜드", "차종"])[month_cols].sum().sum(axis=1).rename("누적생산"),
        sales_filtered.groupby(["브랜드", "차종"])[month_cols].sum().sum(axis=1).rename("누적판매"),
        left_index=True, right_index=True, how="outer"
    ).fillna(0).reset_index()
    inventory_df["예상재고"] = inventory_df["누적생산"] - inventory_df["누적판매"]

    low_stock = inventory_df[inventory_df["예상재고"] < 100]
    high_stock = inventory_df[inventory_df["예상재고"] > 10000]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🚨 재고 부족 차종")
        st.dataframe(low_stock, use_container_width=True, hide_index=True)
    with col2:
        st.markdown("#### 📦 재고 과잉 차종")
        st.dataframe(high_stock, use_container_width=True, hide_index=True)

    st.subheader("💡 인사이트 요약")
    top_model = sales_filtered.groupby("차종")[month_cols].sum().sum(axis=1).sort_values(ascending=False).index[0]
    top_stock = inventory_df.sort_values("예상재고", ascending=False).iloc[0]["차종"]
    st.info(f"가장 많이 팔린 차종은 **{top_model}** 입니다.")
    st.info(f"가장 많이 재고가 쌓인 차종은 **{top_stock}** 입니다.")

    st.subheader("📥 리포트 다운로드")
    csv = inventory_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 재고 리포트 다운로드", data=csv, file_name="재고리포트.csv", mime="text/csv")

    def create_pdf():
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        pdfmetrics.registerFont(TTFont("NanumGothic", "fonts/NanumGothic.ttf"))
        c.setFont("NanumGothic", 14)
        c.drawString(30, height - 50, f"ERP 분석 리포트 - {brand} {year}년")
        c.setFont("NanumGothic", 10)
        c.drawString(30, height - 80, f"총 생산량: {total_prod:,} 대")
        c.drawString(30, height - 100, f"총 판매량: {total_sales:,} 대")
        c.drawString(30, height - 120, f"총 수출량: {total_export:,} 대")
        c.drawString(30, height - 140, f"예상 재고량: {total_stock:,} 대")
        c.drawString(30, height - 170, f"재고 경고 요약:")

        for i, row in low_stock.head(5).iterrows():
            c.drawString(40, height - 190 - i*15, f"🚨 {row['브랜드']} - {row['차종']} : {int(row['예상재고'])} 대")
        for i, row in high_stock.head(5).iterrows():
            c.drawString(40, height - 280 - i*15, f"📦 {row['브랜드']} - {row['차종']} : {int(row['예상재고'])} 대")

        c.drawString(30, height - 380, f"💡 가장 많이 팔린 차종은 {top_model} 입니다.")
        c.drawString(30, height - 400, f"💡 재고가 가장 많은 차종은 {top_stock} 입니다.")
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    pdf_file = create_pdf()
    st.download_button("📄 PDF 리포트 다운로드", data=pdf_file, file_name=f"ERP_리포트_{brand}_{year}.pdf", mime="application/pdf")
