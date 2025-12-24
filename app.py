import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time

# Configuração da Página
st.set_page_config(page_title="BrendaBot Shopee Anti-Block", page_icon="🧡", layout="wide")

# Configurar API
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)

# ORDEM DE PRIORIDADE (Baseada nas suas cotas livres 0/10 e 0/5)
MODELOS_DISPONIVEIS = [
    'gemini-2.5-flash-lite', 
    'gemini-3-flash',
    'gemini-1.5-flash'
]

st.title("🧡 Shopee Seller - Gerador de Ativos")
st.caption("Sistema com proteção de cota e fallback automático.")

uploaded_file = st.file_uploader("📂 Suba o vídeo do seu Produto...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # 1. Salvar arquivo temporário
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    st.info("📦 Processando vídeo... Aguarde a análise da IA.")
    
    try:
        # 2. Upload para o File API do Google
        # Importante: O upload do vídeo costuma ter cota separada
        video_file = genai.upload_file(path=video_path)
        
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
            
        prompt = """
        Atue como Especialista Shopee. Analise o vídeo e retorne:
        1. [PONTUACAO_VENDA]: Nota 0-100.
        2. LEGENDA_CURTA: Máximo 130 caracteres.
        3. HASHTAGS: 3 tags.
        4. AUDITORIA: Risco de banimento (marca d'água ou estático).
        5. CAPA: segundo sugerido.
        """

        # 3. Tentar gerar conteúdo com Fallback e Tempo de Espera
        response = None
        modelo_sucesso = ""
        
        for nome_modelo in MODELOS_DISPONIVEIS:
            try:
                model = genai.GenerativeModel(nome_modelo)
                response = model.generate_content([video_file, prompt])
                modelo_sucesso = nome_modelo
                break # Se funcionar, sai do loop
            except Exception as e:
                if "429" in str(e):
                    st.warning(f"Cota cheia no modelo {nome_modelo}. Tentando o próximo...")
                    time.sleep(1) # Pausa pequena para não estressar a API
                    continue
                else:
                    st.error(f"Erro no modelo {nome_modelo}: {e}")
        
        if response:
            st.success(f"✅ Analisado com {modelo_sucesso}")
            texto_ia = response.text
            
            # --- LAYOUT DE RESULTADOS ---
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("🎯 Ativos Shopee")
                # Extração via Regex
                legenda = re.search(r'LEGENDA_CURTA:(.*?)(?=HASHTAGS|$)', texto_ia, re.S)
                tags = re.search(r'HASHTAGS:(.*?)(?=AUDITORIA|$)', texto_ia, re.S)
                
                txt_legenda = legenda.group(1).strip() if legenda else "Confira!"
                txt_tags = tags.group(1).strip() if tags else "#shopee"
                
                st.text_area("Legenda (Copiar):", f"{txt_legenda} {txt_tags}", height=120)
                st.write(f"Caracteres: {len(txt_legenda) + len(txt_tags) + 1}/150")
                
                st.markdown("---")
                st.markdown(texto_ia)
            
            with col2:
                # Extração e exibição da CAPA
                match_capa = re.search(r'CAPA:\s*(\d+)', texto_ia)
                segundo = int(match_capa.group(1)) if match_capa else 1
                
                cap = cv2.VideoCapture(video_path)
                cap.set(cv2.CAP_PROP_POS_MSEC, segundo * 1000)
                ret, frame = cap.read()
                if ret:
                    st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True, caption="Capa Sugerida")
                cap.release()
            
            # Limpeza na API do Google para liberar cota de armazenamento
            genai.delete_file(video_file.name)
            
        else:
            st.error("❌ Todos os modelos atingiram o limite de cota. Tente novamente em 1 minuto.")

    except Exception as e:
        st.error(f"Erro geral: {e}")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
