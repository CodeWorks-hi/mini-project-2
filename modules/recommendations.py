import streamlit as st
import re
from huggingface_hub import InferenceClient

# Constants
TEXT_MODEL_ID = "google/gemma-2-9b-it"

# Helper functions
def get_huggingface_token(model_type):
    tokens = {"gemma": st.secrets.get("HUGGINGFACE_API_TOKEN_GEMMA")}
    return tokens.get(model_type)

def clean_input(text: str) -> str:
    return re.sub(r"(해줘|알려줘|설명해 줘|말해 줘)", "", text).strip()

def generate_text_via_api(prompt: str, model_name: str = TEXT_MODEL_ID) -> str:
    token = get_huggingface_token("gemma")
    if not token:
        st.error("❌ Hugging Face API 토큰이 없습니다.")
        return ""

    system_prompt = """
    [시스템 지시사항]
    ### 1. 분석 요구사항
    **🖼️ 이미지 분석**
    - 차량 모델 특성 식별:
    - 연식: ±1년 오차 허용 (예: 2024-2026)
    - 디자인 요소: 전면 그릴/헤드라이트/휠 디자인 상세 분석
    - 기술 사양: 배터리 용량 (±5kWh), 주행거리 (NEDC ±30km)

    **📝 텍스트 분석**
    - 현대차그룹 2025 목표: 739만 대 중 전기차 67만 대
    - 글로벌 전기차 시장: 2025년 1,160만 대 (전년比 +30%)
    - 리스크: BYD 가격경쟁, Euro7 규제, 충전 표준화 지연

    ### 2. 출력 형식
    ## 2025 현대/기아 전기차 전략 보고서
    | 구분 | 2024 | 2025예상 | 비중 |
    |------|------|----------|------|
    | 글로벌 시장 | 890만 | 1,160만 | +30% |
    | 현대/기아 | 48만 | 67만 | 7.2% |

    - 리스크 요인: 가격경쟁, 규제비용 증가
    - 전략: 북미 아이오닉9, 유럽 EV5 확대, 중국 X-GMP 투자
    """

    text_prompt = [
        "한국어로 번역해서 작성해줘",
        "현대&기아 분석을 중점으로 작성해줘",
        "AI 학습 모델의 분석을 기준으로 작성해줘",
        "최근 10년간의 데이터를 기반으로 작성해줘",
        "글로벌 시장을 중심으로 작성해줘",
        "최근 5년간의 트렌드를 기반으로 작성해줘",
        "현재 뉴스를 참고해서 분석해줘",
        "시장 데이터를 기반으로 구체적인 근거를 포함해줘",
        "표 형식으로 정리해줘",
        "긍정적/부정적 요인을 나눠서 정리해줘",
        "3가지 시나리오(낙관/중립/비관)로 예측해줘",
        "간결하게 핵심 위주로 요약해줘",
        "전문가처럼 객관적인 톤으로 설명해줘",
        "최근 1년간 변화된 흐름을 반영해서 설명해줘",
        "시장흐름을 우선적으로 언급하고 다음에 주요 리스크 요인을 언급해줘",
        "예상 수치를 포함해 구체적으로 설명해줘"
    ]

    full_prompt = f"{system_prompt}\n\n[사용자 질문]\n{prompt}\n\n[추가 지시사항]\n" + "\n".join(text_prompt)

    try:
        client = InferenceClient(model=model_name, token=token)
        response = client.text_generation(
            prompt=f"다음 요청에 맞는 분석을 전문가처럼 700자 내외로 요약해줘:\n{full_prompt}",
            max_new_tokens=700,
            temperature=0.7
        )
        return response
    except Exception as e:
        st.error(f"텍스트 생성 오류: {e}")
        return ""

# Streamlit UI
def recommendations_ui():
    st.title("🤖 AI 추천 시스템")
    st.markdown("""
        이 시스템은 Gemma AI를 활용한 텍스트 분석 및 시장 예측을 지원합니다.
        사용자가 입력한 질문에 대한 텍스트 분석 결과를 제공합니다.
    """)
    st.info("💡 예측의 경우 분석이 아니므로 ")

    with st.form("analyze_form"):
        user_input = st.text_area("📝 분석할 질문 입력", placeholder="예: 2025년 미국 수출 예측해줘 ")
        submitted = st.form_submit_button("🚀 분석 실행")

    if submitted:
        st.markdown("---")
        if user_input:
            with st.spinner("📊 텍스트 기반 시장 예측 중..."):
                cleaned = clean_input(user_input)
                result_txt = generate_text_via_api(cleaned)
                st.markdown(f"### 📊 종합 분석 결과\n{result_txt}")
        else:
            st.warning("입력 내용을 확인해주세요.")



