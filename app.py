import streamlit as st
import subprocess
import os
import platform
import math

# =========================================================
# CONFIGURAÇÃO DO OPENSCAD (IMPORTANTE!)
# =========================================================
CAMINHO_OPENSCAD = "/opt/homebrew/bin/openscad"

# =========================================================
# FRONTEND (A Interface)
# =========================================================
st.set_page_config(page_title="Gridfinity Factory", page_icon="📦", layout="wide")

st.title("📦 Fábrica Gridfinity Local")

# Selection Mode
mode = st.radio("Modo de Geração", ["Bin (Caixa)", "Baseplate (Base)"], horizontal=True)

def run_openscad(cmd, output_filename):
    status_text = st.empty()
    status_text.info("🔨 O OpenSCAD está martelando... aguarde.")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            status_text.success("✅ Sucesso! STL gerado.")
            with open(output_filename, "rb") as file:
                st.download_button("📥 Baixar STL", file, output_filename, "application/octet-stream")
        else:
            status_text.error("❌ Erro ao gerar.")
            st.code(result.stderr)
    except FileNotFoundError:
        status_text.error("❌ OpenSCAD não encontrado. Verifique o caminho.")


if mode == "Bin (Caixa)":
    st.markdown("Gere caixas usando o motor original do OpenSCAD, controlado por Python.")
    col1, col2 = st.columns(2)

    with col1:
        st.header("Dimensões")
        width = st.number_input("Largura (Units)", min_value=0.5, max_value=10.0, value=2.0, step=0.5, key="w1")
        depth = st.number_input("Profundidade (Units)", min_value=1.0, max_value=10.0, value=1.0, step=1.0, key="d1")
        height = st.number_input("Altura (Units)", min_value=2, max_value=20, value=3, step=1, key="h1")

    with col2:
        st.header("Opções")
        chambers = st.number_input("Divisórias (X)", 1, 10, 1, key="c1")
        with_label = st.checkbox("Incluir Aba de Etiqueta (Label)", value=False, key="l1")
        fingerslide = st.checkbox("Arredondamento Interno (Fingerslide)", value=True, key="f1")
        holes = st.checkbox("Furos para Ímãs", value=True, key="m1")

    # Lógica dos parâmetros booleanos para o OpenSCAD
    label_val = "true" if with_label else "disabled"
    fingerslide_val = "true" if fingerslide else "false"
    magnet_val = "6.5" if holes else "0"

    if st.button("🚀 Gerar STL Bin", type="primary"):
        output_filename = f"gridfinity_bin_{width}x{depth}x{height}.stl"
        
        # Update path to point to scad/ folder
        scad_file = os.path.join("scad", "gridfinity_basic_cup.scad")
        
        cmd = [
            CAMINHO_OPENSCAD,
            "-o", output_filename,
            scad_file,
            "-D", f"width={width}",
            "-D", f"depth={depth}",
            "-D", f"height={height}",
            "-D", f"chambers={chambers}",
            "-D", f"withLabel=\"{label_val}\"",
            "-D", f"fingerslide={fingerslide_val}",
            "-D", f"magnet_diameter={magnet_val}"
        ]
        run_openscad(cmd, output_filename)

