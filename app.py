import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time

# Configuração da Página
st.set_page_config(page_title="BrendaBot Shopee Pro - Multi-Cota", page_icon="🧡", layout="wide")

# Interface Laranja Shopee
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .status-box { padding: 20px; border-radius: 15px; margin-bottom: 25px; text-align: center; border: 2px solid #ee4d2d; background-color: #fff5f2; color: #ee4d2d; }
    .asset-card { background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #ee4d2d; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🧡 BrendaBot Shopee - Multi-Cota")
st.caption("Sistema inteligente que alterna entre Gemini 3, 2.5 Lite e 2.5 Flash automaticamente.")

# Configurar API
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)

# Lista de modelos por ordem de prioridade baseada nas suas cotas livres
MODELOS_PRIORIDADE = [
    'models/gemini-3-flash',        # Prioridade 1: Cota zerada e mais moderno
    'models/gemini-2.5-flash-lite', # Prioridade 2: Cota zerada
    'models/gemini-2.5-flash'       # Prioridade 3: Sua cota original (quase cheia)
]

def gerar_conteudo_com_fallback(arquivo_ia, prompt):
    """Tenta gerar conteúdo alternando entre os modelos caso a cota estoure."""
    for nome_modelo in MODELOS_PRIORIDADE:
        try:
            model = genai.GenerativeModel(nome_modelo)
            response = model.generate_content([arquivo_ia, prompt])
            return response, nome_modelo
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                st.warning(f"⚠️ Cota esgotada no {nome_modelo}. Tentando próximo modelo...")
                continue
            else:
                raise e
    return None, None

uploaded_file = st.file_uploader("📂 Suba o vídeo do seu Produto...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
        tfile.write(uploaded_file.read())
        file_path = tfile.name
    
    with st.spinner("📦 Analisando vídeo... (Testando modelos disponíveis)"):
        try:
            # Upload do vídeo
            media_file = genai.upload_file(path=file_path)
            while media_file.name and genai.get_file(media_file.name).state.name == "PROCESSING":
                time.sleep(2)
            
            prompt = """
            Atue como Especialista Shopee. Analise o vídeo e retorne:
            1. [PONTUACAO_VENDA]: Nota 0-100.
            2. LEGENDA_CURTA: Máximo 130 caracteres (foco em benefício/cupom).
            3. HASHTAGS: 3 tags (ex: #shopee #achados).
            4. AUDITORIA: Risco de banimento (marca d'água ou estático).
            5. CAPA: segundo sugerido.
            """
            
            response, modelo_usado = gerar_conteudo_com_fallback(media_file, prompt)
            
            if response:
                texto_ia = response.text
                st.success(f"✅ Analisado com sucesso usando o modelo: **{modelo_usado}**")
                
                # --- LAYOUT DE EXIBIÇÃO ---
                score_match = re.search(r'\[PONTUACAO_VENDA\]:\s*(\d+)', texto_ia)
                score = int(score_match.group(1)) if score_match else 50
                
                st.markdown(f'<div class="status-box"><h2>Poder de Venda: {score}/100</h2></div>', unsafe_allow_html=True)
                st.progress(score / 100)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader("🎯 Ativos")
                    legenda = re.search(r'LEGENDA_CURTA:(.*?)(?=HASHTAGS|$)', texto_ia, re.S)
                    tags = re.search(r'HASHTAGS:(.*?)(?=AUDITORIA|$)', texto_ia, re.S)
                    
                    texto_legenda = legenda.group(1).strip() if legenda else "Achadinho Shopee!"
                    texto_tags = tags.group(1).strip() if tags else "#shopee"
                    
                    st.markdown(f'<div class="asset-card">{texto_legenda}<br><b>{texto_tags}</b></div>', unsafe_allow_html=True)
                    st.text_area("Copiar Legenda (Max 150 chars):", f"{texto_legenda} {texto_tags}")
                
                with col2:
                    match_capa = re.search(r'CAPA:\s*(\d+)', texto_ia)
                    segundo = int(match_capa.group(1)) if match_capa else 1
                    cap = cv2.VideoCapture(file_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                    success, frame = cap.read()
                    if success:
                        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True, caption="Thumbnail Sugerida")
                    cap.release()
            else:
                st.error("❌ Todas as suas cotas de modelos multimodais (Gemini) foram excedidas.")

            genai.delete_file(media_file.name)

        except Exception as e:
            st.error(f"Erro crítico: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
