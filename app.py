import streamlit as st
import google.generativeai as genai
import cv2
import os
import re
import tempfile
import time

# Configuração da Página
st.set_page_config(page_title="BrendaBot Shopee Expert", page_icon="🧡", layout="wide")

# Configurar API
API_KEY = "AIzaSyCiJyxLVYVgI7EiTuQmkQGTi1nWiQn9g_8"
genai.configure(api_key=API_KEY)
MODELOS = ['gemini-3-flash', 'gemini-2.5-flash-lite']

# Inicializar estados de sessão
if 'texto_copiar' not in st.session_state: st.session_state.texto_copiar = ""
if 'relatorio_expert' not in st.session_state: st.session_state.relatorio_expert = ""

def limpar_e_travar_150(texto):
    """Extrai, limpa vírgulas e trava em 150 caracteres"""
    try:
        titulo = re.search(r'TITULO_VENDA:(.*?)(?=TAGS|$)', texto, re.S).group(1).strip()
        tags = re.search(r'TAGS:(.*?)(?=---|$)', texto, re.S).group(1).strip()
        
        # Limpeza de títulos e caracteres especiais
        titulo = re.sub(r'^[\s\d.*-]*', '', titulo)
        
        # Especialista em Tags: Remove vírgulas e garante o #
        tags = tags.replace(',', ' ').replace('.', ' ')
        tags_limpas = []
        for word in tags.split():
            word = word.strip()
            if word:
                if not word.startswith('#'): word = f"#{word}"
                tags_limpas.append(word)
        
        # Garante exatamente 4 tags e monta o texto
        resultado = f"{titulo} {' '.join(tags_limpas[:4])}"
        
        # CORTE RÍGIDO EM 150 CARACTERES
        return resultado[:150]
    except:
        return "Erro ao gerar ativos."

st.title("🧡 Shopee Expert: 150 Chars Direct")

uploaded_file = st.file_uploader("📂 Suba o vídeo...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    file_path = tfile.name
    
    if st.button("🚀 Gerar Título e Tags (Máx 150)") or st.session_state.texto_copiar == "":
        with st.spinner("🕵️ Consultando Copywriter..."):
            try:
                video_file = genai.upload_file(path=file_path)
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)
                
                prompt = """
                Atue como Copywriter Expert. Analise o vídeo e retorne:
                --- ATIVOS ---
                TITULO_VENDA: (Título magnético)
                TAGS: (4 hashtags com # separadas por espaço, SEM VÍRGULAS)
                --- FIM ---
                REGRA: Título + Tags não podem passar de 145 caracteres.
                # CONSULTORIA
                (Resumo técnico da venda)
                CAPA_LIMPA: X
                """
                
                model = genai.GenerativeModel('gemini-3-flash')
                response = model.generate_content([video_file, prompt])
                
                if response:
                    st.session_state.relatorio_expert = response.text.split('# CONSULTORIA')[-1].split('CAPA_LIMPA:')[0].strip()
                    st.session_state.texto_copiar = limpar_e_travar_150(response.text)
                
                genai.delete_file(video_file.name)
            except Exception as e:
                st.error(f"Erro: {e}")
            finally:
                if os.path.exists(file_path): os.remove(file_path)

    if st.session_state.texto_copiar:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📋 Título + 4 Tags")
            # Componente de texto que permite selecionar e copiar facilmente
            st.text_area("Cópia Direta:", st.session_state.texto_copiar, height=100, label_visibility="collapsed")
            
            # Contador visual
            chars = len(st.session_state.texto_copiar)
            st.write(f"📊 **{chars}/150 caracteres**")
            
            if st.button("🔄 Recriar Nova Opção"):
                with st.spinner("🔄 Gerando..."):
                    model = genai.GenerativeModel('gemini-2.5-flash-lite')
                    nova = model.generate_content(f"Gere um NOVO TITULO e 4 TAGS (com # e sem vírgula) para: {st.session_state.relatorio_expert}. Máximo 150 caracteres.")
                    st.session_state.texto_copiar = limpar_e_travar_150(nova.text)
                    st.rerun()

        with col2:
            st.subheader("👨‍🏫 Por que este título?")
            st.info(st.session_state.relatorio_expert if st.session_state.relatorio_expert else "Análise concluída.")
                st.subheader("🖼️ Capa")
                st.image(st.session_state.capa_frame, use_container_width=True)
                st.caption(f"Caracteres: {len(st.session_state.texto_copiar)}/150")
