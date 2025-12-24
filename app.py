import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time

# Configuração da Página - Visual Shopee (Laranja)
st.set_page_config(page_title="BrendaBot Shopee Seller", page_icon="🧡", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .status-box {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 25px;
        text-align: center;
        border: 2px solid #ee4d2d;
    }
    .safe-bg { background-color: #fff5f2; color: #ee4d2d; border: 2px solid #ee4d2d; }
    .warning-bg { background-color: #fff9e6; color: #d69e2e; border: 2px solid #d69e2e; }
    .danger-bg { background-color: #fff0f0; color: #e53e3e; border: 2px solid #e53e3e; }
    .asset-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ee4d2d;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧡 BrendaBot Shopee Seller")
st.caption("Validador de Conversão e Diretrizes para Shopee Vídeos")

# Configurar API
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

uploaded_file = st.file_uploader("📂 Suba o vídeo do seu Produto...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
        tfile.write(uploaded_file.read())
        file_path = tfile.name
    
    with st.spinner("📦 Analisando potencial de vendas e regras da Shopee..."):
        try:
            video_file = genai.upload_file(path=file_path)
            while video_file.name and genai.get_file(video_file.name).state.name == "PROCESSING":
                time.sleep(2)
            
            prompt = """
            Atue como Especialista em E-commerce e Algoritmo Shopee Vídeos. 
            Analise o vídeo do produto e retorne o relatório neste formato:

            [PONTUACAO_VENDA]: X (Nota de 0 a 100 baseada no potencial de convencer alguém a comprar)
            
            # 🚨 ANÁLISE DE DIRETRIZES SHOPEE
            - **RISCO DE BANIMENTO**: (A Shopee bane vídeos com apenas fotos estáticas, tarjas pretas gigantes ou marcas d'água de outras lojas. Analise isso).
            - **QUALIDADE TÉCNICA**: (A iluminação e o som permitem ver os detalhes do produto? Essencial para conversão).
            - **CHANCE DE FLOPAR**: (Porcentagem e motivo: Ex: gancho fraco ou vídeo longo demais).

            # 💰 ATIVOS DE CONVERSÃO (PARA POSTAR)
            - **LEGENDA CHAMATIVA**: (Curta, direta e com foco no benefício + Cupons/Frete Grátis).
            - **HASHTAGS SHOPEE**: (As 3 melhores para o nicho, ex: #shopeebr #achadinhos).
            - **MELHOR CUPOM PARA CITAR**: (Sugira se deve focar em Frete Grátis ou Desconto).

            # 🎯 ESTRATÉGIA DE VÍDEO
            - **O GANCHO**: (Analise os primeiros 2 segundos. O produto aparece rápido?).
            - **PROVA SOCIAL**: (O vídeo mostra o produto sendo usado/testado? Se não, sugira adicionar).

            CAPA: X (segundo sugerido onde o produto aparece mais bonito)
            """
            
            response = model.generate_content([video_file, prompt])
            texto_ia = response.text
            
            try:
                score = int(re.search(r'\[PONTUACAO_VENDA\]:\s*(\d+)', texto_ia).group(1))
            except:
                score = 50

            # --- INDICÔMETRO DE CONVERSÃO ---
            if score >= 75:
                label, bg_class = "🚀 ALTO POTENCIAL DE VENDA", "safe-bg"
            elif score >= 45:
                label, bg_class = "⚖️ MÉDIO POTENCIAL (PRECISA AJUSTES)", "warning-bg"
            else:
                label, bg_class = "⚠️ BAIXA CONVERSÃO / RISCO", "danger-bg"

            st.markdown(f'<div class="status-box {bg_class}"><h2>{label}</h2><p>Poder de Convencimento: {score}/100</p></div>', unsafe_allow_html=True)
            st.progress(score / 100)

            col1, col2 = st.columns([1.2, 0.8])
            
            with col1:
                st.subheader("📋 Auditoria de Vendedor")
                texto_limpo = re.sub(r'\[PONTUACAO_VENDA\]:.*?\d+', '', texto_ia)
                texto_limpo = re.sub(r'CAPA:\s*\d+', '', texto_limpo)
                
                partes = texto_limpo.split('# 💰 ATIVOS DE CONVERSÃO')
                st.markdown(partes[0])
                
                if len(partes) > 1:
                    st.markdown('<div class="asset-card">', unsafe_allow_html=True)
                    st.subheader("🛒 Ativos para Postagem")
                    st.markdown(partes[1])
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.divider()
                    st.subheader("📋 Copiar Legenda Shopee")
                    st.text_area("Pronto para colar no App:", partes[1].split('###')[0].strip(), height=150)
            
            with col2:
                match = re.search(r'CAPA:\s*(\d+)', texto_ia)
                segundo = int(match.group(1)) if match else 1
                cap = cv2.VideoCapture(file_path)
                cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                success, frame = cap.read()
                if success:
                    st.subheader("📸 Frame de Capa (Produto)")
                    st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)
                    ret, buffer = cv2.imencode('.jpg', frame)
                    st.download_button("📥 Baixar Capa", buffer.tobytes(), "capa_shopee.jpg", "image/jpeg")
                cap.release()
                
                st.warning("⚠️ **Dica de Ouro:** Na Shopee, vídeos de 15 a 30 segundos convertem 40% mais que vídeos longos.")

            if score >= 75: st.balloons()
            genai.delete_file(video_file.name)

        except Exception as e:
            st.error(f"Erro: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
