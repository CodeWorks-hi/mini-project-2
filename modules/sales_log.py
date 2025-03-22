import streamlit as st
import pandas as pd
import os

CSV_PATH = "data/세일즈파일/sales_records.csv"
DELETED_LOG_PATH = "data/processed/deleted_log.csv"

def show_sales_log_table(df: pd.DataFrame):
    st.subheader("📋 판매 내역 관리")

    with st.expander("🔍 필터 옵션"):
        col1, col2 = st.columns(2)
        with col1:
            model_filter = st.multiselect("모델명 필터", df["모델명"].unique())
        with col2:
            date_filter = st.date_input("판매일 필터", [])

    filtered_df = df.copy()
    if model_filter:
        filtered_df = filtered_df[filtered_df["모델명"].isin(model_filter)]
    if isinstance(date_filter, list) and len(date_filter) == 2:
        start, end = map(str, date_filter)
        filtered_df = filtered_df[
            (filtered_df["판매일"] >= start) & (filtered_df["판매일"] <= end)
        ]

    if not filtered_df.empty:
        filtered_df["삭제"] = False

        edited_df = st.data_editor(
            filtered_df,
            column_config={
                "삭제": st.column_config.CheckboxColumn("삭제", help="삭제할 항목 체크")
            },
            disabled=["판매일", "모델명", "수량", "지역", "담당자", "차종", "가격"],
            use_container_width=True,
            key="sales_log_editor"
        )

        if st.button("🗑️ 선택 항목 삭제하기"):
            delete_rows = edited_df[edited_df["삭제"] == True].drop(columns=["삭제"])
            keep_rows = df[~df.apply(tuple, axis=1).isin(delete_rows.apply(tuple, axis=1))]

            if not delete_rows.empty:
                if os.path.exists(DELETED_LOG_PATH):
                    deleted_log = pd.read_csv(DELETED_LOG_PATH)
                    delete_rows = pd.concat([deleted_log, delete_rows], ignore_index=True)
                delete_rows.to_csv(DELETED_LOG_PATH, index=False)

            keep_rows.to_csv(CSV_PATH, index=False)
            st.success(f"✅ {len(delete_rows)}건 삭제됨. 로그 저장 완료.")
            st.experimental_rerun()

        st.download_button(
            "📤 필터된 결과 다운로드",
            data=filtered_df.drop(columns=["삭제"]).to_csv(index=False).encode("utf-8-sig"),
            file_name="filtered_sales_records.csv"
        )
    else:
        st.info("📭 표시할 판매 기록이 없습니다.")
