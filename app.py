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

st.title("🧡 Shopee Expert: Validação & Recriação")

# Configurar API
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)
MODELOS = ['gemini-3-flash', 'gemini-2.5-flash-lite']

# Inicializar estados de sessão para permitir recriação sem re-upload do vídeo
if 'texto_copiar' not in st.session_state:
    st.session_state.texto_copiar = ""
if 'relatorio_expert' not in st.session_state:
    st.session_state.relatorio_expert = ""
if 'score' not in st.session_state:
    st.session_state.score = "0"

def extrair_e_limpar(texto):
    try:
        titulo = re.search(r'TITULO_VENDA:(.*?)(?=TAGS|$)', texto, re.S).group(1).strip()
        tags = re.search(r'TAGS:(.*?)(?=---|$)', texto, re.S).group(1).strip()
        titulo = re.sub(r'^[\s\d.*-]*', '', titulo)
        tags = re.sub(r'^[\s\d.*-]*', '', tags)
        return f"{titulo} {tags}"
    except:
        return "Erro ao extrair ativos."

uploaded_file = st.file_uploader("📂 Suba o vídeo para análise...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    file_path = tfile.name
    
    # Botão para processar pela primeira vez ou recriar
    if st.button("🚀 Analisar Vídeo / Gerar Ativos") or st.session_state.texto_copiar == "":
        with st.spinner("🕵️ Consultando especialista e gerando texto..."):
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
                - **CONVERSÃO**: (Gatilhos de venda).
                - **DICA**: (Melhoria rápida).

                --- ATIVOS ---
                TITULO_VENDA: (Texto de venda impactante)
                TAGS: (4 hashtags estratégicas)
                --- FIM ---
                REGRA: O bloco (TITULO_VENDA + TAGS) deve ter no máximo 150 caracteres.
                CAPA_LIMPA: X
                """

                # Tentativa com modelos de cota livre
                response = None
                for m in MODELOS:
                    try:
                        model = genai.GenerativeModel(m)
                        response = model.generate_content([video_file, prompt])
                        break
                    except: continue

                if response:
                    res_text = response.text
                    st.session_state.score = re.search(r'\[SCORE\]:\s*(\d+)', res_text).group(1) if "[" in res_text else "50"
                    st.session_state.relatorio_expert = res_text.split('--- ATIVOS ---')[0].replace(f"[SCORE]: {st.session_state.score}", "").strip()
                    st.session_state.texto_copiar = extrair_e_limpar(res_text)
                    
                    # Salva o frame da capa
                    match_capa = re.search(r'CAPA_LIMPA:\s*(\d+)', res_text)
                    segundo = int(match_capa.group(1)) if match_capa else 1
                    cap = cv2.VideoCapture(file_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                    ret, frame = cap.read()
                    if ret:
                        st.session_state.capa_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    cap.release()

                genai.delete_file(video_file.name)
            except Exception as e:
                st.error(f"Erro: {e}")
            finally:
                if os.path.exists(file_path): os.remove(file_path)

    # --- ÁREA DE EXIBIÇÃO ---
    if st.session_state.texto_copiar:
        st.markdown(f'<div class="status-box"><h2>Potencial de Conversão: {st.session_state.score}/100</h2></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1.3, 0.7])
        
        with col1:
            st.subheader("👨‍🏫 Consultoria do Especialista")
            st.info(st.session_state.relatorio_expert)

            st.divider()
            st.subheader("📋 Título + 4 Tags (Máx 150 chars)")
            st.code(st.session_state.texto_copiar, language=None)
            
            # BOTÃO PARA RECRIAR APENAS O TEXTO
            if st.button("🔄 Recriar Título e Tags (Nova Opção)"):
                with st.spinner("🔄 Gerando nova variação de texto..."):
                    model = genai.GenerativeModel('gemini-2.5-flash-lite') # Usando Lite para texto puro
                    novo_prompt = f"Com base nesta análise: {st.session_state.relatorio_expert}, crie um NOVO TITULO_VENDA e 4 TAGS diferentes da anterior. Respeite o limite de 150 caracteres totais. Formato: TITULO_VENDA: ... TAGS: ..."
                    nova_resp = model.generate_content(novo_prompt)
                    st.session_state.texto_copiar = extrair_e_limpar(nova_resp.text)
                    st.rerun()

        with col2:
            if 'capa_frame' in st.session_state:
                st.subheader("🖼️ Capa")
                st.image(st.session_state.capa_frame, use_container_width=True)
