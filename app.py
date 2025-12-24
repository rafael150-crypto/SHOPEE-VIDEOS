import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time

# 1. Configuração de Interface
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
        font-weight: bold;
    }
    .stTextArea textarea {
        font-size: 18px !important;
        color: #ee4d2d !important;
        font-weight: bold;
        border: 2px solid #ee4d2d !important;
    }
    .expert-report {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ee4d2d;
        color: #1a1a1a;
    }
    .api-counter {
        background-color: #1e1e1e;
        color: #00ff00;
        padding: 5px 15px;
        border-radius: 20px;
        font-family: monospace;
        font-size: 12px;
        float: right;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Configuração da API
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)

# 3. Estados de Sessão (Memória)
if 'texto_copiar' not in st.session_state: st.session_state.texto_copiar = ""
if 'relatorio_expert' not in st.session_state: st.session_state.relatorio_expert = ""
if 'score' not in st.session_state: st.session_state.score = "0"
if 'capa_frame' not in st.session_state: st.session_state.capa_frame = None
if 'api_usage' not in st.session_state: st.session_state.api_usage = 0

def limpar_ativos_expert(texto):
    """Extrai apenas o conteúdo útil, removendo rótulos e vírgulas"""
    try:
        # Tenta capturar o título e as tags ignorando os rótulos da IA
        partes = re.split(r'TITULO_VENDA:|TAGS:', texto)
        if len(partes) >= 3:
            titulo = partes[1].split('\n')[0].strip()
            tags_brutas = partes[2].split('\n')[0].strip()
        else:
            # Fallback caso a regex falhe
            titulo = texto.split('\n')[0]
            tags_brutas = ""

        # Limpeza de caracteres de lista e rótulos residuais
        titulo = re.sub(r'(?i)TITULO_VENDA:|TITULO:|[#*0-9.-]', '', titulo).strip()
        
        # Formatação de Hashtags (sem vírgulas)
        tags_limpas = tags_brutas.replace(',', ' ').replace('.', ' ').replace('TAGS:', '')
        lista_tags = []
        for word in tags_limpas.split():
            word = word.strip()
            if word:
                if not word.startswith('#'): word = f"#{word}"
                lista_tags.append(word)
        
        resultado = f"{titulo} {' '.join(lista_tags[:4])}"
        return resultado[:150].strip()
    except:
        return "Erro ao formatar. Tente recriar o título."

# 4. Interface
st.markdown(f'<div class="api-counter">Uso da Sessão: {st.session_state.api_usage} chamadas | Modelo: Gemini-3-Flash</div>', unsafe_allow_html=True)
st.title("🧡 Shopee Expert: Auditoria de Vendas")

uploaded_file = st.file_uploader("📂 Suba o vídeo...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    file_path = tfile.name
    
    if st.button("🚀 Iniciar Auditoria do Especialista"):
        st.session_state.api_usage += 1
        with st.spinner("🕵️ Consultando Especialista..."):
            try:
                video_file = genai.upload_file(path=file_path)
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)
                
                prompt = """
                Atue como Especialista Shopee. Analise o vídeo e retorne:
                [SCORE]: 0-100
                # 🧠 RELATÓRIO DO ESPECIALISTA
                - (Análise técnica de gancho, segurança e conversão)
                --- ATIVOS ---
                TITULO_VENDA: (Texto de venda magnético)
                TAGS: (4 hashtags com # sem vírgulas)
                --- FIM ---
                CAPA: X (segundo sugerido)
                """

                model = genai.GenerativeModel('gemini-3-flash')
                response = model.generate_content([video_file, prompt])

                if response:
                    res_text = response.text
                    st.session_state.score = re.search(r'\[SCORE\]:\s*(\d+)', res_text).group(1) if "[" in res_text else "50"
                    st.session_state.relatorio_expert = res_text.split('# 🧠 RELATÓRIO DO ESPECIALISTA')[-1].split('--- ATIVOS ---')[0].strip()
                    st.session_state.texto_copiar = limpar_ativos_expert(res_text)
                    
                    # Processamento de Capa
                    match_capa = re.search(r'CAPA:\s*(\d+)', res_text)
                    segundo = int(match_capa.group(1)) if match_capa else 1
                    cap = cv2.VideoCapture(file_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                    ret, frame = cap.read()
                    if ret: st.session_state.capa_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    cap.release()

                genai.delete_file(video_file.name)
            except Exception as e:
                st.error(f"Erro na API: {e}")
            finally:
                if os.path.exists(file_path): os.remove(file_path)

    if st.session_state.texto_copiar:
        st.markdown(f'<div class="status-box">POTENCIAL DE CONVERSÃO: {st.session_state.score}/100</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1.3, 0.7])
        with col1:
            st.subheader("👨‍🏫 Consultoria do Especialista")
            st.markdown(f'<div class="expert-report">{st.session_state.relatorio_expert.replace("-", "<br>•")}</div>', unsafe_allow_html=True)

            st.divider()
            st.subheader("📋 Título + 4 Tags (Máx 150 chars)")
            st.text_area("Copiar:", st.session_state.texto_copiar, height=80, label_visibility="collapsed")
            st.caption(f"Contagem: {len(st.session_state.texto_copiar)}/150")
            
            if st.button("🔄 Recriar Título e Tags"):
                st.session_state.api_usage += 1
                model_lite = genai.GenerativeModel('gemini-2.5-flash-lite')
                resp_nova = model_lite.generate_content(f"Gere um NOVO TITULO e 4 TAGS (# sem vírgula) para este produto. Limite 150 chars totais. Use o formato: TITULO_VENDA: ... TAGS: ...")
                st.session_state.texto_copiar = limpar_ativos_expert(resp_nova.text)
                st.rerun()

        with col2:
            if st.session_state.capa_frame is not None:
                st.subheader("🖼️ Capa")
                st.image(st.session_state.capa_frame, use_container_width=True)
