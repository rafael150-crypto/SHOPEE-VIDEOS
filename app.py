import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time

# Configuração da Página
st.set_page_config(page_title="BrendaBot Shopee Pro", page_icon="🧡", layout="wide")

st.markdown("""
    <style>
    .copy-area {
        background-color: #fffaf9;
        border: 2px dashed #ee4d2d;
        padding: 15px;
        border-radius: 10px;
        margin-top: 10px;
    }
    .status-box {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        background-color: #fff5f2;
        color: #ee4d2d;
        border: 1px solid #ee4d2d;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧡 BrendaBot Shopee - Cópia Direta")

# Configurar API (Usando fallback de modelos para garantir cota)
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)
MODELOS = ['gemini-3-flash', 'gemini-2.5-flash-lite', 'gemini-1.5-flash']

uploaded_file = st.file_uploader("📂 Suba o vídeo do produto...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    file_path = tfile.name
    
    with st.spinner("🕵️ Analisando e limpando ativos..."):
        try:
            video_file = genai.upload_file(path=file_path)
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            prompt = """
            Atue como especialista em Shopee Vídeos. Analise o vídeo e retorne:

            [SCORE]: Nota 0-100.
            [ANALISE]: Resumo da viabilidade e riscos.

            --- TEXTO PARA COPIAR ---
            LEGENDA: (Apenas o texto da legenda, sem o nome 'Legenda', máximo 130 caracteres)
            TAGS: (Apenas as hashtags, sem o nome 'Tags')
            CTA: (Apenas a pergunta de engajamento, sem o nome 'CTA')
            --- FIM ---

            CAPA_LIMPA: X (segundo sugerido com o fundo mais limpo possível)
            """

            response = None
            for m in MODELOS:
                try:
                    model = genai.GenerativeModel(m)
                    response = model.generate_content([video_file, prompt])
                    break
                except: continue

            if response:
                res_text = response.text
                
                # Extração de dados
                score = re.search(r'\[SCORE\]:\s*(\d+)', res_text)
                score = score.group(1) if score else "50"
                
                st.markdown(f'<div class="status-box"><h2>Potencial de Venda: {score}/100</h2></div>', unsafe_allow_html=True)

                col1, col2 = st.columns([1.2, 0.8])
                
                with col1:
                    st.subheader("📋 Auditoria do Vídeo")
                    analise = re.search(r'\[ANALISE\]:(.*?)(?=---)', res_text, re.S)
                    if analise: st.info(analise.group(1).strip())

                    st.subheader("🛒 Conteúdo Pronto (Copiar e Colar)")
                    
                    # Captura os blocos e limpa qualquer resíduo de numeração ou título
                    try:
                        leg = re.search(r'LEGENDA:(.*?)(?=TAGS|$)', res_text, re.S).group(1).strip()
                        tags = re.search(r'TAGS:(.*?)(?=CTA|$)', res_text, re.S).group(1).strip()
                        cta = re.search(r'CTA:(.*?)(?=---|$)', res_text, re.S).group(1).strip()
                        
                        # Remove prefixos como "1. ", "- ", "* "
                        leg = re.sub(r'^[\s\d.*-]*', '', leg)
                        tags = re.sub(r'^[\s\d.*-]*', '', tags)
                        cta = re.sub(r'^[\s\d.*-]*', '', cta)
                        
                        texto_final = f"{leg}\n\n{tags}\n\n{cta}"
                    except:
                        texto_final = "Erro ao formatar. Tente novamente."

                    st.markdown('<div class="copy-area">', unsafe_allow_html=True)
                    st.text_area("Texto Limpo:", texto_final, height=200, label_visibility="collapsed")
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.caption(f"Caracteres: {len(leg) + len(tags)} (Limite Shopee: 150)")

                with col2:
                    match_capa = re.search(r'CAPA_LIMPA:\s*(\d+)', res_text)
                    segundo = int(match_capa.group(1)) if match_capa else 1
                    
                    cap = cv2.VideoCapture(file_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                    ret, frame = cap.read()
                    if ret:
                        st.subheader("🖼️ Frame Sugerido (Capa)")
                        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)
                        _, buffer = cv2.imencode('.jpg', frame)
                        st.download_button("📥 Baixar Capa", buffer.tobytes(), "capa.jpg", "image/jpeg")
                    cap.release()

            genai.delete_file(video_file.name)
        except Exception as e:
            st.error(f"Erro: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
