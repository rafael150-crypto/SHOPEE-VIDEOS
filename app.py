import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time

# Configuração da Página
st.set_page_config(page_title="BrendaBot Shopee Expert", page_icon="🧡", layout="wide")

# CSS para Área de Cópia e Status
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
    </style>
    """, unsafe_allow_html=True)

st.title("🧡 BrendaBot Shopee Expert Edition")

# Configurar API
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)

# Ordem de prioridade dos modelos para evitar erros de cota
MODELOS = ['gemini-3-flash', 'gemini-2.5-flash-lite', 'gemini-1.5-flash']

uploaded_file = st.file_uploader("📂 Suba o vídeo para análise...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    file_path = tfile.name
    
    with st.spinner("🕵️ Consultando especialista..."):
        try:
            # Upload para a API do Google
            video_file = genai.upload_file(path=file_path)
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            prompt = """
            Atue como o maior Especialista em Vendas no Shopee Vídeos.
            Analise o vídeo tecnicamente e retorne:

            [SCORE]: Nota 0-100.

            # CONSULTORIA TÉCNICA
            - **SEGURANÇA**: (Analise risco de banimento/marca d'água).
            - **CONVERSÃO**: (Psicologia de venda e gatilhos).
            - **GANCHO**: (Análise dos segundos iniciais).
            - **DICA**: (O que mudar para vender mais?).

            --- ATIVOS ---
            LEGENDA: (Texto de venda compacto)
            TAGS: (3 hashtags estratégicas)
            CTA: (Pergunta curta de engajamento)
            --- FIM ---

            CAPA_LIMPA: X
            """

            response = None
            modelo_usado = ""
            for m in MODELOS:
                try:
                    model = genai.GenerativeModel(m)
                    response = model.generate_content([video_file, prompt])
                    modelo_usado = m
                    break
                except:
                    continue

            if response:
                res_text = response.text
                
                # Extrair Score
                score_match = re.search(r'\[SCORE\]:\s*(\d+)', res_text)
                score = score_match.group(1) if score_match else "50"
                
                st.markdown(f'<div class="status-box"><h2>Potencial de Conversão: {score}/100</h2></div>', unsafe_allow_html=True)

                col1, col2 = st.columns([1.3, 0.7])
                
                with col1:
                    st.subheader("👨‍🏫 Análise do Especialista")
                    # Extrair o texto da consultoria
                    try:
                        relatorio = res_text.split('--- ATIVOS ---')[0]
                        relatorio = relatorio.replace(f"[SCORE]: {score}", "").strip()
                        # Usando st.info para garantir que o texto seja legível em qualquer tema
                        st.info(relatorio)
                    except:
                        st.write(res_text)

                    st.divider()
                    st.subheader("🛒 Cópia Direta (Sem Espaços)")
                    
                    try:
                        leg = re.search(r'LEGENDA:(.*?)(?=TAGS|$)', res_text, re.S).group(1).strip()
                        tags = re.search(r'TAGS:(.*?)(?=CTA|$)', res_text, re.S).group(1).strip()
                        cta = re.search(r'CTA:(.*?)(?=---|$)', res_text, re.S).group(1).strip()
                        
                        # Limpeza de caracteres de lista
                        leg = re.sub(r'^[\s\d.*-]*', '', leg)
                        tags = re.sub(r'^[\s\d.*-]*', '', tags)
                        cta = re.sub(r'^[\s\d.*-]*', '', cta)
                        
                        # Formatação pedida: Legenda e Tags juntas, CTA abaixo
                        texto_final = f"{leg} {tags}\n{cta}"
                    except:
                        texto_final = "Erro ao processar texto. Tente novamente."

                    st.markdown('<div class="copy-area">', unsafe_allow_html=True)
                    st.text_area("Pronto para colar na Shopee:", texto_final, height=150, label_visibility="collapsed")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    primeira_linha = texto_final.split('\n')[0]
                    st.caption(f"Caracteres na linha principal: {len(primeira_linha)}/150")

                with col2:
                    # Lógica da Capa
                    match_capa = re.search(r'CAPA_LIMPA:\s*(\d+)', res_text)
                    segundo = int(match_capa.group(1)) if match_capa else 1
                    
                    cap = cv2.VideoCapture(file_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                    ret, frame = cap.read()
                    if ret:
                        st.subheader("🖼️ Capa Sugerida")
                        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)
                        _, buffer = cv2.imencode('.jpg', frame)
                        st.download_button("📥 Baixar Capa", buffer.tobytes(), "capa_shopee.jpg", "image/jpeg")
                    cap.release()

            # Apagar arquivo da API do Google
            genai.delete_file(video_file.name)

        except Exception as e:
            st.error(f"Erro detectado: {e}")
        finally:
            # Garantir que o arquivo temporário local seja apagado
            if os.path.exists(file_path):
                os.remove(file_path)

# Seria útil eu adicionar um botão para gerar uma segunda opção de legenda caso a primeira fique muito longa?
