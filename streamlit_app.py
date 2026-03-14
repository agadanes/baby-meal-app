import streamlit as st
import random
import time
from PIL import Image
import easyocr
import numpy as np

# --- 앱 설정 ---
st.set_page_config(page_title="유아식 매니저", layout="centered")

# --- 스타일 설정 ---
st.markdown("""
    <style>
    div.stButton > button { width: 100%; height: 60px; font-size: 18px !important; font-weight: bold; border-radius: 12px; margin-bottom: 10px; }
    .recipe-card { padding: 15px; border-radius: 10px; background-color: #fef9e7; margin-bottom: 10px; border-left: 5px solid #ffcc00; }
    .storage-card { padding: 15px; border: 1px solid #eee; border-radius: 10px; margin-bottom: 10px; background: white; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 데이터 저장소 ---
if 'recipe_db' not in st.session_state:
    st.session_state.recipe_db = [
        {"title": "한우 팝콘", "ingredients": "소고기 다짐육 35g, 전분, 오트밀", "tag": "소고기"},
        {"title": "닭안심 감자볶음", "ingredients": "닭안심, 감자", "tag": "단백질"}
    ]
if 'page' not in st.session_state: st.session_state.page = "main"

# --- OCR 분석 함수 (무료) ---
@st.cache_resource
def get_reader():
    return easyocr.Reader(['ko', 'en'])

def extract_text(image):
    reader = get_reader()
    img_np = np.array(image)
    result = reader.readtext(img_np, detail=0)
    return " ".join(result)

# --- [페이지 1] 메인 화면 ---
if st.session_state.page == "main":
    st.title("👶 유아식 식단 도우미")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📸 레시피 등록"):
            st.session_state.page = "add"
            st.rerun()
    with col2:
        if st.button("📂 레시피 창고"):
            st.session_state.page = "storage"
            st.rerun()
            
    if st.button("📅 오늘 식단 짜기"):
        st.session_state.page = "plan_1"
        st.rerun()
    if st.button("🗓️ 3일치 식단 짜기"):
        st.session_state.page = "plan_3"
        st.rerun()

# --- [페이지 2] 레시피 등록 (진짜 분석!) ---
elif st.session_state.page == "add":
    st.header("📝 새 레시피 추가")
    img_file = st.file_uploader("레시피 사진 업로드", type=['jpg', 'png', 'jpeg'])
    
    extracted_title = ""
    extracted_ing = ""

    if img_file:
        image = Image.open(img_file)
        st.image(image, caption="분석할 사진", use_container_width=True)
        
        if st.button("🔍 사진에서 글자 읽어오기"):
            with st.spinner("AI가 사진 속 글자를 읽고 있습니다..."):
                text = extract_text(image)
                # 간단한 로직으로 제목과 재료 분리 시도
                extracted_title = text[:15] + "..." if len(text) > 15 else text
                extracted_ing = text
                st.success("분석 완료! 아래 내용을 확인하고 수정해주세요.")

    title = st.text_input("메뉴 이름", value=extracted_title)
    ing = st.text_area("재료 및 상세내용", value=extracted_ing, height=150)
    tag = st.selectbox("핵심 재료", ["소고기", "단백질", "채소", "기타"])
    
    if st.button("✅ 창고에 저장하기"):
        st.session_state.recipe_db.append({"title": title, "ingredients": ing, "tag": tag})
        st.success("저장되었습니다!")
        time.sleep(1)
        st.session_state.page = "main"
        st.rerun()

    if st.button("🔙 돌아가기"):
        st.session_state.page = "main"
        st.rerun()

# --- [페이지 3] 레시피 창고 보기 ---
elif st.session_state.page == "storage":
    st.header("📂 내 레시피 창고")
    if not st.session_state.recipe_db:
        st.write("아직 저장된 레시피가 없어요.")
    else:
        for idx, r in enumerate(st.session_state.recipe_db):
            with st.container():
                st.markdown(f"""
                <div class="storage-card">
                    <b>{idx+1}. {r['title']}</b> <span style='color:blue'>#{r['tag']}</span><br>
                    <p style='font-size:14px; color:#666;'>{r['ingredients']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🗑️ {idx+1}번 삭제", key=f"del_{idx}"):
                    st.session_state.recipe_db.pop(idx)
                    st.rerun()

    if st.button("🔙 메인으로 돌아가기"):
        st.session_state.page = "main"
        st.rerun()

# --- [페이지 4] 식단 결과 (유지) ---
elif st.session_state.page in ["plan_1", "plan_3"]:
    days = 1 if st.session_state.page == "plan_1" else 3
    st.header(f"🗓️ {days}일 식단 계획")
    for i in range(days):
        beef = [r for r in st.session_state.recipe_db if "소고기" in r['tag']]
        others = [r for r in st.session_state.recipe_db if "소고기" not in r['tag']]
        
        st.markdown(f"""<div class="recipe-card">
            <b>Day {i+1}</b><br>
            🌅 아침: {random.choice(st.session_state.recipe_db)['title']}<br>
            ☀️ 점심: {random.choice(beef)['title'] if beef else "소고기 메뉴를 추가해주세요"}<br>
            🌙 저녁: {random.choice(others)['title'] if others else "메뉴가 더 필요해요"}
        </div>""", unsafe_allow_html=True)
    if st.button("🔙 홈으로 돌아가기"):
        st.session_state.page = "main"
        st.rerun()
