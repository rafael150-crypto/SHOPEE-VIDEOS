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
        border: 2px solid #ee4d2d;
        margin-bottom: 20px;
    }
    .expert-card {
        background-color: #ffffff;
        padding: 20px;
        border-left: 5px solid #ee4d2d;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧡 BrendaBot Shopee Expert Edition")
st.caption("Consultoria de Conversão e Auditoria de Algoritmo Shopee")

# Configurar API
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)
MODELOS = ['gemini-3-flash', 'gemini-2.5-flash-lite']

uploaded_file = st.file_uploader("📂 Suba o vídeo para análise de expert...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    file_path = tfile.name
    
    with st.spinner("🕵️ Consultando especialista e auditando métricas..."):
        try:
            video_file = genai.upload_file(path=file_path)
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            prompt = """
            Atue como o maior Especialista em Vendas no Shopee Vídeos. Analise o vídeo tecnicamente e retorne:

            [SCORE]: Nota 0-100 baseada em conversão real.

            # 📋 AUDITORIA TÉCNICA DO EXPERT
            - **RISCO DE POLÍTICA**: (Análise rigorosa de marcas d'água, conteúdo estático ou reupload que causa banimento).
            - **ANÁLISE DO GANCHO (HOOK)**: (Os primeiros 2 segundos mostram o benefício? Nota de retenção).
            - **QUALIDADE VISUAL**: (Iluminação, foco no produto e enquadramento para mobile).
            - **GATILHOS MENTAIS**: (Quais gatilhos estão presentes ou faltam? Ex: urgência, prova social, desejo).

            --- TEXTO PARA COPIAR ---
            LEGENDA: (Escreva o texto de venda compacto)
            TAGS: (3 hashtags estratégicas)
            CTA: (Uma pergunta curta de engajamento)
            --- FIM ---

            CAPA_LIMPA: X (Segundo exato com fundo neutro e produto em destaque)
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
                    # Extrai o relatório completo
                    relatorio = res_text.split('--- TEXTO PARA COPIAR ---')[0].replace(f"[SCORE]: {score}", "")
                    st.markdown(f'<div class="expert-card">{relatorio}</div>', unsafe_allow_html=True)

                    st.divider()
                    st.subheader("🛒 Conteúdo Otimizado (Cópia Sem Espaços)")
                    
                    try:
                        leg = re.search(r'LEGENDA:(.*?)(?=TAGS|$)', res_text, re.S).group(1).strip()
                        tags = re.search(r'TAGS:(.*?)(?=CTA|$)', res_text, re.S).group(1).strip()
                        cta = re.search(r'CTA:(.*?)(?=---|$)', res_text, re.S).group(1).strip()
                        
                        # Limpeza de resíduos
                        leg = re.sub(r'^[\s\d.*-]*', '', leg)
                        tags = re.sub(r'^[\s\d.*-]*', '', tags)
                        cta = re.sub(r'^[\s\d.*-]*', '', cta)
                        
                        # Formatação: Legenda e Tags grudadas, CTA na linha de baixo
                        texto_final = f"{leg} {tags}\n{cta}"
                    except:
                        texto_final = "Erro ao formatar os ativos."

                    st.markdown('<div class="copy-area">', unsafe_allow_html=True)
                    st.text_area("Pronto para colar:", texto_final, height=120, label_visibility="collapsed")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    total_chars = len(texto_final.split('\n')[0])
                    if total_chars > 150:
                        st.error(f"⚠️ Atenção: A primeira linha tem {total_chars} caracteres. A Shopee pode cortar.")
                    else:
                        st.success(f"✅ {total_chars}/150 caracteres (Tamanho ideal)")

                with col2:
                    match_capa = re.search(r'CAPA_LIMPA:\s*(\d+)', res_text)
                    segundo = int(match_capa.group(1)) if match_capa else 1
                    
                    cap = cv2.VideoCapture(file_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                    ret, frame = cap.read()
                    if ret:
                        st.subheader("🖼️ Capa Sugerida")
                        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)
                        _, buffer = cv2.imencode('.jpg', frame)
                        st.download_button("📥 Baixar Capa Expert", buffer.tobytes(), "capa_shopee.jpg", "image/jpeg")
                    cap.release()

            genai.delete_file(video_file.name)
        except Exception as e:
            st.error(f"Erro na análise: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
