import streamlit as st
import re
import requests
import torch
from PIL import Image
from io import BytesIO
from transformers import AutoProcessor, LlavaForConditionalGeneration
from huggingface_hub import InferenceClient

# =====================
# 설정
# =====================
VISION_MODEL_ID = "llava-hf/llava-1.5-7b-hf"
TEXT_MODEL_ID = "google/gemma-2-9b-it"
MAX_IMAGE_SIZE = 2048

# =====================
# 토큰 로딩
# =====================
def get_huggingface_tokens():
    return {
        "llava": st.secrets.get("HUGGINGFACE_API_TOKEN_LLAVA"),
        "gemma": st.secrets.get("HUGGINGFACE_API_TOKEN_GEMMA")
    }

def get_huggingface_token(model_type):
    return get_huggingface_tokens().get(model_type)

# =====================
# 입력 정제
# =====================
def clean_input(text: str) -> str:
    return re.sub(r"\b(해줘|알려줘|설명해 줘|말해 줘)\b", "", text, flags=re.IGNORECASE).strip()

# =====================
# 텍스트 생성 (Gemma API)
# =====================
def generate_text_via_api(prompt: str, model_name: str = TEXT_MODEL_ID) -> str:
    token = get_huggingface_token("gemma")
    if not token:
        st.error("❌ Hugging Face API 토큰이 없습니다.")
        return ""

    prompt_additions = [
        "한국어로 번역해서 작성해줘",
        "시장 데이터를 기반으로 구체적인 근거를 포함해줘",
        "긍정적/부정적 요인을 나눠서 정리해줘",
        "3가지 시나리오(낙관/중립/비관)로 예측해줘",
        "간결하게 핵심 위주로 요약해줘 (500자 이내)"
    ]

    enhanced_prompt = f"{prompt}\n\n추가 지시사항:\n" + "\n".join(prompt_additions)

    try:
        client = InferenceClient(model=model_name, token=token)
        response = client.text_generation(
            prompt=f"전문가처럼 다음 요청에 대해 분석해줘:\n{enhanced_prompt}",
            max_new_tokens=512,
            temperature=0.7
        )
        return response
    except Exception as e:
        st.error(f"API 오류: {e}")
        return ""

# =====================
# 이미지 분석 (LLaVA 로컬 실행)
# =====================
def analyze_image_with_llava(image: Image.Image, question: str) -> str:
    processor = AutoProcessor.from_pretrained(VISION_MODEL_ID)
    model = LlavaForConditionalGeneration.from_pretrained(
        VISION_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )

    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": question}
        ],
    }]

    inputs = processor(
        text=processor.apply_chat_template(messages, add_generation_prompt=True),
        images=image,
        return_tensors="pt"
    ).to(model.device, torch.bfloat16)

    output = model.generate(
        **inputs,
        max_new_tokens=256,
        temperature=0.3,
        top_p=0.95,
        do_sample=True,
        repetition_penalty=1.2,
        use_cache=True
    )

    result = processor.decode(
        output[0],
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True
    )
    return result

# =====================
# Streamlit UI
# =====================
def recommendations_ui():
    st.title("🤖 AI 수출 분석 & 차량 추천 시스템")
    st.info("차량 이미지나 질문을 업로드하면 분석과 예측을 제공합니다.")

    with st.form("recommend_form"):
        image_file = st.file_uploader("📷 차량 또는 문서 이미지 업로드 (선택)", type=["jpg", "png"])
        user_input = st.text_area(
            "📝 분석 질문 입력",
            placeholder="예: 북미 시장에서 이 전기 SUV의 수요 예측",
            height=120
        )
        submitted = st.form_submit_button("🚀 분석 실행")

    if submitted:
        results = []

        # 이미지 처리
        if image_file:
            try:
                image = Image.open(image_file).convert("RGB")
                st.image(image, caption="업로드한 이미지", use_column_width=True)
                with st.spinner("🔍 이미지 분석 중..."):
                    result_img = analyze_image_with_llava(image, user_input or "이 차량의 특징과 시장 분석을 해줘")
                    results.append(f"### 🔍 이미지 분석 결과\n{result_img}")
            except Exception as e:
                st.error(f"이미지 처리 오류: {e}")

        # 텍스트 분석
        if user_input:
            with st.spinner("📊 텍스트 기반 예측 생성 중..."):
                cleaned = clean_input(user_input)
                result_text = generate_text_via_api(cleaned)
                results.append(f"### 📊 종합 분석 결과\n{result_text}")

        # 결과 출력
        if results:
            st.divider()
            for r in results:
                st.markdown(r)
        else:
            st.warning("입력 내용 또는 이미지를 확인해주세요.")
