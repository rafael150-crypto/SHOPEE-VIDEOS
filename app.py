import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time

# Configuração da Página
st.set_page_config(page_title="BrendaBot Shopee Expert", page_icon="🧡", layout="wide")

# CSS Corrigido para Visibilidade Total
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
        background-color: #ee4d2d;
        color: white;
        margin-bottom: 20px;
    }
    .expert-card {
        background-color: #f9f9f9;
        padding: 20px;
        border-left: 5px solid #ee4d2d;
        border-radius: 8px;
        color: #1a1a1a !important; /* Força cor preta no texto */
        line-height: 1.6;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .expert-card h1, .expert-card h2, .expert-card h3, .expert-card p, .expert-card li {
        color: #1a1a1a !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧡 BrendaBot Shopee Expert Edition")

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
            Atue como o maior Especialista em Vendas no Shopee Vídeos.
            Retorne um relatório completo e depois os ativos:

            [SCORE]: Nota 0-100.

            # 📋 CONSULTORIA DO ESPECIALISTA
            - **VEREDITO DE SEGURANÇA**: (Analise risco de banimento/marca d'água).
            - **PODER DE CONVERSÃO**: (Psicologia de venda e gatilhos).
            - **QUALIDADE DO GANCHO**: (Análise dos segundos iniciais).
            - **SUGESTÃO DE MELHORIA**: (O que mudar para vender mais?).

            --- ATIVOS ---
            LEGENDA: (Texto de venda)
            TAGS: (3 hashtags)
            CTA: (Pergunta curta)
            --- FIM ---

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
                    st.subheader("👨‍🏫 Análise Técnica de Vendas")
                    # Extraindo apenas o relatório (antes dos ativos)
                    relatorio = res_text.split('--- ATIVOS ---')[0]
                    relatorio = relatorio.replace(f"[SCORE]: {score}", "").strip()
                    
                    # Exibição segura com cor forçada
                    st.markdown(f'<div class="expert-card">{relatorio}</div>', unsafe_allow_html=True)

                    st.divider()
                    st.subheader("🛒 Conteúdo Pronto (Sem espaços)")
                    
                    try:
                        leg = re.search(r'LEGENDA:(.*?)(?=TAGS|$)', res_text, re.S).group(1).strip()
                        tags = re.search(r'TAGS:(.*?)(?=CTA|$)', res_text, re.S).group(1).strip()
                        cta = re.search(r'CTA:(.*?)(?=---|$)', res_text, re.S).group(1).strip()
                        
                        leg = re.sub(r'^[\s\d.*-]*', '', leg)
                        tags = re.sub(r'^[\s\d.*-]*', '', tags)
                        cta = re.sub(r'^[\s\d.*-]*', '', cta)
                        
                        # Legenda e Tags na mesma linha, CTA abaixo
                        texto_final = f"{leg} {tags}\n{cta}"
                    except:
                        texto_final = "Falha ao extrair ativos."

                    st.markdown('<div class="copy-area">', unsafe_allow_html=True)
                    st.text_area("Cópia Direta:", texto_final, height=120, label_visibility="collapsed")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    primeira_linha = texto_final.split('\n')[0]
                    st.caption(f"Caracteres na linha principal: {len(primeira_linha)}/150")

                with col2:
                    match_capa = re.search(r'CAPA_LIMPA:\s*(\d+)', res_text)
                    segundo = int(match_capa.group(1)) if match_capa else 1
                    cap = cv2.VideoCapture(file_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                    ret, frame = cap.read()
                    if ret:
                        st.subheader("🖼️ Capa Sugerida")
                        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)
                    cap.release()

            genai.delete_file(video_file.name)
        except Exception as e:
            st.error(f"Erro: {e}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
