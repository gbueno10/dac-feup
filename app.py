import streamlit as st
import subprocess
import os
import platform
import numpy as np
import cv2
from PIL import Image
from cv_utils import detect_a4, extract_object_contour, smooth_contour, contour_to_openscad_points

# =========================================================
# CONFIGURAÇÃO DO OPENSCAD (IMPORTANTE!)
# =========================================================
CAMINHO_OPENSCAD = "/opt/homebrew/bin/openscad"

# =========================================================
# FRONTEND (A Interface)
# =========================================================
st.set_page_config(page_title="Gridfinity Factory", page_icon="📦", layout="wide")

st.title("📦 Fábrica Gridfinity Local")

tab1, tab2, tab3 = st.tabs(["🏭 Fábrica Padrão", "📸 Escanear Objeto", "🔬 Debug OpenCV"])

with tab1:
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

    if st.button("🚀 Gerar STL Padrão", type="primary"):
        output_filename = f"gridfinity_{width}x{depth}x{height}_div{chambers}.stl"
        
        cmd = [
            CAMINHO_OPENSCAD,
            "-o", output_filename,
            "gridfinity_basic_cup.scad",
            "-D", f"width={width}",
            "-D", f"depth={depth}",
            "-D", f"height={height}",
            "-D", f"chambers={chambers}",
            "-D", f"withLabel=\"{label_val}\"",
            "-D", f"fingerslide={fingerslide_val}",
            "-D", f"magnet_diameter={magnet_val}"
        ]

        status_text = st.empty()
        status_text.info("🔨 O OpenSCAD está martelando sua peça... aguarde.")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                status_text.success("✅ Sucesso! Peça gerada.")
                with open(output_filename, "rb") as file:
                    st.download_button("📥 Baixar STL", file, output_filename, "application/octet-stream")
            else:
                status_text.error("❌ Erro ao gerar.")
                st.code(result.stderr)
        except FileNotFoundError:
            status_text.error("❌ OpenSCAD não encontrado.")

from streamlit_image_coordinates import streamlit_image_coordinates
from streamlit_drawable_canvas import st_canvas

# Funções com cache para evitar reprocessamento
@st.cache_data
def process_image(file_bytes):
    image = cv2.imdecode(file_bytes, 1)
    return image

# Import new functions
from cv_utils import find_a4_at_point, find_object_at_point, find_all_a4_candidates, create_contour_overlay

