import streamlit as st
import random
import time
from PIL import Image
import easyocr
import numpy as np
import re

# --- 앱 설정 ---
st.set_page_config(page_title="우리 아이 식단 매니저", layout="centered")

# --- 스타일 설정 (가독성 강화) ---
st.markdown("""
    <style>
    div.stButton > button { width: 100%; height: 60px; font-size: 18px !important; font-weight: bold; border-radius: 12px; margin-bottom: 10px; }
    .recipe-card { padding: 20px; border-radius: 15px; background-color: #ffffff; border: 1px solid #e0e0e0; margin-bottom: 15px; box-shadow: 2px 4px 10px rgba(0,0,0,0.05); }
    .meal-tag { background-color: #ffefef; color: #ff4b4b; padding: 2px 8px; border-radius: 5px; font-size: 0.8em; font-weight: bold; }
    .ingredient-list { background-color: #f9f9f9; padding: 10px; border-radius: 8px; font-size: 0.9em; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# --- 데이터 저장소 ---
if 'recipe_db' not in st.session_state:
    st.session_state.recipe_db = []
if 'page' not in st.session_state: st.session_state.page = "main"

# --- 텍스트 정제 함수 (사진 글자를 목록으로 변환) ---
def clean_recipe_text(text):
    # 재료 단위나 키워드 뒤에 줄바꿈 추가
    text = text.replace("재료", "\n[재료]\n").replace("방법", "\n[방법]\n")
    text = re.sub(r'(\d+g|\d+ml|\d+스푼|\d+T)', r'\1\n', text)
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

# --- [페이지 2] 레시피 등록 (보기 편한 나열) ---
elif st.session_state.page == "add":
    st.header("📝 레시피 정리하기")
    img_file = st.file_uploader("이미지 업로드", type=['jpg', 'png', 'jpeg'])
    
    if img_file:
        image = Image.open(img_file)
        st.image(image, use_container_width=True)
        
        if st.button("🔍 사진 분석해서 나열하기"):
            with st.spinner("글자를 읽어서 목록으로 만드는 중..."):
                reader = get_reader()
                result = reader.readtext(np.array(image), detail=0)
                raw_text = " ".join(result)
                
                # 가독성 있게 정리된 텍스트
                st.session_state.temp_ing = clean_recipe_text(raw_text)
                st.success("분석 완료! 아래 서식을 확인해주세요.")

    # 두 번째 사진처럼 깔끔하게 나열된 입력창
    st.subheader("🍴 메뉴 정보")
    title = st.text_input("메뉴 이름", placeholder="예: 한우 전분구이")
    
    st.subheader("🛒 재료 목록")
    ing = st.text_area("재료 (한 줄에 하나씩)", value=st.session_state.get('temp_ing', ''), height=150)
    
    st.subheader("👨‍🍳 요리 방법")
    method = st.text_area("순서대로 적어주세요", height=100)
    
    tag = st.selectbox("핵심 분류", ["소고기 (30g 필수)", "단백질", "채소", "기타"])
    
    if st.button("✅ 이대로 창고에 저장"):
        st.session_state.recipe_db.append({"title": title, "ingredients": ing, "method": method, "tag": tag})
        st.success("창고에 잘 보관되었습니다!")
        time.sleep(1)
        st.session_state.page = "main"; st.rerun()

    if st.button("🔙 돌아가기"): st.session_state.page = "main"; st.rerun()

# --- [페이지 3] 식단 짜기 (중복 방지) ---
elif st.session_state.page in ["plan_1", "plan_3"]:
    days = 1 if st.session_state.page == "plan_1" else 3
    st.header(f"🗓️ {days}일 권장 식단")
    
    beef_recipes = [r for r in st.session_state.recipe_db if "소고기" in r['tag']]
    other_recipes = [r for r in st.session_state.recipe_db if "소고기" not in r['tag']]

    if not beef_recipes:
        st.error("❗ 소고기 레시피가 최소 1개는 저장되어 있어야 식단을 짤 수 있어요.")
    else:
        for i in range(days):
            day_beef = random.choice(beef_recipes)
            day_others = random.sample(other_recipes, min(len(other_recipes), 2)) if len(other_recipes) >= 2 else other_recipes
            
            st.markdown(f"""
            <div class="recipe-card">
                <h3 style='margin:0;'>📅 Day {i+1}</h3>
                <p>🌅 아침: <b>{day_others[0]['title'] if len(day_others)>0 else '메뉴 등록 필요'}</b></p>
                <p>☀️ 점심: <b>{day_beef['title']}</b> <span class="meal-tag">철분 30g 필수</span></p>
                <p>🌙 저녁: <b>{day_others[1]['title'] if len(day_others)>1 else '메뉴 등록 필요'}</b></p>
                <div class="ingredient-list">
                    <b>오늘의 메인 재료:</b><br>{day_beef['ingredients']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    if st.button("🔙 홈으로"): st.session_state.page = "main"; st.rerun()

# --- [페이지 4] 창고 보기 ---
elif st.session_state.page == "storage":
    st.header("📂 레시피 창고")
    for idx, r in enumerate(st.session_state.recipe_db):
        with st.expander(f"{r['title']} ({r['tag']})"):
            st.markdown(f"**재료:**\n{r['ingredients']}")
            st.markdown(f"**방법:**\n{r['method']}")
            if st.button(f"삭제", key=f"del_{idx}"):
                st.session_state.recipe_db.pop(idx); st.rerun()
    if st.button("🔙 메인"): st.session_state.page = "main"; st.rerun()
