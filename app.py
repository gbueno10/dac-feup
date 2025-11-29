import streamlit as st
import subprocess
import os
import platform

# =========================================================
# CONFIGURAÇÃO DO OPENSCAD (IMPORTANTE!)
# =========================================================
# Se o comando 'openscad' não estiver no PATH do seu sistema,
# você precisa dizer onde o programa está instalado.
# Edite a linha abaixo se necessário:

CAMINHO_OPENSCAD = "/opt/homebrew/bin/openscad"

# Exemplo no Windows (se não funcionar direto):
# CAMINHO_OPENSCAD = r"C:\Program Files\OpenSCAD\openscad.exe"

# =========================================================
# FRONTEND (A Interface)
# =========================================================
st.set_page_config(page_title="Gridfinity Factory", page_icon="📦")

st.title("📦 Fábrica Gridfinity Local")
st.markdown("Gere caixas usando o motor original do OpenSCAD, controlado por Python.")

col1, col2 = st.columns(2)

with col1:
    st.header("Dimensões")
    width = st.number_input("Largura (Units)", min_value=0.5, max_value=10.0, value=2.0, step=0.5)
    depth = st.number_input("Profundidade (Units)", min_value=1.0, max_value=10.0, value=1.0, step=1.0)
    height = st.number_input("Altura (Units)", min_value=2, max_value=20, value=3, step=1)

with col2:
    st.header("Opções")
    chambers = st.number_input("Divisórias (X)", 1, 10, 1)
    with_label = st.checkbox("Incluir Aba de Etiqueta (Label)", value=False)
    fingerslide = st.checkbox("Arredondamento Interno (Fingerslide)", value=True)
    holes = st.checkbox("Furos para Ímãs", value=True)

# Lógica dos parâmetros booleanos para o OpenSCAD
label_val = "true" if with_label else "disabled" # O SCAD original usa string ou bool dependendo da versão, mas string costuma ser seguro aqui se o script esperar string
fingerslide_val = "true" if fingerslide else "false"
magnet_val = "6.5" if holes else "0" # 6.5mm é o padrão, 0 remove

# =========================================================
# BACKEND (O Wrapper)
# =========================================================
if st.button("🚀 Gerar STL", type="primary"):
    
    output_filename = f"gridfinity_{width}x{depth}x{height}_div{chambers}.stl"
    
    # Montando o comando do terminal
    # -D define variáveis dentro do script .scad antes de rodar
    cmd = [
        CAMINHO_OPENSCAD,
        "-o", output_filename,
        "gridfinity_basic_cup.scad", # O arquivo alvo
        "-D", f"width={width}",
        "-D", f"depth={depth}",
        "-D", f"height={height}",
        "-D", f"chambers={chambers}",
        "-D", f"withLabel=\"{label_val}\"", # Aspas escapadas para strings
        "-D", f"fingerslide={fingerslide_val}",
        "-D", f"magnet_diameter={magnet_val}"
    ]

    status_text = st.empty()
    status_text.info("🔨 O OpenSCAD está martelando sua peça... aguarde.")

    try:
        # Executa o comando no sistema operacional
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            status_text.success("✅ Sucesso! Peça gerada.")
            
            # Mostra botão de download
            with open(output_filename, "rb") as file:
                st.download_button(
                    label="📥 Baixar Arquivo STL",
                    data=file,
                    file_name=output_filename,
                    mime="application/octet-stream"
                )
                
            # (Opcional) Visualizador rápido se tiver uma imagem gerada, 
            # mas aqui focamos no STL.
            
        else:
            status_text.error("❌ Erro ao gerar.")
            with st.expander("Ver detalhes do erro"):
                st.code(result.stderr)
                
    except FileNotFoundError:
        status_text.error("❌ O executável do OpenSCAD não foi encontrado.")
        st.warning(f"Verifique a variável 'CAMINHO_OPENSCAD' no código. O sistema tentou rodar: `{CAMINHO_OPENSCAD}`")
