import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time

# Configuração da Página
st.set_page_config(page_title="BrendaBot Shopee Expert", page_icon="🧡", layout="wide")

st.markdown("""
    <style>
    .status-box {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        background-color: #ee4d2d;
        color: white;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧡 Shopee Expert: Foco em Conversão")

# Configurar API
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)
MODELOS = ['gemini-3-flash', 'gemini-2.5-flash-lite']

uploaded_file = st.file_uploader("📂 Suba o vídeo para análise...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    file_path = tfile.name
    
    with st.spinner("🕵️ Consultando especialista..."):
        try:
            video_file = genai.upload_file(path=file_path)
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            prompt = """
            Atue como Especialista em Shopee Vídeos. Analise o vídeo e retorne:

            [SCORE]: Nota 0-100.

            # CONSULTORIA TÉCNICA
            - **SEGURANÇA**: (Analise risco de banimento).
            - **CONVERSÃO**: (Gatilhos de venda usados).
            - **DICA**: (Melhoria rápida).

            --- ATIVOS ---
            TITULO_VENDA: (Texto de venda impactante)
            TAGS: (4 hashtags estratégicas)
            --- FIM ---
            
            REGRA: O bloco (TITULO_VENDA + TAGS) deve ter no máximo 150 caracteres totais.

            CAPA_LIMPA: X
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
                score = re.search(r'\[SCORE\]:\s*(\d+)', res_text)
                score = score.group(1) if score else "50"
                
                st.markdown(f'<div class="status-box"><h2>Potencial de Conversão: {score}/100</h2></div>', unsafe_allow_html=True)

                col1, col2 = st.columns([1.3, 0.7])
                
                with col1:
                    st.subheader("👨‍🏫 Consultoria do Especialista")
                    relatorio = res_text.split('--- ATIVOS ---')[0].replace(f"[SCORE]: {score}", "").strip()
                    st.info(relatorio)

                    st.divider()
                    st.subheader("📋 Clique para Copiar (Título + 4 Tags)")
                    
                    try:
                        titulo = re.search(r'TITULO_VENDA:(.*?)(?=TAGS|$)', res_text, re.S).group(1).strip()
                        tags = re.search(r'TAGS:(.*?)(?=---|$)', res_text, re.S).group(1).strip()
                        
                        # Limpeza profunda de prefixos
                        titulo = re.sub(r'^[\s\d.*-]*', '', titulo)
                        tags = re.sub(r'^[\s\d.*-]*', '', tags)
                        
                        # Bloco final: Título e Tags na mesma linha sem nada extra
                        texto_final = f"{titulo} {tags}"
                    except:
                        texto_final = "Erro ao extrair texto."

                    # Botão de copiar nativo (st.code)
                    st.code(texto_final, language=None)
                    
                    st.caption(f"Total: {len(texto_final)}/150 caracteres")
                    if len(texto_final) > 150:
                        st.error("⚠️ O texto excedeu 150 caracteres.")

                with col2:
                    match_capa = re.search(r'CAPA_LIMPA:\s*(\d+)', res_text)
                    segundo = int(match_capa.group(1)) if match_capa else 1
                    cap = cv2.VideoCapture(file_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                    ret, frame = cap.read()
                    if ret:
                        st.subheader("🖼️ Capa")
                        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)
                        _, buffer = cv2.imencode('.jpg', frame)
                        st.download_button("📥 Baixar Capa", buffer.tobytes(), "capa.jpg", "image/jpeg")
                    cap.release()

            genai.delete_file(video_file.name)
        except Exception as e:
            st.error(f"Erro: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
