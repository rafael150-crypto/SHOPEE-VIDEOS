import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time

# Configuração da Página
st.set_page_config(page_title="BrendaBot Shopee Expert", page_icon="🧡", layout="wide")

# CSS para Estilização
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

st.title("🧡 Shopee Expert: Validação & Ativos")

# Configurar API
API_KEY = "AIzaSyDmqVD3ZnaPKumWVrlJUpvWgbZNxNT9unY"
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
            Atue como Especialista em Shopee Vídeos. 
            Analise o vídeo e retorne:

            [SCORE]: Nota 0-100.

            # CONSULTORIA TÉCNICA
            - **SEGURANÇA**: (Analise risco de banimento).
            - **CONVERSÃO**: (Gatilhos de venda).
            - **DICA**: (Melhoria rápida).

            --- ATIVOS ---
            LEGENDA: (Texto de venda)
            TAGS: (3 hashtags)
            CTA: (Pergunta curta)
            --- FIM ---
            
            IMPORTANTE: A soma de LEGENDA + TAGS deve ter NO MÁXIMO 145 caracteres.

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
                    st.subheader("👨‍🏫 Consultoria Técnica")
                    relatorio = res_text.split('--- ATIVOS ---')[0].replace(f"[SCORE]: {score}", "").strip()
                    st.info(relatorio)

                    st.divider()
                    st.subheader("📋 Clique para Copiar")
                    
                    try:
                        leg = re.search(r'LEGENDA:(.*?)(?=TAGS|$)', res_text, re.S).group(1).strip()
                        tags = re.search(r'TAGS:(.*?)(?=CTA|$)', res_text, re.S).group(1).strip()
                        cta = re.search(r'CTA:(.*?)(?=---|$)', res_text, re.S).group(1).strip()
                        
                        leg = re.sub(r'^[\s\d.*-]*', '', leg)
                        tags = re.sub(r'^[\s\d.*-]*', '', tags)
                        cta = re.sub(r'^[\s\d.*-]*', '', cta)
                        
                        # Bloco final otimizado para os 150 caracteres
                        texto_final = f"{leg} {tags}\n{cta}"
                    except:
                        texto_final = "Erro na geração do texto."

                    # O componente st.code já vem com um botão de copiar por padrão no canto superior direito
                    st.code(texto_final, language=None)
                    
                    # Verificador de caracteres para sua segurança
                    primeira_linha = texto_final.split('\n')[0]
                    st.caption(f"Tamanho da legenda + tags: {len(primeira_linha)}/150")

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
