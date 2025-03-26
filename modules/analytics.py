import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def analytics_ui():
    st.title("📊 분석 리포트")

    @st.cache_data
    def load_data():
        # 1) CSV 로드
        prod_h = pd.read_csv("data/processed/현대_해외공장판매실적_전처리.CSV")
        prod_k = pd.read_csv("data/processed/기아_해외공장판매실적_전처리.CSV")
        sales_h = pd.read_csv("data/processed/현대_차종별판매실적_전처리.CSV")
        sales_k = pd.read_csv("data/processed/기아_차종별판매실적_전처리.CSV")
        export_h = pd.read_csv("data/processed/현대_지역별수출실적_전처리.CSV")
        export_k = pd.read_csv("data/processed/기아_지역별수출실적_전처리.CSV")

        # 2) 브랜드 컬럼 추가
        for df_, brand_ in [
            (prod_h, "현대"), (prod_k, "기아"),
            (sales_h, "현대"), (sales_k, "기아"),
            (export_h, "현대"), (export_k, "기아")
        ]:
            df_["브랜드"] = brand_

        # 3) 데이터프레임 병합
        prod_df_ = pd.concat([prod_h, prod_k], ignore_index=True)
        sales_df_ = pd.concat([sales_h, sales_k], ignore_index=True)
        export_df_ = pd.concat([export_h, export_k], ignore_index=True)

        # 4) 월별 컬럼 가정 (1월~12월)
        month_cols_ = [f"{i}월" for i in range(1, 13)]

        # 5) 월 컬럼이 있는 경우만 to_numeric 처리
        for df_ in [prod_df_, sales_df_, export_df_]:
            existing_month_cols = [c for c in month_cols_ if c in df_.columns]
            df_[existing_month_cols] = df_[existing_month_cols].apply(pd.to_numeric, errors='coerce')

        return prod_df_, sales_df_, export_df_

    # ✅ 데이터 로드
    prod_df, sales_df, export_df = load_data()

    # ✅ 필수 컬럼 체크 (연도 등)
    if "연도" not in prod_df.columns:
        st.error("❌ '연도' 컬럼이 존재하지 않습니다. 전처리 과정을 확인해 주세요.")
        return

    # ✅ 월 컬럼
    month_cols = [f"{i}월" for i in range(1, 13)]

    # ---------------------------
    # 필터
    # ---------------------------
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

    def apply_filters(df):
        if "연도" not in df.columns:
            return pd.DataFrame()  # 연도 없는 DF는 필터 불가
        filtered_df = df[df["연도"] == year]
        if brand != "전체":
            filtered_df = filtered_df[filtered_df["브랜드"] == brand]
        return filtered_df

    prod_filtered = apply_filters(prod_df)
    sales_filtered = apply_filters(sales_df)
    export_filtered = apply_filters(export_df)

    # ---------------------------
    # KPI 계산
    # ---------------------------
    total_prod = int(prod_filtered[month_cols].sum(numeric_only=True).sum(skipna=True))
    total_sales = int(sales_filtered[month_cols].sum(numeric_only=True).sum(skipna=True))
    total_export = int(export_filtered[month_cols].sum(numeric_only=True).sum(skipna=True))
    total_stock = total_prod - total_sales  # 음수 가능

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("총 생산량", f"{total_prod:,} 대")
    k2.metric("총 판매량", f"{total_sales:,} 대")
    k3.metric("총 수출량", f"{total_export:,} 대")
    k4.metric("예상 재고량", f"{total_stock:,} 대")

    # ---------------------------
    # 월별 추이 (생산/판매/수출)
    # ---------------------------
    st.subheader("📈 월별 판매 / 생산 / 수출 추이")
    def sum_by_month(df_):
        """df_에서 month_cols 컬럼 합계를 [월, 값] 형태로 변환"""
        existing_cols = [c for c in month_cols if c in df_.columns]
        # 존재하지 않는 월 컬럼이 있을 수도 있으니 필터링
        summed = df_[existing_cols].sum(numeric_only=True).reset_index(name="값").rename(columns={"index": "월"})
        return summed

    prod_m = sum_by_month(prod_filtered).rename(columns={"값": "생산량"})
    sales_m = sum_by_month(sales_filtered).rename(columns={"값": "판매량"})
    export_m = sum_by_month(export_filtered).rename(columns={"값": "수출량"})

    merged = prod_m.merge(sales_m, on="월", how="outer").merge(export_m, on="월", how="outer").fillna(0)
    melted = merged.melt(id_vars="월", var_name="구분", value_name="수량")

    chart = alt.Chart(melted).mark_line(point=True).encode(
        x="월",
        y=alt.Y("수량:Q", title="수량"),
        color="구분:N"
    ).properties(width=800, height=400)
    st.altair_chart(chart, use_container_width=True)

    # ---------------------------
    # 재고 경고
    # ---------------------------
    st.subheader("⚠️ 재고 경고 요약")

    # 생산, 판매 각각 브랜드+차종 묶음으로 월 컬럼 합산
    prod_group = prod_filtered.groupby(["브랜드", "차종"])[month_cols].sum(numeric_only=True).sum(axis=1).rename("누적생산")
    sales_group = sales_filtered.groupby(["브랜드", "차종"])[month_cols].sum(numeric_only=True).sum(axis=1).rename("누적판매")

    inventory_df = pd.merge(prod_group, sales_group, left_index=True, right_index=True, how="outer").fillna(0).reset_index()
    inventory_df["예상재고"] = inventory_df["누적생산"] - inventory_df["누적판매"]

    low_stock = inventory_df[inventory_df["예상재고"] < 100]
    high_stock = inventory_df[inventory_df["예상재고"] > 10000]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🚨 재고 부족 차종 (미만 100)")
        st.dataframe(low_stock, use_container_width=True, hide_index=True)

    with c2:
        st.markdown("#### 📦 재고 과잉 차종 (초과 10,000)")
        st.dataframe(high_stock, use_container_width=True, hide_index=True)

    # ---------------------------
    # 간단한 인사이트
    # ---------------------------
    st.subheader("💡 인사이트 요약")
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

    # ---------------------------
    # CSV 다운로드
    # ---------------------------
    st.subheader("📥 리포트 다운로드")
    csv_bytes = inventory_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 재고 리포트 다운로드", data=csv_bytes, file_name="재고리포트.csv", mime="text/csv")

    # ---------------------------
    # PDF 생성 함수
    # ---------------------------
    def create_pdf():
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # 폰트 파일 확인
        font_path = "fonts/NanumGothic.ttf"
        if not os.path.exists(font_path):
            c.setFont("Helvetica", 12)
            c.drawString(30, height - 50, "[주의] 폰트 파일이 없어 기본 폰트를 사용합니다.")
        else:
            pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
            c.setFont("NanumGothic", 14)
            c.drawString(30, height - 50, f"ERP 분석 리포트 - {brand} {year}년")

        c.setFont("Helvetica", 10)
        c.drawString(30, height - 80, f"총 생산량: {total_prod:,} 대")
        c.drawString(30, height - 100, f"총 판매량: {total_sales:,} 대")
        c.drawString(30, height - 120, f"총 수출량: {total_export:,} 대")
        c.drawString(30, height - 140, f"예상 재고량: {total_stock:,} 대")

        c.drawString(30, height - 170, f"재고 경고 요약:")
        y_pos = height - 190
        for i, row in low_stock.head(5).iterrows():
            c.drawString(40, y_pos, f"🚨 {row['브랜드']} - {row['차종']}: {int(row['예상재고'])} 대")
            y_pos -= 15
        for i, row in high_stock.head(5).iterrows():
            c.drawString(40, y_pos, f"📦 {row['브랜드']} - {row['차종']}: {int(row['예상재고'])} 대")
            y_pos -= 15

        y_pos -= 30
        c.drawString(30, y_pos, f"💡 분석 인사이트:")
        y_pos -= 20
        if not sales_filtered.empty:
            c.drawString(40, y_pos, f"가장 많이 팔린 차종: {top_model}")
            y_pos -= 20
        if not inventory_df.empty:
            c.drawString(40, y_pos, f"가장 많이 재고가 쌓인 차종: {top_stock}")
            y_pos -= 20

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    # ---------------------------
    # PDF 다운로드
    # ---------------------------
    pdf_file = create_pdf()
    st.download_button(
        "📄 PDF 리포트 다운로드",
        data=pdf_file,
        file_name=f"ERP_리포트_{brand}_{year}.pdf",
        mime="application/pdf"
    )
