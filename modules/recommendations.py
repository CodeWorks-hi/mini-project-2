# pages/recommendations.py
# ----------------------------
# AI 추천 시스템
# ----------------------------

import streamlit as st
import re
import pandas as pd
from huggingface_hub import InferenceClient

# 🔹 Hugging Face API 토큰 로딩

def get_huggingface_token():
    """환경 변수 또는 Streamlit secrets에서 Hugging Face API 토큰을 가져옵니다."""
    return st.secrets.get("HUGGINGFACE_API_TOKEN")

# 🔹 프롬프트 정제 함수

def clean_input(text: str) -> str:
    """불필요한 단어 제거 후 정제된 입력 반환"""
    return re.sub(r"\b(해줘|알려줘|설명해 줘|말해 줘)\b", "", text, flags=re.IGNORECASE).strip()

# 🔹 텍스트 생성 함수

def generate_text_via_api(prompt: str, model_name: str = "google/gemma-2-9b-it") -> str:
    """Hugging Face API를 사용하여 텍스트 생성"""
    token = get_huggingface_token()
    if not token:
        st.error("Hugging Face API 토큰이 설정되지 않았습니다. secrets.toml 확인 필요.")
        return ""
    try:
        client = InferenceClient(model=model_name, api_key=token)
        response = client.text_generation(
            prompt=f"다음 요청에 맞는 분석 및 예측 정보를 전문가의 시각으로 500자 내외로 작성해줘:\n{prompt}",
            max_new_tokens=512,
            temperature=0.7
        )
        return response
    except Exception as e:
        st.error(f"API 호출 중 오류 발생: {str(e)}")
        return ""

# 🔹 Streamlit UI 진입점

def recommendations_ui():
    st.title("🤖 AI 추천 시스템")
    st.info("차량 수요 예측 또는 모델 추천 결과가 여기에 표시됩니다.")

    with st.form("recommend_form"):
        user_input = st.text_area(
            "🔍 추천 요청 문장",
            placeholder="예: 2025년 미국 시장에서 전기 SUV 수요 예측",
            height=120
        )

        submitted = st.form_submit_button("🚀 추천 실행")

    if submitted and user_input:
        clean_prompt = clean_input(user_input)
        with st.spinner("AI가 추천을 생성 중입니다..."):
            output = generate_text_via_api(clean_prompt)

        st.divider()
        st.subheader(" 추천 결과")
        st.success(output.strip())
