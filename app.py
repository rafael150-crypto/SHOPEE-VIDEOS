import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time
from PIL import Image

# Configuração da Página
st.set_page_config(page_title="BrendaBot Shopee + Banana Pro", page_icon="🍌", layout="wide")

st.title("🍌 BrendaBot Shopee Seller - Banana Pro Edition")
st.caption("Análise de Vídeo + Geração de Capa Profissional com IA")

# Configurar API
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)

# Lista de modelos por prioridade
MODELOS_PRIORIDADE = ['gemini-3-flash', 'gemini-2.5-flash-lite']

uploaded_file = st.file_uploader("📂 Arraste o vídeo do produto aqui...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    file_path = tfile.name
    
    with st.spinner("🕵️ Analisando produto e criando capa profissional..."):
        try:
            # 1. Análise do Vídeo
            video_file = genai.upload_file(path=file_path)
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            prompt_video = """
            Analise este vídeo de produto e retorne:
            1. [DESCRICAO_VISUAL]: Descreva o produto detalhadamente (cor, material, forma) para gerar uma imagem.
            2. [PONTUACAO]: Nota de venda.
            3. LEGENDA: Texto limpo.
            4. TAGS: 3 hashtags.
            """
            
            # Fallback de modelos
            response = None
            for m in MODELOS_PRIORIDADE:
                try:
                    model = genai.GenerativeModel(m)
                    response = model.generate_content([video_file, prompt_video])
                    break
                except: continue

            if response:
                texto_ia = response.text
                
                # Extrair descrição para a IA de imagem
                desc_match = re.search(r'\[DESCRICAO_VISUAL\]:(.*?)(?=\[PONTUACAO\]|LEGENDA|$)', texto_ia, re.S)
                descricao_produto = desc_match.group(1).strip() if desc_match else "Produto de ecommerce"
                
                # 2. Geração da Capa com "Banana Pro" (Nano Banana)
                # Criamos um prompt focado em fundo limpo
                prompt_imagem = f"A professional e-commerce product photography of {descricao_produto}, centered, clean white background, high resolution, studio lighting, 4k."
                
                # Chamada para geração de imagem
                image_response = genai.GenerativeModel('imagen-3').generate_content(prompt_imagem)
                
                # Exibição
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("📝 Ativos para Postagem")
                    legenda = re.search(r'LEGENDA:(.*?)(?=TAGS|$)', texto_ia, re.S).group(1).strip()
                    tags = re.search(r'TAGS:(.*?)$', texto_ia, re.S).group(1).strip()
                    
                    # Cópia Direta e Limpa
                    texto_final = f"{legenda}\n\n{tags}"
                    st.text_area("Copiar e Colar:", texto_final, height=150)
                    st.caption(f"Caracteres: {len(texto_final)}/150")

                with col2:
                    st.subheader("🖼️ Capa Gerada (Banana Pro)")
                    try:
                        # Mostra a imagem gerada pela IA
                        st.image(image_response.candidates[0].content.parts[0].inline_data.data, use_container_width=True)
                        st.success("Capa criada com fundo limpo profissional!")
                    except:
                        st.warning("Não foi possível gerar a imagem, mostrando frame do vídeo.")
                        # Fallback: mostra frame do vídeo se a geração falhar
                        cap = cv2.VideoCapture(file_path)
                        cap.set(cv2.CAP_PROP_POS_MSEC, 2000)
                        ret, frame = cap.read()
                        if ret: st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)
                        cap.release()

            genai.delete_file(video_file.name)
        except Exception as e:
            st.error(f"Erro: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
