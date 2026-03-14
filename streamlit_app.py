import streamlit as st
import random
import time
from PIL import Image
import easyocr
import numpy as np
import re

# --- 앱 설정 ---
st.set_page_config(page_title="똑똑 유아식 매니저", layout="centered")

# --- 스타일 설정 ---
st.markdown("""
    <style>
    div.stButton > button { width: 100%; height: 60px; font-size: 18px !important; font-weight: bold; border-radius: 12px; margin-bottom: 10px; }
    .recipe-card { padding: 20px; border-radius: 15px; background-color: #ffffff; border: 1px solid #e0e0e0; margin-bottom: 15px; box-shadow: 2px 4px 10px rgba(0,0,0,0.05); }
    .meal-tag { background-color: #ffefef; color: #ff4b4b; padding: 2px 8px; border-radius: 5px; font-size: 0.8em; font-weight: bold; }
    .ingredient-display { background-color: #f1f3f5; padding: 12px; border-radius: 8px; font-size: 0.95em; line-height: 1.8; white-space: pre-wrap; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 데이터 저장소 ---
if 'recipe_db' not in st.session_state:
    st.session_state.recipe_db = []
if 'page' not in st.session_state: st.session_state.page = "main"

# --- [핵심] 텍스트 정제 함수 (더 강력한 규칙) ---
def smart_clean_text(text):
    # 1. 쓸데없는 공백 정리
    text = re.sub(r'\s+', ' ', text)
    
    # 2. 주요 키워드 앞에서 강제 줄바꿈
    keywords = ['재료', '방법', '만드는 법', '준비물', '순서']
    for k in keywords:
        text = text.replace(k, f"\n\n[{k}]\n")
    
    # 3. 재료 단위 뒤에서 줄바꿈 (g, ml, 스푼, T, 알, 개 등)
    text = re.sub(r'(\d+\s?[gGmlL]|[T|t]|스푼|알|개|컵|작은술|큰술)', r'\1\n', text)
    
    # 4. 문장 마침표나 번호 뒤에서 줄바꿈 (방법 나열용)
    text = re.sub(r'(\d\.)', r'\n\1', text)
    
    return text.strip()

# --- OCR 분석 함수 ---
@st.cache_resource
def get_reader():
    return easyocr.Reader(['ko', 'en'])

# --- [페이지 1] 메인 화면 ---
if st.session_state.page == "main":
    st.title("👶 아이 식단 매니저")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📸 레시피 등록"): st.session_state.page = "add"; st.rerun()
    with col2:
        if st.button("📂 레시피 창고"): st.session_state.page = "storage"; st.rerun()
    if st.button("📅 오늘 식단 짜기"): st.session_state.page = "plan_1"; st.rerun()
    if st.button("🗓️ 3일치 식단 짜기"): st.session_state.page = "plan_3"; st.rerun()

# --- [페이지 2] 레시피 등록 ---
elif st.session_state.page == "add":
    st.header("📝 레시피 정리하기")
    img_file = st.file_uploader("이미지 업로드", type=['jpg', 'png', 'jpeg'])
    
    if img_file:
        image = Image.open(img_file)
        st.image(image, use_container_width=True)
        
        if st.button("🔍 사진 분석해서 목록 만들기"):
            with st.spinner("AI가 글자를 읽어서 정리 중입니다..."):
                reader = get_reader()
                result = reader.readtext(np.array(image), detail=0)
                raw_text = " ".join(result)
                # 정제된 텍스트를 세션에 저장
                st.session_state.temp_ing = smart_clean_text(raw_text)
                st.success("분석 완료! 아래 칸에서 필요한 부분만 남기고 수정해주세요.")

    title = st.text_input("🍴 메뉴 이름", placeholder="예: 한우 전분구이")
    
    # 정제된 텍스트가 들어가는 곳 (사용자가 편집하기 훨씬 쉬워짐)
    ing = st.text_area("🛒 재료 및 방법 (정리된 목록)", value=st.session_state.get('temp_ing', ''), height=250)
    
    tag = st.selectbox("핵심 분류", ["소고기 (30g 필수)", "단백질", "채소", "기타"])
    
    if st.button("✅ 이대로 창고에 저장"):
        # 재료와 방법을 굳이 나누지 않고 하나의 리스트로 저장해도 보기 편하게 구성
        st.session_state.recipe_db.append({"title": title, "content": ing, "tag": tag})
        st.success("창고에 잘 보관되었습니다!")
        time.sleep(1)
        st.session_state.page = "main"; st.rerun()
    
    if st.button("🔙 돌아가기"): st.session_state.page = "main"; st.rerun()

# --- [페이지 3] 레시피 창고 (화면 개선) ---
elif st.session_state.page == "storage":
    st.header("📂 레시피 창고")
    if not st.session_state.recipe_db:
        st.write("아직 저장된 레시피가 없어요.")
    else:
        for idx, r in enumerate(st.session_state.recipe_db):
            with st.expander(f"🍴 {r['title']} ({r['tag']})"):
                # 저장된 내용을 줄바꿈 그대로 보여줌
                st.markdown(f"**상세 내용:**")
                st.markdown(f"<div class='ingredient-display'>{r['content']}</div>", unsafe_allow_html=True)
                if st.button(f"{idx+1}번 레시피 삭제", key=f"del_{idx}"):
                    st.session_state.recipe_db.pop(idx); st.rerun()
    if st.button("🔙 메인으로"): st.session_state.page = "main"; st.rerun()

# --- [페이지 4] 식단 결과 ---
elif st.session_state.page in ["plan_1", "plan_3"]:
    days = 1 if st.session_state.page == "plan_1" else 3
    st.header(f"🗓️ {days}일 권장 식단")
    
    beef_recipes = [r for r in st.session_state.recipe_db if "소고기" in r['tag']]
    other_recipes = [r for r in st.session_state.recipe_db if "소고기" not in r['tag']]

    if not beef_recipes:
        st.error("❗ 소고기 레시피가 있어야 식단을 짤 수 있어요.")
    else:
        for i in range(days):
            day_beef = random.choice(beef_recipes)
            # 식단 구성 로직
            st.markdown(f"""
            <div class="recipe-card">
                <h3 style='margin:0;'>📅 Day {i+1}</h3>
                <p>☀️ 점심(철분필수): <b>{day_beef['title']}</b> <span class="meal-tag">소고기 30g</span></p>
                <div class='ingredient-display' style='font-size:0.85em;'>{day_beef['content'][:100]}...</div>
            </div>
            """, unsafe_allow_html=True)
    if st.button("🔙 홈으로"): st.session_state.page = "main"; st.rerun()
