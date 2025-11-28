import streamlit as st
import subprocess
import os
import platform

# =========================================================
# CONFIGURAÇÃO DO OPENSCAD (IMPORTANTE!)
# =========================================================
# O OpenSCAD foi instalado via Homebrew no macOS
# O comando 'openscad' já está disponível no PATH

CAMINHO_OPENSCAD = "openscad"

# =========================================================
# FRONTEND (A Interface)
# =========================================================
st.set_page_config(page_title="Gridfinity Factory", page_icon="📦")

st.title("📦 Fábrica Gridfinity Local")
st.markdown("Gere caixas usando o motor original do OpenSCAD, controlado por Python.")

col1, col2 = st.columns(2)

with col1:
    st.header("Dimensões")
    gridx = st.number_input("Largura (Grid X)", min_value=1, max_value=10, value=2, step=1)
    gridy = st.number_input("Profundidade (Grid Y)", min_value=1, max_value=10, value=1, step=1)
    gridz = st.number_input("Altura (Grid Z - 7mm units)", min_value=2, max_value=20, value=6, step=1)

with col2:
    st.header("Opções")
    divx = st.number_input("Divisórias em X", 0, 10, 1)
    divy = st.number_input("Divisórias em Y", 0, 10, 1)
    scoop = st.slider("Scoop (arredondamento)", 0.0, 1.0, 1.0, 0.1)
    magnet_holes = st.checkbox("Furos para Ímãs", value=False)
    screw_holes = st.checkbox("Furos para Parafusos", value=False)

# =========================================================
# BACKEND (O Wrapper)
# =========================================================
if st.button("🚀 Gerar STL", type="primary"):
    
    output_filename = f"gridfinity_{gridx}x{gridy}x{gridz}_div{divx}x{divy}.stl"
    
    # Montando o comando do terminal
    # -D define variáveis dentro do script .scad antes de rodar
    cmd = [
        CAMINHO_OPENSCAD,
        "-o", output_filename,
        "gridfinity_basic_cup.scad",
        "-D", f"gridx={gridx}",
        "-D", f"gridy={gridy}",
        "-D", f"gridz={gridz}",
        "-D", f"divx={divx}",
        "-D", f"divy={divy}",
        "-D", f"scoop={scoop}",
        "-D", f"magnet_holes={str(magnet_holes).lower()}",
        "-D", f"screw_holes={str(screw_holes).lower()}",
        "-D", "refined_holes=false"  # Desabilita refined_holes quando magnet_holes está ativo
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
                
            # Exibe informações sobre o arquivo gerado
            file_size = os.path.getsize(output_filename) / 1024  # KB
            st.info(f"📊 Tamanho do arquivo: {file_size:.2f} KB")
            
        else:
            status_text.error("❌ Erro ao gerar.")
            with st.expander("Ver detalhes do erro"):
                st.code(result.stderr)
                
    except FileNotFoundError:
        status_text.error("❌ O executável do OpenSCAD não foi encontrado.")
        st.warning(f"Verifique a variável 'CAMINHO_OPENSCAD' no código. O sistema tentou rodar: `{CAMINHO_OPENSCAD}`")
        st.info("💡 No macOS, o caminho geralmente é: `/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD`")
