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
    </style>
    """, unsafe_allow_html=True)

# 2. Configuração da API - USE NOMES ESTÁVEIS AQUI
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)
# Alterado para os nomes que o Google reconhece oficialmente agora
MODELOS = ['gemini-1.5-flash', 'gemini-1.5-pro']

# 3. Estados de Sessão
if 'texto_copiar' not in st.session_state: st.session_state.texto_copiar = ""
if 'relatorio_expert' not in st.session_state: st.session_state.relatorio_expert = ""
if 'score' not in st.session_state: st.session_state.score = "0"
if 'capa_frame' not in st.session_state: st.session_state.capa_frame = None

def limpar_ativos(texto):
    """Filtro de Elite: Título + 4 Tags sem vírgulas em 150 caracteres"""
    try:
        titulo = re.search(r'TITULO_VENDA:(.*?)(?=TAGS|$)', texto, re.S).group(1).strip()
        tags_brutas = re.search(r'TAGS:(.*?)(?=---|$)', texto, re.S).group(1).strip()
        titulo = re.sub(r'^[\s\d.*-]*', '', titulo)
        
        # Limpa as tags: remove vírgulas e pontos
        tags_limpas = tags_brutas.replace(',', ' ').replace('.', ' ')
        lista_tags = []
        for word in tags_limpas.split():
            word = word.strip()
            if word:
                if not word.startswith('#'): word = f"#{word}"
                lista_tags.append(word)
        
        resultado = f"{titulo} {' '.join(lista_tags[:4])}"
        return resultado[:150]
    except:
        return "Erro na formatação. Tente novamente."

# 4. Interface Principal
st.title("🧡 Shopee Expert: Auditoria de Vendas")

uploaded_file = st.file_uploader("📂 Suba o vídeo para análise do Especialista...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # Salvar arquivo temporário corretamente
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
        tfile.write(uploaded_file.read())
        file_path = tfile.name
    
    if st.button("🚀 Iniciar Auditoria do Especialista"):
        with st.spinner("🕵️ Consultando Especialista em Conversão Shopee..."):
            try:
                # Upload para a API
                video_file = genai.upload_file(path=file_path)
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)
                
                prompt = """
                Atue como o maior Especialista em Algoritmo e Vendas do Shopee Vídeos.
                Analise o vídeo de forma técnica e retorne:

                [SCORE]: (Nota de 0 a 100 de potencial de venda)

                # 🧠 RELATÓRIO DO ESPECIALISTA
                - **GANCHO INICIAL**: (Análise dos primeiros 2s).
                - **ESTÉTICA E ILUMINAÇÃO**: (O vídeo é profissional?).
                - **POLÍTICA E RISCO**: (Análise de shadowban).
                - **GATILHOS DE CONVERSÃO**: (Psicologia usada).
                - **VEREDITO FINAL**: (O que fazer para vender).

                --- ATIVOS ---
                TITULO_VENDA: (Título magnético curto)
                TAGS: (4 hashtags estratégicas sem vírgulas)
                --- FIM ---
                REGRA: Título + Tags não podem passar de 150 caracteres.
                CAPA: X (segundo sugerido)
                """

                response = None
                for m in MODELOS:
                    try:
                        model = genai.GenerativeModel(m)
                        response = model.generate_content([video_file, prompt])
                        break
                    except Exception as e:
                        continue

                if response:
                    res_text = response.text
                    # Extrair Score
                    score_match = re.search(r'\[SCORE\]:\s*(\d+)', res_text)
                    st.session_state.score = score_match.group(1) if score_match else "50"
                    
                    # Extrair Relatório
                    if '# 🧠 RELATÓRIO DO ESPECIALISTA' in res_text:
                        st.session_state.relatorio_expert = res_text.split('# 🧠 RELATÓRIO DO ESPECIALISTA')[-1].split('--- ATIVOS ---')[0].strip()
                    
                    # Extrair Ativos
                    st.session_state.texto_copiar = limpar_ativos(res_text)
                    
                    # Extrair Capa
                    match_capa = re.search(r'CAPA:\s*(\d+)', res_text)
                    segundo = int(match_capa.group(1)) if match_capa else 1
                    cap = cv2.VideoCapture(file_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                    ret, frame = cap.read()
                    if ret: 
                        st.session_state.capa_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    cap.release()

                genai.delete_file(video_file.name)
            except Exception as e:
                st.error(f"Erro no processamento: {e}")
            finally:
                if os.path.exists(file_path): 
                    os.remove(file_path)

    # 5. Dashboard de Resultados
    if st.session_state.texto_copiar:
        st.markdown(f'<div class="status-box">POTENCIAL DE CONVERSÃO: {st.session_state.score}/100</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1.3, 0.7])
        
        with col1:
            st.subheader("👨‍🏫 Consultoria do Especialista")
            st.markdown(f"""
                <div class="expert-report">
                    {st.session_state.relatorio_expert.replace('-', '<br>•').replace('\n', '<br>')}
                </div>
            """, unsafe_allow_html=True)

            st.divider()
            st.subheader("📋 Título + 4 Tags (Máx 150 chars)")
            st.text_area("Pronto para colar:", st.session_state.texto_copiar, height=100)
            st.caption(f"Contagem: {len(st.session_state.texto_copiar)}/150 caracteres.")
            
            if st.button("🔄 Recriar Título e Tags"):
                model_lite = genai.GenerativeModel('gemini-1.5-flash')
                resp_nova = model_lite.generate_content(f"Gere um NOVO TITULO e 4 TAGS (# sem vírgula) para: {st.session_state.relatorio_expert}. Máximo 150 chars.")
                st.session_state.texto_copiar = limpar_ativos(resp_nova.text)
                st.rerun()

        with col2:
            if st.session_state.capa_frame is not None:
                st.subheader("🖼️ Capa")
                st.image(st.session_state.capa_frame, use_container_width=True)
                st.info("💡 Dica: Capas com Unboxing convertem mais!")
