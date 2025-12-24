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
    .stCodeBlock { border: 2px solid #ee4d2d !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧡 Shopee Expert: Títulos & SEO")

# Configurar API
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)
MODELOS = ['gemini-3-flash', 'gemini-2.5-flash-lite']

# Inicializar estados de sessão
if 'texto_copiar' not in st.session_state: st.session_state.texto_copiar = ""
if 'relatorio_expert' not in st.session_state: st.session_state.relatorio_expert = ""
if 'score' not in st.session_state: st.session_state.score = "0"

def formatar_ativos_expert(texto):
    """Extrai e garante que as hashtags usem apenas # e espaços (sem vírgulas)"""
    try:
        titulo = re.search(r'TITULO_VENDA:(.*?)(?=TAGS|$)', texto, re.S).group(1).strip()
        tags = re.search(r'TAGS:(.*?)(?=---|$)', texto, re.S).group(1).strip()
        
        # Limpeza pesada
        titulo = re.sub(r'^[\s\d.*-]*', '', titulo)
        
        # Especialista em Tags: Remove vírgulas, pontos e garante o #
        tags = tags.replace(',', ' ').replace('.', ' ') # Troca vírgula por espaço
        tags_limpas = []
        for word in tags.split():
            word = word.strip()
            if word:
                if not word.startswith('#'):
                    tags_limpas.append(f"#{word}")
                else:
                    tags_limpas.append(word)
        
        resultado = f"{titulo} {' '.join(tags_limpas)}"
        return resultado[:150] # Trava rígida de 150 caracteres
    except:
        return "Erro ao processar ativos. Tente novamente."

uploaded_file = st.file_uploader("📂 Suba o vídeo para análise...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    file_path = tfile.name
    
    if st.button("🚀 Analisar Vídeo & Criar Título de Elite") or st.session_state.texto_copiar == "":
        with st.spinner("🕵️ Consultando Copywriter Expert..."):
            try:
                video_file = genai.upload_file(path=file_path)
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)
                
                prompt = """
                Atue como um Especialista em Copywriting para E-commerce e Estrategista de SEO para Shopee Vídeos.
                Sua missão é criar o título mais clicável possível e 4 hashtags de alto volume.

                [SCORE]: Nota 0-100.
                # CONSULTORIA TÉCNICA
                - **ANÁLISE DE VENDAS**: (Por que esse título vai converter?).
                - **GATILHOS**: (Explique o uso de urgência ou curiosidade).

                --- ATIVOS ---
                TITULO_VENDA: (Crie um título magnético focado no produto)
                TAGS: (4 hashtags começando com #, separadas APENAS por espaço, SEM VÍRGULAS)
                --- FIM ---
                REGRA DE OURO: Título + Tags não podem passar de 150 caracteres.
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
                    st.session_state.score = re.search(r'\[SCORE\]:\s*(\d+)', res_text).group(1) if "[" in res_text else "50"
                    st.session_state.relatorio_expert = res_text.split('--- ATIVOS ---')[0].replace(f"[SCORE]: {st.session_state.score}", "").strip()
                    st.session_state.texto_copiar = formatar_ativos_expert(res_text)
                    
                    match_capa = re.search(r'CAPA_LIMPA:\s*(\d+)', res_text)
                    segundo = int(match_capa.group(1)) if match_capa else 1
                    cap = cv2.VideoCapture(file_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                    ret, frame = cap.read()
                    if ret: st.session_state.capa_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    cap.release()

                genai.delete_file(video_file.name)
            except Exception as e:
                st.error(f"Erro: {e}")
            finally:
                if os.path.exists(file_path): os.remove(file_path)

    if st.session_state.texto_copiar:
        st.markdown(f'<div class="status-box"><h2>Potencial de Conversão: {st.session_state.score}/100</h2></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1.3, 0.7])
        
        with col1:
            st.subheader("👨‍🏫 Consultoria do Especialista")
            st.info(st.session_state.relatorio_expert)

            st.divider()
            st.subheader("📋 Título + 4 Tags (Clique no ícone para copiar)")
            st.code(st.session_state.texto_copiar, language=None)
            
            if st.button("🔄 Recriar Título e Tags (Nova Sugestão de Elite)"):
                with st.spinner("🔄 Especialista gerando nova variação..."):
                    model = genai.GenerativeModel('gemini-2.5-flash-lite')
                    novo_prompt = f"Baseado na análise: {st.session_state.relatorio_expert}, gere um NOVO TITULO_VENDA magnético e 4 TAGS (usando # e espaços). Sem vírgulas. Máximo 150 caracteres."
                    nova_resp = model.generate_content(novo_prompt)
                    st.session_state.texto_copiar = formatar_ativos_expert(nova_resp.text)
                    st.rerun()

        with col2:
            if 'capa_frame' in st.session_state:
                st.subheader("🖼️ Capa")
                st.image(st.session_state.capa_frame, use_container_width=True)
                st.caption(f"Caracteres: {len(st.session_state.texto_copiar)}/150")
