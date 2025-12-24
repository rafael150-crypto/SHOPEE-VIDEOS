import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time

# Configuração da Página
st.set_page_config(page_title="BrendaBot Shopee Seller", page_icon="🧡", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .status-box { padding: 20px; border-radius: 15px; margin-bottom: 25px; text-align: center; }
    .safe-bg { background-color: #fff5f2; color: #ee4d2d; border: 2px solid #ee4d2d; }
    .warning-bg { background-color: #fff9e6; color: #d69e2e; border: 2px solid #d69e2e; }
    .danger-bg { background-color: #fff0f0; color: #e53e3e; border: 2px solid #e53e3e; }
    .asset-card { background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #ee4d2d; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🧡 BrendaBot Shopee Seller")

# API KEY - Recomendo usar st.secrets["GEMINI_API_KEY"] no Streamlit Cloud
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

uploaded_file = st.file_uploader("📂 Suba o vídeo do Produto", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
        tfile.write(uploaded_file.read())
        file_path = tfile.name
    
    with st.spinner("📦 Validando conversão e gerando legenda curta..."):
        try:
            media_file = genai.upload_file(path=file_path)
            while media_file.name and genai.get_file(media_file.name).state.name == "PROCESSING":
                time.sleep(2)
            
            prompt = """
            Atue como Especialista em Shopee Vídeos.
            1. [PONTUACAO_VENDA]: Nota de 0 a 100.
            2. LEGENDA_CURTA: Crie uma legenda com NO MÁXIMO 140 caracteres (para sobrar espaço para emojis). Foque em benefício e cupom.
            3. HASHTAGS: 3 hashtags (ex: #shopee #achadinhos).
            4. AUDITORIA: Analise risco de banimento (conteúdo estático ou marca d'água).
            5. CAPA: segundo sugerido.
            """
            
            response = model.generate_content([media_file, prompt])
            texto_ia = response.text
            
            score = int(re.search(r'\[PONTUACAO_VENDA\]:\s*(\d+)', texto_ia).group(1)) if "[" in texto_ia else 50
            
            # --- STATUS ---
            if score >= 75: label, bg_class = "🚀 ALTO POTENCIAL", "safe-bg"
            elif score >= 45: label, bg_class = "⚖️ MÉDIO POTENCIAL", "warning-bg"
            else: label, bg_class = "⚠️ BAIXA CONVERSÃO", "danger-bg"

            st.markdown(f'<div class="status-box {bg_class}"><h2>{label}</h2><p>Poder de Venda: {score}/100</p></div>', unsafe_allow_html=True)
            st.progress(score / 100)

            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader("🛒 Ativos de Postagem")
                # Extraindo apenas a legenda para facilitar a cópia
                try:
                    legenda = re.search(r'LEGENDA_CURTA:(.*?)(?=HASHTAGS|AUDITORIA|$)', texto_ia, re.S).group(1).strip()
                    hashtags = re.search(r'HASHTAGS:(.*?)(?=AUDITORIA|$)', texto_ia, re.S).group(1).strip()
                except:
                    legenda = "Confira esse achadinho incrível na Shopee! 🎁"
                    hashtags = "#shopee #ofertas"

                st.markdown(f'<div class="asset-card"><b>Legenda (Max 150 caracteres):</b><br>{legenda}<br><br><b>Tags:</b> {hashtags}</div>', unsafe_allow_html=True)
                
                # Contador de caracteres visual
                st.caption(f"Contagem da legenda: {len(legenda)} caracteres.")
                st.text_area("Copiar Legenda:", f"{legenda} {hashtags}", height=100)
            
            with col2:
                match = re.search(r'CAPA:\s*(\d+)', texto_ia)
                segundo = int(match.group(1)) if match else 1
                cap = cv2.VideoCapture(file_path)
                cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                success, frame = cap.read()
                if success:
                    st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True, caption="Frame para Capa")
                cap.release()

            genai.delete_file(media_file.name)
        except Exception as e:
            st.error(f"Erro: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
