# modules/dashboard_cards.py
# ----------------------------
# KPI 카드 시각화 컴포넌트 모듈
# - 판매 로그 관리 기능
# - 국가별 수출 현황 분석
# ----------------------------

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import Optional, Tuple

# 상수 정의
CSV_PATH = "data/processed/sales_records.csv"
DELETED_LOG_PATH = "data/processed/deleted_log.csv"
BACKUP_PATH = "data/processed/backups/"

def load_sales_data() -> pd.DataFrame:
    """판매 데이터 로드 함수"""
    try:
        df = pd.read_csv(CSV_PATH, parse_dates=['판매일'])
        df.insert(0, '고유ID', range(1, 1 + len(df)))
        return df
    except FileNotFoundError:
        st.error("판매 기록 파일을 찾을 수 없습니다")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터 로드 오류: {str(e)}")
        return pd.DataFrame()

def apply_filters(df: pd.DataFrame, models: list, dates: list) -> pd.DataFrame:
    """데이터 필터링 함수"""
    filtered = df.copy()
    if models:
        filtered = filtered[filtered["모델명"].isin(models)]
    if len(dates) == 2:
        start, end = dates
        filtered = filtered[
            (filtered["판매일"] >= pd.to_datetime(start)) &
            (filtered["판매일"] <= pd.to_datetime(end))
        ]
    return filtered

def backup_data(df: pd.DataFrame) -> None:
    """데이터 백업 생성"""
    os.makedirs(BACKUP_PATH, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_PATH, f"sales_backup_{timestamp}.csv")
    df.to_csv(backup_file, index=False)

def handle_deletions(original_df: pd.DataFrame, edited_df: pd.DataFrame) -> None:
    """삭제 처리 핸들러"""
    deleted_rows = edited_df[edited_df["삭제"]]
    if not deleted_rows.empty:
        backup_data(original_df)
        deleted_rows['삭제일시'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if os.path.exists(DELETED_LOG_PATH):
            existing_log = pd.read_csv(DELETED_LOG_PATH)
            deleted_rows = pd.concat([existing_log, deleted_rows], ignore_index=True)
            
        deleted_rows.to_csv(DELETED_LOG_PATH, index=False)
        remaining_ids = edited_df[~edited_df["삭제"]]['고유ID']
        original_df[original_df['고유ID'].isin(remaining_ids)].to_csv(CSV_PATH, index=False)
        st.success(f"✅ {len(deleted_rows)}건 삭제 완료 | 백업: {BACKUP_PATH}")
        st.experimental_rerun()

def show_sales_log_table():
    """판매 로그 관리 메인 인터페이스"""
    st.subheader("📋 판매 내역 관리")
    df = load_sales_data()
    if df.empty:
        return

    with st.expander("🔍 상세 필터 설정", expanded=True):
        col1, col2, col3 = st.columns([2,2,1])
        with col1:
            model_filter = st.multiselect(
                "모델명 선택", 
                df["모델명"].unique(),
                format_func=lambda x: f"{x} ({df[df['모델명']==x].shape[0]}건)"
            )
        with col2:
            date_filter = st.date_input(
                "판매일 범위 선택",
                [df['판매일'].min(), df['판매일'].max()]
            )
        with col3:
            st.write("<br>", unsafe_allow_html=True)
            show_all = st.checkbox("전체 보기", True)

    filtered_df = apply_filters(df, model_filter, date_filter)
    if not show_all and not filtered_df.empty:
        filtered_df = filtered_df.sample(frac=0.3)

    if not filtered_df.empty:
        filtered_df["삭제"] = False
        cols = ["삭제"] + [col for col in filtered_df.columns if col != "삭제"]
        
        edited_df = st.data_editor(
            filtered_df[cols],
            column_config={
                "삭제": st.column_config.CheckboxColumn("삭제", help="삭제할 항목 선택"),
                "고유ID": None
            },
            disabled=["판매일", "모델명", "수량", "지역", "담당자", "차종", "가격"],
            use_container_width=True,
            hide_index=True,
            key=f"sales_editor_{datetime.now().timestamp()}"
        )

        col1, col2 = st.columns([3,1])
        with col2:
            if st.button("🗑️ 선택 항목 삭제", type="primary"):
                handle_deletions(df, edited_df)
        with col1:
            st.download_button(
                "💾 현재 데이터 내보내기",
                data=filtered_df.drop(columns=["삭제", "고유ID"]).to_csv(index=False).encode("utf-8-sig"),
                file_name=f"sales_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        with st.expander("📊 실시간 통계 요약"):
            col1, col2, col3 = st.columns(3)
            col1.metric("총 판매량", f"{df['수량'].sum():,}대")
            col2.metric("평균 단가", f"₩{df['가격'].mean():,.0f}")
            col3.metric("진행 중인 삭제", f"{len(edited_df[edited_df['삭제']])}건")
    else:
        st.info("📭 조건에 맞는 판매 기록이 없습니다")

def render_top_bottom_countries(data: pd.DataFrame):
    """상위/하위 수출국 분석 카드 렌더링"""
    st.subheader("🌍 국가별 수출 현황 분석")
    
    # 분석 데이터 생성
    top5 = data.nlargest(5, '총수출')
    bottom5 = data.nsmallest(5, '총수출')
    
    # 시각화 섹션
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("##### 🏆 상위 5개 수출국")
            st.dataframe(
                top5[['지역명', '총수출']],
                column_config={"총수출": st.column_config.NumberColumn(format="%,d 대")},
                hide_index=True
            )
    
    with col2:
        with st.container(border=True):
            st.markdown("##### 📉 하위 5개 수출국")
            st.dataframe(
                bottom5[['지역명', '총수출']],
                column_config={"총수출": st.column_config.NumberColumn(format="%,d 대")},
                hide_index=True
            )

# 테스트 실행 블록
if __name__ == "__main__":
    # 샘플 데이터 생성
    test_data = pd.DataFrame({
        '지역명': ['미국', '중국', '일본', '독일', '영국', '프랑스', '이탈리아'],
        '총수출': [15000, 12000, 9000, 7500, 6000, 4500, 3000]
    })
    
    # 기능 테스트
    show_sales_log_table()
    render_top_bottom_countries(test_data)