with tab2:
    st.header("📸 Escanear Objeto (Modo Avançado)")
    st.markdown("1. Envie a foto.\\n2. **Clique na máscara da folha A4** para selecioná-la.\\n3. **Ajuste os cantos** se necessário.\\n4. **Clique no objeto** para criar o recorte.")

    uploaded_file = st.file_uploader("Envie a foto", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        # Usar cache para carregar a imagem
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = process_image(file_bytes)
        
        # State management for interactive flow
        if 'a4_candidates' not in st.session_state:
            st.session_state.a4_candidates = None
        if 'a4_data' not in st.session_state:
            st.session_state.a4_data = None # (warped, scale, contour)
        if 'obj_data' not in st.session_state:
            st.session_state.obj_data = None # (contour_points, smoothed_points)
        if 'obj_candidates' not in st.session_state:
            st.session_state.obj_candidates = None
        if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != uploaded_file.name:
             # Reset if new file
             st.session_state.a4_candidates = None
             st.session_state.a4_data = None
             st.session_state.obj_data = None
             st.session_state.obj_candidates = None
             st.session_state.last_uploaded_file = uploaded_file.name

        # Step 1: Find all A4 candidates and show overlay
        st.subheader("Passo 1: Identificar Folha A4")
        
        # Find candidates on first load
        if st.session_state.a4_candidates is None:
            with st.spinner("Procurando folhas A4..."):
                st.session_state.a4_candidates = find_all_a4_candidates(image)
        
        candidates = st.session_state.a4_candidates
        
        if not candidates:
            st.error("Nenhuma folha A4 detectada. Tente outra imagem.")
        else:
            # Create and display overlay
            overlay = create_contour_overlay(image, candidates)
            
            # Resize for display
            max_width = 800
            h, w = overlay.shape[:2]
            if w > max_width:
                scale_factor = max_width / w
                new_h = int(h * scale_factor)
                display_overlay = cv2.resize(overlay, (max_width, new_h))
            else:
                scale_factor = 1.0
                display_overlay = overlay

            st.write(f"Encontradas {len(candidates)} possíveis folhas A4. **Clique na máscara colorida** para selecionar.")
            
            # Display overlay and capture click
            coords_a4 = streamlit_image_coordinates(display_overlay, key="a4_click")
            
            if coords_a4 is not None:
                # Scale coordinates back to original image size
                x = int(coords_a4['x'] / scale_factor)
                y = int(coords_a4['y'] / scale_factor)
                
                with st.spinner(f"Selecionando folha A4 em ({x}, {y})..."):
                    warped, scale, paper_contour = find_a4_at_point(image, (x, y))
                
                if warped is not None:
                    st.session_state.a4_data = (warped, scale, paper_contour)
                    st.session_state.obj_candidates = None  # Reset object candidates when new A4 is selected
                    st.session_state.obj_data = None  # Reset selected object
                    st.session_state.selected_objects = []  # Reset selections
                    st.session_state.custom_objects = []  # Reset custom objects
                    st.session_state.manual_refinement = False  # Reset refinement mode
                    st.success("Folha A4 detectada!")
                else:
                    st.error("Não foi possível encontrar uma folha A4 nesse ponto. Tente clicar mais no centro da folha.")

        # Show feedback if A4 found
        if st.session_state.a4_data is not None:
            warped, scale, paper_contour = st.session_state.a4_data
            
            # Draw contour on original (small preview)
            img_with_paper = image.copy()
            cv2.drawContours(img_with_paper, [paper_contour], -1, (0, 255, 0), 5)
            with st.expander("Ver Detecção na Imagem Original", expanded=False):
                st.image(img_with_paper, channels="BGR")

            st.divider()
            
            # Step 2: Object Detection
            st.subheader("Passo 2: Identificar Objeto")
            st.write(f"Escala: {scale:.2f} px/mm")
            
            # Add option to use manual mask
            use_manual_mask = st.checkbox("🎨 Usar Máscara Manual (Desenhar com Mouse)", value=False, key="use_mask")
            
            # Initialize mask in session state
            if 'manual_mask' not in st.session_state:
                st.session_state.manual_mask = None
            
            if use_manual_mask:
                st.info("💡 **Modo Máscara:** Desenhe sobre os objetos que deseja detectar. Use a borracha para corrigir.")
                
                # Prepare image for canvas
                h_canvas, w_canvas = warped.shape[:2]
                max_canvas_width = 800
                if w_canvas > max_canvas_width:
                    canvas_scale = max_canvas_width / w_canvas
                    canvas_h = int(h_canvas * canvas_scale)
                    canvas_w = max_canvas_width
                    canvas_img = cv2.resize(warped, (canvas_w, canvas_h))
                else:
                    canvas_scale = 1.0
                    canvas_h, canvas_w = h_canvas, w_canvas
                    canvas_img = warped.copy()
                
                # Convert BGR to RGB for display
                canvas_img_rgb = cv2.cvtColor(canvas_img, cv2.COLOR_BGR2RGB)
                
                col_canvas1, col_canvas2 = st.columns([3, 1])
                
                with col_canvas2:
                    st.markdown("**Controles:**")
                    drawing_mode = st.selectbox(
                        "Modo:",
                        ["freedraw", "line", "rect", "circle", "polygon", "transform"],
                        index=0,
                        key="draw_mode"
                    )
                    
                    stroke_width = st.slider("Espessura do Pincel:", 1, 50, 10, key="stroke_width")
                    stroke_color = st.color_picker("Cor:", "#00FF00", key="stroke_color")
                    
                    if st.button("🗑️ Limpar Máscara"):
                        st.session_state.manual_mask = None
                        st.rerun()
                
                with col_canvas1:
                    # Create canvas
                    canvas_result = st_canvas(
                        fill_color="rgba(0, 255, 0, 0.3)",
                        stroke_width=stroke_width,
                        stroke_color=stroke_color,
                        background_image=Image.fromarray(canvas_img_rgb),
                        update_streamlit=True,
                        height=canvas_h,
                        width=canvas_w,
                        drawing_mode=drawing_mode,
                        point_display_radius=0,
                        key="canvas",
                    )
                
                # Process canvas result
                if canvas_result.image_data is not None:
                    # Extract the drawn mask (alpha channel or color detection)
                    mask_data = canvas_result.image_data[:, :, :3]  # RGB channels
                    
                    # Create binary mask where anything drawn is white
                    mask_gray = cv2.cvtColor(mask_data.astype(np.uint8), cv2.COLOR_RGB2GRAY)
                    _, binary_mask = cv2.threshold(mask_gray, 1, 255, cv2.THRESH_BINARY)
                    
                    # Scale mask back to original warped image size if needed
                    if canvas_scale != 1.0:
                        binary_mask = cv2.resize(binary_mask, (w_canvas, h_canvas), interpolation=cv2.INTER_NEAREST)
                    
                    # Store in session state
                    st.session_state.manual_mask = binary_mask
                    
                    # Show mask preview
                    with st.expander("👁️ Ver Máscara", expanded=False):
                        st.image(binary_mask, caption="Máscara Binária", use_container_width=True, clamp=True)
                
                st.markdown("---")
            
            # Add controls to adjust detection sensitivity
            with st.expander("⚙️ Ajustar Sensibilidade da Detecção", expanded=False):
                col_sens1, col_sens2 = st.columns(2)
                with col_sens1:
                    min_area_percent = st.slider(
                        "Área Mínima do Objeto (%)", 
                        0.5, 10.0, 1.0, 0.5,
                        help="Objetos menores que esta porcentagem da folha serão ignorados"
                    )
                with col_sens2:
                    max_objects = st.slider(
                        "Máximo de Objetos", 
                        3, 20, 10, 1,
                        help="Número máximo de objetos a detectar"
                    )
                
                if st.button("🔄 Re-detectar Objetos"):
                    st.session_state.obj_candidates = None
                    st.session_state.obj_data = None
                    st.rerun()
            
            # Initialize object candidates if not present
            if 'obj_candidates' not in st.session_state:
                st.session_state.obj_candidates = None
            
            # Find all object candidates on first view
            if st.session_state.obj_candidates is None:
                with st.spinner("Detectando objetos na folha..."):
                    from cv_utils import find_all_object_candidates, create_object_overlay
                    
                    # Apply manual mask if available
                    mask_to_use = st.session_state.manual_mask if use_manual_mask else None
                    
                    st.session_state.obj_candidates = find_all_object_candidates(
                        warped, 
                        min_area_ratio=min_area_percent/100,
                        max_objects=max_objects,
                        mask=mask_to_use
                    )
            
            obj_candidates = st.session_state.obj_candidates
            
            if not obj_candidates:
                st.warning("Nenhum objeto detectado automaticamente. Tente ajustar a iluminação ou o contraste.")
                # Show the warped image anyway so user can see what was processed
                st.image(warped, caption="Folha A4 Corrigida (sem objetos detectados)", channels="BGR", use_container_width=True)
            else:
                # Create overlay with all detected objects
                obj_overlay = create_object_overlay(warped, obj_candidates)
                
                # Resize for display
                max_width_obj = 800
                h_w, w_w = obj_overlay.shape[:2]
                if w_w > max_width_obj:
                    scale_factor_obj = max_width_obj / w_w
                    new_h_obj = int(h_w * scale_factor_obj)
                    display_obj_overlay = cv2.resize(obj_overlay, (max_width_obj, new_h_obj))
                else:
                    scale_factor_obj = 1.0
                    display_obj_overlay = obj_overlay

                st.write(f"✅ Encontrados **{len(obj_candidates)}** objetos.")
                
                # Show object selection interface
                st.markdown("**Selecione os objetos que deseja incluir:**")
                
                # Initialize selected objects in session state
                if 'selected_objects' not in st.session_state:
                    st.session_state.selected_objects = []
                
                # Create columns for object selection
                cols_per_row = 3
                num_objects = len(obj_candidates)
                
                for i in range(0, num_objects, cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j in range(cols_per_row):
                        idx = i + j
                        if idx < num_objects:
                            with cols[j]:
                                obj = obj_candidates[idx]
                                area_cm2 = obj['area'] / (scale ** 2) / 100
                                
                                # Checkbox for selection
                                is_selected = st.checkbox(
                                    f"Objeto {idx+1}",
                                    key=f"obj_check_{idx}",
                                    value=idx in st.session_state.selected_objects
                                )
                                
                                # Update selection state
                                if is_selected and idx not in st.session_state.selected_objects:
                                    st.session_state.selected_objects.append(idx)
                                elif not is_selected and idx in st.session_state.selected_objects:
                                    st.session_state.selected_objects.remove(idx)
                                
                                # Show details
                                st.caption(f"📐 {area_cm2:.1f} cm²")
                                st.caption(f"🔹 Solidez: {obj['solidity']:.2f}")
                
                # Display image with selected objects highlighted
                st.image(display_obj_overlay, caption="Objetos Detectados - Selecione acima", use_container_width=True)
                
                # Button to refine selection
                if st.session_state.selected_objects:
                    st.success(f"✅ {len(st.session_state.selected_objects)} objeto(s) selecionado(s)")
                    
                    if st.button("✂️ Refinar Seleção Manualmente"):
                        st.info("💡 **Modo de Refinamento:** Clique diretamente na imagem acima para ajustar ou adicionar objetos individualmente.")
                        st.session_state.manual_refinement = True
                
                # Manual click refinement (optional)
                if st.session_state.get('manual_refinement', False):
                    coords_obj = streamlit_image_coordinates(display_obj_overlay, key="obj_click_refine")
                    
                    if coords_obj is not None:
                        ox = int(coords_obj['x'] / scale_factor_obj)
                        oy = int(coords_obj['y'] / scale_factor_obj)
                        
                        with st.spinner(f"Refinando seleção em ({ox}, {oy})..."):
                            obj_points = find_object_at_point(warped, (ox, oy), scale)
                            
                            if obj_points is not None:
                                # Add this as a custom object
                                if 'custom_objects' not in st.session_state:
                                    st.session_state.custom_objects = []
                                
                                smoothed = smooth_contour(obj_points, s=2.0)
                                st.session_state.custom_objects.append((obj_points, smoothed))
                                st.success(f"✅ Objeto refinado adicionado! Total: {len(st.session_state.custom_objects)}")
                                st.session_state.manual_refinement = False
                            else:
                                st.error("Não foi possível encontrar um objeto nesse ponto.")

            contour_points = None
            all_selected_contours = []
            
            # Collect all selected objects
            if st.session_state.selected_objects:
                for idx in st.session_state.selected_objects:
                    if idx < len(obj_candidates):
                        obj = obj_candidates[idx]
                        # Convert contour to mm coordinates
                        points_mm = []
                        h, w = warped.shape[:2]
                        center_x, center_y = w / 2, h / 2
                        for point in obj['contour']:
                            px, py = point[0]
                            mm_x = (px - center_x) / scale
                            mm_y = (center_y - py) / scale
                            points_mm.append([mm_x, mm_y])
                        
                        smoothed = smooth_contour(points_mm, s=2.0)
                        all_selected_contours.append(smoothed)
            
            # Add custom refined objects
            if st.session_state.get('custom_objects'):
                for obj_points, smoothed in st.session_state.custom_objects:
                    all_selected_contours.append(smoothed)
            
            # Visualize all selected objects
            if all_selected_contours:
                h, w = warped.shape[:2]
                cx, cy = w/2, h/2
                vis_img = warped.copy()
                
                # Draw all selected contours
                colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
                for idx, smoothed_points in enumerate(all_selected_contours):
                    pts_px = []
                    for x_mm, y_mm in smoothed_points:
                        px = int(x_mm * scale + cx)
                        py = int(cy - y_mm * scale)
                        pts_px.append([px, py])
                    color = colors[idx % len(colors)]
                    cv2.polylines(vis_img, [np.array(pts_px)], True, color, 3)
                
                st.image(vis_img, caption=f"{len(all_selected_contours)} Objeto(s) Selecionado(s)", channels="BGR")
                
                # Configuration for the box
                st.divider()
                st.subheader("Configurar Caixa Personalizada")
                
                col_opts1, col_opts2 = st.columns(2)
                with col_opts1:
                    c_width = st.number_input("Largura da Caixa (Units)", 1.0, 10.0, 3.0, 0.5, key="cw")
                    c_depth = st.number_input("Profundidade da Caixa (Units)", 1.0, 10.0, 2.0, 0.5, key="cd")
                    c_height = st.number_input("Altura da Caixa (Units)", 2, 20, 3, 1, key="ch")
                with col_opts2:
                    margin = st.slider("Folga do Recorte (mm)", 0.0, 5.0, 1.0, 0.1)
                    cut_depth = st.number_input("Profundidade do Recorte (mm)", 1.0, 50.0, 10.0, 1.0)

                if st.button("🚀 Gerar Caixa Personalizada"):
                    # Generate OpenSCAD code with multiple cutouts
                    cutout_code = ""
                    for idx, smoothed_points in enumerate(all_selected_contours):
                        poly_str = contour_to_openscad_points(smoothed_points)
                        cutout_code += f"""
        // Cutout {idx + 1}
        translate([0, 0, height*7 - {cut_depth}])
        linear_extrude({cut_depth} + 5)
        offset(r={margin})
        polygon(points={poly_str});
        """
                    
                    # Create SCAD script with multiple cutouts
                    scad_script = f"""
                    include <gridfinity_modules.scad>
                    
                    width = {c_width};
                    depth = {c_depth};
                    height = {c_height};
                    
                    difference() {{
                        // Solid block
                        grid_block(width, depth, height);
                        
                        // Object cutouts
{cutout_code}
                    }}
                    """
                    
                    custom_scad_filename = "custom_cutout.scad"
                    with open(custom_scad_filename, "w") as f:
                        f.write(scad_script)
                        
                    output_custom = "custom_gridfinity.stl"
                    
                    cmd_custom = [CAMINHO_OPENSCAD, "-o", output_custom, custom_scad_filename]
                    
                    with st.spinner("Gerando geometria complexa..."):
                        res = subprocess.run(cmd_custom, capture_output=True, text=True)
                        
                        if res.returncode == 0:
                            st.success("Caixa gerada com sucesso!")
                            with open(output_custom, "rb") as f:
                                st.download_button("📥 Baixar STL Personalizado", f, output_custom, "application/octet-stream")
                        else:
                            st.error("Erro no OpenSCAD")
                            st.code(res.stderr)

with tab3:
    st.header("🔬 Debug e Testes de OpenCV")
    st.markdown("Visualize os diferentes métodos de processamento de imagem para entender e ajustar a detecção.")
    
    debug_file = st.file_uploader("Envie uma foto para testar", type=["jpg", "png", "jpeg"], key="debug_upload")
    
    if debug_file is not None:
        file_bytes_debug = np.asarray(bytearray(debug_file.read()), dtype=np.uint8)
        image_debug = cv2.imdecode(file_bytes_debug, 1)
        
        # Resize for faster processing
        max_width_debug = 800
        h_orig, w_orig = image_debug.shape[:2]
        if w_orig > max_width_debug:
            scale_debug = max_width_debug / w_orig
            new_h = int(h_orig * scale_debug)
            image_debug = cv2.resize(image_debug, (max_width_debug, new_h))
        
        st.subheader("📷 Imagem Original")
        st.image(image_debug, channels="BGR", caption="Original", use_container_width=True)
        
        st.divider()
        st.subheader("🎛️ Análise de Contraste e Iluminação")
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image_debug, cv2.COLOR_BGR2GRAY)
        
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        with col_stats1:
            st.metric("Média (Brilho)", f"{gray.mean():.1f}")
        with col_stats2:
            st.metric("Desvio Padrão", f"{gray.std():.1f}")
        with col_stats3:
            st.metric("Mínimo", f"{gray.min()}")
        with col_stats4:
            st.metric("Máximo", f"{gray.max()}")
        
        # Histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(hist, color='black')
        ax.set_xlim([0, 256])
        ax.set_xlabel('Intensidade de Pixel')
        ax.set_ylabel('Frequência')
        ax.set_title('Histograma - Distribuição de Brilho')
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        
        # Evaluate contrast quality
        contrast_score = gray.std()
        if contrast_score < 30:
            st.warning("⚠️ **Contraste BAIXO** - A imagem tem pouca variação de brilho. Considere melhorar a iluminação.")
        elif contrast_score < 50:
            st.info("ℹ️ **Contraste MODERADO** - Pode funcionar, mas melhor iluminação ajudaria.")
        else:
            st.success("✅ **Contraste BOM** - A imagem tem boa variação de brilho.")
        
        st.divider()
        st.subheader("🔍 Métodos de Detecção de Bordas")
        
        # Controls for edge detection
        col_controls1, col_controls2 = st.columns(2)
        with col_controls1:
            blur_kernel = st.slider("Tamanho do Blur (Gaussian)", 1, 15, 5, 2, key="blur")
            if blur_kernel % 2 == 0:
                blur_kernel += 1
            canny_low = st.slider("Canny - Threshold Baixo", 0, 200, 50, 5, key="canny_low")
        with col_controls2:
            canny_high = st.slider("Canny - Threshold Alto", 0, 300, 150, 5, key="canny_high")
            morph_kernel = st.slider("Tamanho Kernel Morfologia", 1, 15, 5, 2, key="morph")
        
        # Apply preprocessing
        blurred = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)
        
        # Method 1: Canny
        canny = cv2.Canny(blurred, canny_low, canny_high)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_kernel, morph_kernel))
        canny_dilated = cv2.dilate(canny, kernel, iterations=2)
        
        # Method 2: Otsu Thresholding
        _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        otsu_morphed = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel, iterations=2)
        otsu_morphed = cv2.morphologyEx(otsu_morphed, cv2.MORPH_OPEN, kernel)
        
        # Method 3: Adaptive Thresholding
        adapt_block = st.slider("Adaptive - Tamanho do Bloco", 3, 51, 15, 2, key="adapt_block")
        if adapt_block % 2 == 0:
            adapt_block += 1
        adapt_c = st.slider("Adaptive - Constante C", -10, 20, 3, 1, key="adapt_c")
        
        adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, adapt_block, adapt_c)
        adaptive_morphed = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel, iterations=2)
        adaptive_morphed = cv2.morphologyEx(adaptive_morphed, cv2.MORPH_OPEN, kernel)
        
        # Display results in grid
        st.markdown("### Resultados dos Métodos:")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.image(blurred, caption="1. Gaussian Blur", use_container_width=True, clamp=True)
            st.image(canny, caption="2. Canny (Raw)", use_container_width=True, clamp=True)
            st.image(canny_dilated, caption="3. Canny + Dilatação", use_container_width=True, clamp=True)
        
        with col_m2:
            st.image(otsu, caption="4. Otsu Threshold (Raw)", use_container_width=True, clamp=True)
            st.image(otsu_morphed, caption="5. Otsu + Morfologia", use_container_width=True, clamp=True)
            st.image(adaptive, caption="6. Adaptive Threshold (Raw)", use_container_width=True, clamp=True)
        
        st.image(adaptive_morphed, caption="7. Adaptive + Morfologia (MELHOR)", use_container_width=True, clamp=True)
        
        st.divider()
        st.subheader("🎯 Detecção de Contornos")
        
        # Choose which method to use for contour detection
        method_choice = st.radio(
            "Escolha o método para detectar contornos:",
            ["Canny + Dilatação", "Otsu + Morfologia", "Adaptive + Morfologia"],
            index=2
        )
        
        if method_choice == "Canny + Dilatação":
            edges_for_contours = canny_dilated
        elif method_choice == "Otsu + Morfologia":
            edges_for_contours = otsu_morphed
        else:
            edges_for_contours = adaptive_morphed
        
        # Find contours
        contours_debug, _ = cv2.findContours(edges_for_contours, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        st.write(f"**Total de contornos encontrados:** {len(contours_debug)}")
        
        # Filter by area
        min_area_slider = st.slider("Área Mínima (pixels²)", 100, 10000, 1000, 100, key="min_area_debug")
        max_area_slider = st.slider("Área Máxima (pixels²)", 1000, 500000, 100000, 1000, key="max_area_debug")
        
        filtered_contours = [c for c in contours_debug if min_area_slider <= cv2.contourArea(c) <= max_area_slider]
        
        st.write(f"**Contornos após filtro de área:** {len(filtered_contours)}")
        
        # Draw contours on original image
        img_with_contours = image_debug.copy()
        cv2.drawContours(img_with_contours, filtered_contours, -1, (0, 255, 0), 2)
        
        # Also show individual contours with info
        for idx, cnt in enumerate(filtered_contours[:10]):  # Limit to first 10
            area = cv2.contourArea(cnt)
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0
            
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(img_with_contours, (x, y), (x+w, y+h), (255, 0, 0), 1)
            
            # Draw contour number
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(img_with_contours, str(idx+1), (cx, cy), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        st.image(img_with_contours, channels="BGR", caption=f"Contornos Detectados (Top 10 de {len(filtered_contours)})", use_container_width=True)
        
        # Show details of contours
        with st.expander("📊 Detalhes dos Contornos Detectados"):
            for idx, cnt in enumerate(filtered_contours[:20]):
                area = cv2.contourArea(cnt)
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                solidity = area / hull_area if hull_area > 0 else 0
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                
                st.markdown(f"**Contorno {idx+1}**: Área={area:.0f}px² | Solidez={solidity:.2f} | Cantos={len(approx)}")
        
        st.divider()
        st.markdown("### 💡 Dicas para Melhorar a Detecção:")
        st.markdown("""
        - **Contraste baixo?** Aumente a iluminação ou use flash
        - **Muitos contornos?** Aumente a área mínima ou ajuste o threshold
        - **Poucos contornos?** Diminua a área mínima ou ajuste o Canny
        - **Objetos pretos?** Use THRESH_BINARY_INV (já aplicado)
        - **Sombras?** Melhore a iluminação uniforme
        """)