else: # Baseplate Mode
    st.subheader("Configuração da Base")
    
    col_base1, col_base2 = st.columns(2)
    with col_base1:
        st.markdown("##### Otimização de Impressora")
        preset = st.selectbox("Preset de Tamanho", 
                            ["Custom", "Bambu Lab A1 Mini (Max 168x168mm)", "Prusa Mini (Max 168x168mm)", "Standard Printer (Max 210x210mm)"])
        
        # Safe limits in Gridfinity UNITS (integer)
        max_safe_units = 999
        if "A1 Mini" in preset or "Prusa Mini" in preset:
            max_safe_units = 4 # 168mm
        elif "Standard" in preset:
            max_safe_units = 5 # 210mm
        
        # Default values logic in mm
        if "A1 Mini" in preset or "Prusa Mini" in preset:
            default_w_mm, default_d_mm = 168.0, 168.0
        elif "Standard" in preset:
            default_w_mm, default_d_mm = 210.0, 210.0
        else:
            default_w_mm, default_d_mm = 84.0, 84.0 # 2 units
    
    with col_base2:
        st.markdown("##### Dimensões Reais (mm)")
        st.caption("O sistema calculará as Unidades Gridfinity (42mm) inteiras que cabem nessa medida.")
        b_width_mm = st.number_input("Largura (mm)", 42.0, 1000.0, default_w_mm, 1.0, key="bw_mm")
        b_depth_mm = st.number_input("Profundidade (mm)", 42.0, 1000.0, default_d_mm, 1.0, key="bd_mm")

    # Calculate Integer Units
    # Gridfinity pitch is 42mm. We usually floor to ensure it fits, or round?
    # Spec says 42mm. If I say 200mm space in drawer.
    # 200 / 42 = 4.76 -> 4 units (168mm). The rest is gap.
    b_width_units = math.floor(b_width_mm / 42.0)
    b_depth_units = math.floor(b_depth_mm / 42.0)
    
    real_w = b_width_units * 42
    real_d = b_depth_units * 42
    
    st.markdown(f"📏 **Resultado Gridfinity:** {b_width_units} x {b_depth_units} Unidades")
    st.caption(f"Dimensão Final da Peça: {real_w}mm x {real_d}mm (Sobra: {b_width_mm - real_w:.1f}mm / {b_depth_mm - real_d:.1f}mm)")

    if b_width_units < 1 or b_depth_units < 1:
        st.error("Dimensões muito pequenas! Mínimo 42mm.")
        st.stop()

    # Check if splitting is needed
    needs_split = (b_width_units > max_safe_units) or (b_depth_units > max_safe_units)
    
    if needs_split:
        st.info(f"🧩 **Auto-Split Ativado**: A base de {b_width_units}x{b_depth_units} units excede o limite seguro da impressora ({max_safe_units}x{max_safe_units} units). Será dividida automaticamente.")

    if st.button("🚀 Gerar Baseplate", type="primary"):
        import zipfile
        import io
        
        files_to_zip = []
        scad_file = os.path.join("scad", "gridfinity_baseplate.scad")
        
        status_text = st.empty()
        status_text.info("🔨 Calculando geometria...")
        
        if not needs_split:
            # Simple single generation
            output_filename = f"gridfinity_baseplate_{b_width_units}x{b_depth_units}.stl"
            cmd = [
                CAMINHO_OPENSCAD,
                "-o", output_filename,
                scad_file,
                "-D", f"width={b_width_units}",
                "-D", f"depth={b_depth_units}"
            ]
            run_openscad(cmd, output_filename)
        else:
            # Splitting Logic
            chunks_x = []
            rem_x = b_width_units
            while rem_x > 0:
                chunk = min(rem_x, max_safe_units)
                chunks_x.append(chunk)
                rem_x -= chunk
                
            chunks_y = []
            rem_y = b_depth_units
            while rem_y > 0:
                chunk = min(rem_y, max_safe_units)
                chunks_y.append(chunk)
                rem_y -= chunk
            
            generated_files = []
            
            # Progress bar
            progress_bar = st.progress(0)
            total_chunks = len(chunks_x) * len(chunks_y) + 1 # +1 for clip
            current_chunk = 0
            
            # Generate Connector Clip first
            clip_filename = "gridfinity_connector_clip.stl"
            cmd_clip = [
                CAMINHO_OPENSCAD,
                "-o", clip_filename,
                scad_file,
                "-D", "render_key=true"
            ]
            res = subprocess.run(cmd_clip, capture_output=True, text=True)
            if res.returncode == 0:
                generated_files.append(clip_filename)
            else:
                st.error("Erro ao gerar conector")
            
            current_chunk += 1
            progress_bar.progress(current_chunk / total_chunks)
            
            # Generate Chunks
            for i, cx in enumerate(chunks_x):
                for j, cy in enumerate(chunks_y):
                    # Determine connectivity
                    conn_top = "true" if j < len(chunks_y) - 1 else "false"
                    conn_bottom = "true" if j > 0 else "false"
                    conn_right = "true" if i < len(chunks_x) - 1 else "false"
                    conn_left = "true" if i > 0 else "false"
                    
                    part_name = f"baseplate_part_{i}_{j}_{cx}x{cy}.stl"
                    
                    cmd_part = [
                        CAMINHO_OPENSCAD,
                        "-o", part_name,
                        scad_file,
                        "-D", f"width={cx}",
                        "-D", f"depth={cy}",
                        "-D", f"side_conn_top={conn_top}",
                        "-D", f"side_conn_bottom={conn_bottom}",
                        "-D", f"side_conn_right={conn_right}",
                        "-D", f"side_conn_left={conn_left}"
                    ]
                    
                    subprocess.run(cmd_part, capture_output=True)
                    generated_files.append(part_name)
                    
                    current_chunk += 1
                    progress_bar.progress(current_chunk / total_chunks)
            
            status_text.success(f"✅ Gerados {len(generated_files)} arquivos!")
            
            # Create Zip
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for f in generated_files:
                    zf.write(f, arcname=f)
                    os.remove(f) # Clean up
            
            zip_filename = f"gridfinity_baseplate_{b_width_units}x{b_depth_units}_split.zip"
            
            st.download_button(
                label=f"📦 Baixar ZIP ({len(generated_files)} arquivos)",
                data=zip_buffer.getvalue(),
                file_name=zip_filename,
                mime="application/zip"
            )
