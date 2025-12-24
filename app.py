import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time

# Configuração da Página - Visual Premium Shopee
st.set_page_config(page_title="BrendaBot Shopee Pro", page_icon="🧡", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .status-box {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 25px;
        text-align: center;
        border: 2px solid #ee4d2d;
        background-color: #fff5f2;
        color: #ee4d2d;
    }
    .asset-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ee4d2d;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    .copy-area {
        background-color: #fffaf9;
        border: 1px dashed #ee4d2d;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧡 BrendaBot Shopee Seller - Ultra Edition")
st.caption("Validador de Políticas, Conversão e Gerador de Ativos Limpos")

# Configurar API
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)

# Lista de prioridade de modelos para evitar "Quota Exceeded"
MODELOS_PRIORIDADE = ['gemini-3-flash', 'gemini-2.5-flash-lite', 'gemini-1.5-flash']

uploaded_file = st.file_uploader("📂 Arraste o vídeo do produto aqui...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    file_path = tfile.name
    
    with st.spinner("🕵️ BrendaBot está auditando seu vídeo com inteligência multi-modelo..."):
        try:
            # Upload do arquivo
            video_file = genai.upload_file(path=file_path)
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            prompt = """
            Atue como Especialista em Shopee Vídeos e Conversão. 
            Analise o vídeo e retorne o relatório RIGOROSAMENTE neste formato:

            [PONTUACAO_VENDA]: Nota 0-100.

            ### 🚨 AUDITORIA DE POLÍTICAS SHOPEE
            - **RISCO DE BANIMENTO**: (Analise marcas d'água, vídeos estáticos ou baixa qualidade).
            - **VEREDITO**: (Aprovado ou Reprovado para o algoritmo).

            ### 🎯 ANÁLISE DE CONVERSÃO
            - **CHANCE DE VENDA**: (Justifique a nota de 0 a 100).
            - **QUALIDADE DO GANCHO**: (O produto aparece nos primeiros 2 segundos?).

            ### ✍️ ATIVOS PARA POSTAGEM (LIMPOS)
            - **LEGENDA_LIMPA**: (Crie uma legenda de no máximo 130 caracteres, sem números, sem títulos, apenas o texto de venda).
            - **TAGS_LIMPAS**: (3 hashtags apenas, sem números).
            - **CTA**: (Chamada para ação).

            CAPA: X (segundo sugerido onde o produto está em destaque).
            """

            # Tentar gerar conteúdo com sistema de Fallback
            response = None
            modelo_usado = ""
            for m in MODELOS_PRIORIDADE:
                try:
                    model = genai.GenerativeModel(m)
                    response = model.generate_content([video_file, prompt])
                    modelo_usado = m
                    break
                except:
                    continue

            if response:
                texto_ia = response.text
                
                # Extrair Score
                score = re.search(r'\[PONTUACAO_VENDA\]:\s*(\d+)', texto_ia)
                score = int(score.group(1)) if score else 50
                
                # --- TOPO: INDICÔMETRO ---
                st.markdown(f'<div class="status-box"><h2>Potencial de Conversão: {score}/100</h2><p>Modelo utilizado: {modelo_usado}</p></div>', unsafe_allow_html=True)
                st.progress(score / 100)

                col1, col2 = st.columns([1.2, 0.8])
                
                with col1:
                    st.subheader("📋 Relatório de Auditoria")
                    # Mostrar o relatório completo exceto a parte da capa
                    relatorio_visivel = re.sub(r'CAPA:\s*\d+', '', texto_ia)
                    st.markdown(relatorio_visivel)

                    # --- ÁREA DE CÓPIA LIMPA ---
                    st.divider()
                    st.subheader("🛒 Cópia Limpa para Shopee")
                    
                    # Extrair apenas o texto das labels LIMPAS
                    try:
                        leg_limpa = re.search(r'LEGENDA_LIMPA:(.*?)(?=TAGS_LIMPAS|CTA|$)', texto_ia, re.S).group(1).strip()
                        tags_limpas = re.search(r'TAGS_LIMPAS:(.*?)(?=CTA|$)', texto_ia, re.S).group(1).strip()
                        # Limpeza extra de caracteres indesejados (-, *, números no início)
                        leg_limpa = re.sub(r'^[-*0-9.\s]+', '', leg_limpa)
                        tags_limpas = re.sub(r'^[-*0-9.\s]+', '', tags_limpas)
                        
                        texto_final = f"{leg_limpa} {tags_limpas}"
                    except:
                        texto_final = "Confira esse achadinho imperdível com o melhor preço! 🧡 #shopee #achados"

                    st.markdown('<div class="copy-area">', unsafe_allow_html=True)
                    st.text_area("Legenda sem formatação (Pronta para colar):", texto_final, height=100)
                    st.caption(f"Total: {len(texto_final)}/150 caracteres")
                    st.markdown('</div>', unsafe_allow_html=True)

                with col2:
                    # Mostrar a CAPA
                    match_capa = re.search(r'CAPA:\s*(\d+)', texto_ia)
                    segundo = int(match_capa.group(1)) if match_capa else 1
                    
                    cap = cv2.VideoCapture(file_path)
                    cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                    success, frame = cap.read()
                    if success:
                        st.subheader("🖼️ Frame Sugerido")
                        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)
                        ret, buffer = cv2.imencode('.jpg', frame)
                        st.download_button("📥 Baixar Capa", buffer.tobytes(), "capa_shopee.jpg", "image/jpeg")
                    cap.release()
                    
                    st.info("💡 **Dica de Ouro:** A Shopee prefere capas onde o produto está centralizado e com fundo limpo.")

            else:
                st.error("ERRO: Não foi possível obter resposta dos modelos. Verifique sua conexão ou API Key.")

            genai.delete_file(video_file.name)

        except Exception as e:
            st.error(f"Erro no processamento: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
