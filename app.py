"""
Gridfinity Generator Web App
Otimizado para Bambu Lab A1 Mini

Aplicação Streamlit para gerar arquivos Gridfinity personalizados
com suporte a Smart Tiling para impressoras pequenas.
"""

import streamlit as st
import tempfile
import os
from typing import List, Tuple

# Tenta importar build123d - pode falhar se não instalado
try:
    from build123d import Compound, Part, export_stl
    from gridfinity import BasePlateGenerator, BinGenerator
    from gridfinity.constants import GRID_UNIT, A1_MINI_MAX_UNITS, GRID_HEIGHT_UNIT, A1_MINI_BUILD_VOLUME_X
    from gridfinity.export_utils import create_download_zip, export_to_stl_bytes, get_file_size_str, create_individual_parts_zip
    BUILD123D_AVAILABLE = True
except ImportError as e:
    BUILD123D_AVAILABLE = False
    IMPORT_ERROR = str(e)


# Configuração da página
st.set_page_config(
    page_title="Gridfinity Generator",
    page_icon="🗃️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #155a8a;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Função principal da aplicação."""
    
    # Header
    st.markdown('<div class="main-header">🗃️ Gridfinity Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Gere baseplates e bins Gridfinity personalizados para sua gaveta</div>', unsafe_allow_html=True)
    
    # Verificação de dependências
    if not BUILD123D_AVAILABLE:
        st.error(f"""
        ⚠️ **Dependências não instaladas**
        
        O módulo `build123d` não foi encontrado. Execute o seguinte comando para instalar:
        
        ```bash
        pip install -r requirements.txt
        ```
        
        Erro: {IMPORT_ERROR}
        """)
        return
    
    # Sidebar - Configurações
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Toggle para A1 Mini
        optimize_a1_mini = st.checkbox(
            "🖨️ Otimizar para Bambu Lab A1 Mini (Max 180mm)",
            value=True,
            help="Se marcado, divide automaticamente baseplates maiores que 4x4 unidades"
        )
        
        if optimize_a1_mini:
            st.info(f"**Limite ativo:** Máximo {A1_MINI_MAX_UNITS}x{A1_MINI_MAX_UNITS} unidades ({A1_MINI_MAX_UNITS * GRID_UNIT:.0f}mm)")
        else:
            st.warning("**Modo ilimitado:** Gera peças inteiras (requer impressora maior)")
        
        st.divider()
        
        # Informações do Gridfinity
        st.header("📐 Especificações Gridfinity")
        st.markdown(f"""
        - **Unidade base:** {GRID_UNIT}mm × {GRID_UNIT}mm
        - **Altura da unidade:** {GRID_HEIGHT_UNIT}mm
        - **Limite A1 Mini:** {A1_MINI_MAX_UNITS}x{A1_MINI_MAX_UNITS} = {A1_MINI_MAX_UNITS * GRID_UNIT:.0f}mm
        """)
        
        # Status do sistema
        st.divider()
        st.header("📦 Status do Sistema")
        st.success("✅ Sistema Gridfinity Standalone - Sem dependências externas")
    
    # Tabs principais
    tab_baseplate, tab_bins, tab_help = st.tabs(["🔲 Baseplate", "📦 Bins (Caixas)", "❓ Ajuda"])
    
    # ===== TAB BASEPLATE =====
    with tab_baseplate:
        st.header("🔲 Gerador de Baseplate")
        st.markdown("Insira as dimensões internas da sua gaveta para calcular o grid Gridfinity ideal.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            drawer_x = st.number_input(
                "📏 Largura da gaveta (mm)",
                min_value=42,
                max_value=2000,
                value=300,
                step=10,
                help="Dimensão interna da gaveta no eixo X"
            )
        
        with col2:
            drawer_y = st.number_input(
                "📐 Profundidade da gaveta (mm)",
                min_value=42,
                max_value=2000,
                value=400,
                step=10,
                help="Dimensão interna da gaveta no eixo Y"
            )
        
        # Cálculos
        generator = BasePlateGenerator(optimize_for_a1_mini=optimize_a1_mini)
        units_x, units_y, sobra_x, sobra_y = generator.calculate_grid_from_drawer(drawer_x, drawer_y)
        tiles = generator.calculate_tiling_strategy(units_x, units_y)
        needs_tiling = generator.needs_tiling(units_x, units_y)
        
        # Feedback visual
        st.subheader("📊 Análise do Grid")
        
        total_width = units_x * GRID_UNIT
        total_depth = units_y * GRID_UNIT
        spacer_x = sobra_x / 2
        spacer_y = sobra_y / 2
        
        # Calcula limite máximo de espaçador baseado no maior tile
        max_tile_size = max(max(t[2], t[3]) for t in tiles) if tiles else 4
        max_spacer_allowed = A1_MINI_BUILD_VOLUME_X - (max_tile_size * GRID_UNIT) if optimize_a1_mini else 999
        spacer_truncado = (spacer_x > max_spacer_allowed or spacer_y > max_spacer_allowed) and optimize_a1_mini
        
        # Aplica o limite
        spacer_x_efetivo = min(spacer_x, max_spacer_allowed) if optimize_a1_mini else spacer_x
        spacer_y_efetivo = min(spacer_y, max_spacer_allowed) if optimize_a1_mini else spacer_y
        
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        
        with col_info1:
            st.metric("Grid Calculado", f"{units_x} × {units_y} unidades")
        
        with col_info2:
            st.metric("Dimensão Total", f"{total_width:.0f} × {total_depth:.0f}mm")
        
        with col_info3:
            st.metric("Peças a Gerar", len(tiles))
        
        with col_info4:
            if spacer_x_efetivo > 0 or spacer_y_efetivo > 0:
                st.metric("Espaçadores", f"{spacer_x_efetivo:.1f} × {spacer_y_efetivo:.1f}mm")
            else:
                st.metric("Espaçadores", "Nenhum")
        
        # Info sobre espaçadores
        if spacer_x_efetivo > 0 or spacer_y_efetivo > 0:
            if spacer_truncado:
                st.markdown(f"""
                <div class="warning-box" style="padding: 10px; border-left: 4px solid #f0ad4e; background: #fcf8e3; margin: 10px 0;">
                    <strong>⚠️ Espaçador Limitado:</strong><br>
                    O espaçador ideal seria <strong>{spacer_x:.1f}mm × {spacer_y:.1f}mm</strong>, mas foi reduzido para 
                    <strong>{spacer_x_efetivo:.1f}mm × {spacer_y_efetivo:.1f}mm</strong> para caber na cama da A1 Mini (180mm).
                    O baseplate ficará ligeiramente descentrado.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="success-box">
                    <strong>📐 Centralização Automática:</strong><br>
                    Serão adicionadas abas de <strong>{spacer_x_efetivo:.1f}mm</strong> (esq/dir) e <strong>{spacer_y_efetivo:.1f}mm</strong> (cima/baixo) 
                    para travar o baseplate no centro da gaveta.
                </div>
                """, unsafe_allow_html=True)
        
        # Descrição da estratégia
        if needs_tiling and optimize_a1_mini:
            st.markdown(f"""
            <div class="info-box">
                <strong>📋 Estratégia de Divisão:</strong><br>
                Sua gaveta precisa de um grid <strong>{units_x}x{units_y}</strong>. 
                Como excede o limite da A1 Mini, {generator.get_tiling_description(tiles)}
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar detalhes das peças
            st.markdown("**Peças geradas:**")
            cols = st.columns(min(len(tiles), 4))
            for i, (pos_x, pos_y, size_x, size_y) in enumerate(tiles):
                with cols[i % 4]:
                    st.info(f"**Peça {i+1}:** {size_x}×{size_y}\n\nPosição: ({pos_x}, {pos_y})")
        else:
            st.markdown(f"""
            <div class="success-box">
                <strong>✅ Sem divisão necessária:</strong> Grid {units_x}×{units_y} cabe na mesa de impressão.
            </div>
            """, unsafe_allow_html=True)
        
        # Botão de geração
        st.divider()
        
        # Opção de conectores Refined
        include_connectors = st.checkbox(
            "🔗 Incluir conectores Refined",
            value=True,
            help="Gera clips para unir as peças do baseplate (recomendado se dividido)"
        )
        
        if st.button("🔧 Gerar Baseplate", key="gen_baseplate", type="primary"):
            with st.spinner("Gerando geometria 3D... Isso pode levar alguns segundos."):
                try:
                    compound, _, _, tiles_result, num_connectors = generator.generate_from_drawer(
                        drawer_x, drawer_y, include_connectors=include_connectors
                    )
                    
                    # Gera resumo
                    summary = generator.get_generation_summary(units_x, units_y, tiles_result, num_connectors)
                    
                    st.success(f"✅ {summary}")
                    
                    # Se há múltiplas peças, oferece download individual (melhor para alinhamento)
                    if len(tiles_result) > 1:
                        st.markdown("""
                        <div class="info-box">
                            <strong>💡 Dica para Bambu Studio:</strong><br>
                            Use o <strong>ZIP Individual</strong> para importar cada peça separadamente.
                            Cada arquivo está centrado na origem para facilitar o alinhamento automático.
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_dl1, col_dl2 = st.columns(2)
                        
                        with col_dl1:
                            # ZIP com peças individuais (recomendado)
                            zip_bytes = create_individual_parts_zip(compound, "baseplate")
                            st.download_button(
                                label="⬇️ ZIP Individual (Recomendado)",
                                data=zip_bytes,
                                file_name="baseplate_individual_parts.zip",
                                mime="application/zip",
                                help="Cada peça em arquivo separado, centrada na origem"
                            )
                        
                        with col_dl2:
                            # STL único com tudo junto
                            stl_bytes = export_to_stl_bytes(compound)
                            st.download_button(
                                label="⬇️ STL Único (Tudo junto)",
                                data=stl_bytes,
                                file_name="baseplate_full_set.stl",
                                mime="application/octet-stream",
                                help="Todas as peças em um único arquivo"
                            )
                    else:
                        # Peça única - download direto
                        stl_bytes = export_to_stl_bytes(compound)
                        st.info(f"📁 Tamanho do arquivo: {get_file_size_str(len(stl_bytes))}")
                        
                        st.download_button(
                            label="⬇️ Download STL",
                            data=stl_bytes,
                            file_name="baseplate.stl",
                            mime="application/octet-stream"
                        )
                except Exception as e:
                    st.error(f"❌ Erro ao gerar baseplate: {str(e)}")
    
    # ===== TAB BINS =====
    with tab_bins:
        st.header("📦 Gerador de Bins (Caixas)")
        st.markdown("Crie caixas Gridfinity personalizadas para organizar seus itens.")
        
        bin_gen = BinGenerator(optimize_for_a1_mini=optimize_a1_mini)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            bin_x = st.number_input(
                "Largura (unidades)",
                min_value=1,
                max_value=10,
                value=2,
                help="Número de unidades Gridfinity no eixo X"
            )
        
        with col2:
            bin_y = st.number_input(
                "Profundidade (unidades)",
                min_value=1,
                max_value=10,
                value=2,
                help="Número de unidades Gridfinity no eixo Y"
            )
        
        with col3:
            bin_height = st.number_input(
                "Altura (unidades)",
                min_value=1,
                max_value=10,
                value=3,
                help="Altura em unidades (1 unidade = 7mm)"
            )
        
        # Validação
        is_valid, validation_msg = bin_gen.validate_size(bin_x, bin_y)
        
        if not is_valid:
            st.markdown(f"""
            <div class="error-box">
                {validation_msg}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="success-box">
                {validation_msg}
            </div>
            """, unsafe_allow_html=True)
        
        # Opções adicionais
        st.subheader("🎛️ Opções do Bin")
        
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            with_label = st.checkbox("🏷️ Área para etiqueta", value=False)
            with_scoop = st.checkbox("🥄 Rampa (scoop)", value=False)
        
        with col_opt2:
            with_dividers = st.checkbox("➕ Divisórias internas", value=False)
            
            if with_dividers:
                div_x = st.number_input("Divisões X", min_value=1, max_value=bin_x, value=min(2, bin_x))
                div_y = st.number_input("Divisões Y", min_value=1, max_value=bin_y, value=1)
            else:
                div_x, div_y = 1, 1
        
        # Métricas do bin
        st.subheader("📐 Dimensões do Bin")
        
        bin_width_mm = bin_x * GRID_UNIT - 0.5
        bin_depth_mm = bin_y * GRID_UNIT - 0.5
        bin_height_mm = bin_height * GRID_HEIGHT_UNIT
        
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            st.metric("Largura", f"{bin_width_mm:.1f}mm")
        with col_m2:
            st.metric("Profundidade", f"{bin_depth_mm:.1f}mm")
        with col_m3:
            st.metric("Altura", f"{bin_height_mm:.1f}mm")
        
        # Botão de geração
        st.divider()
        
        if st.button("🔧 Gerar Bin", key="gen_bin", type="primary", disabled=not is_valid):
            with st.spinner("Gerando geometria 3D do bin..."):
                try:
                    if with_dividers and (div_x > 1 or div_y > 1):
                        bin_part = bin_gen.generate_divider_bin(
                            bin_x, bin_y, bin_height, div_x, div_y
                        )
                    else:
                        bin_part = bin_gen.generate_bin(
                            bin_x, bin_y, bin_height,
                            with_label=with_label,
                            with_scoop=with_scoop
                        )
                    
                    stl_bytes = export_to_stl_bytes(bin_part)
                    
                    st.success(f"✅ Bin gerado com sucesso! Tamanho: {get_file_size_str(len(stl_bytes))}")
                    
                    filename = f"bin_{bin_x}x{bin_y}x{bin_height}u.stl"
                    
                    st.download_button(
                        label="⬇️ Download STL",
                        data=stl_bytes,
                        file_name=filename,
                        mime="application/octet-stream"
                    )
                except Exception as e:
                    st.error(f"❌ Erro ao gerar bin: {str(e)}")
    
    # ===== TAB AJUDA =====
    with tab_help:
        st.header("❓ Ajuda")
        
        st.markdown("""
        ## O que é Gridfinity?
        
        Gridfinity é um sistema modular de organização criado por Zack Freedman. 
        Consiste em baseplates (bases) e bins (caixas) que se encaixam em um grid padronizado de 42mm × 42mm.
        
        ## Como usar este gerador
        
        ### 1. Baseplate
        1. Meça as dimensões internas da sua gaveta em milímetros
        2. Insira os valores na aba "Baseplate"
        3. O sistema calculará automaticamente quantas unidades cabem
        4. Se você estiver usando uma A1 Mini, o sistema dividirá automaticamente peças grandes
        5. Clique em "Gerar Baseplate" e faça o download do STL
        
        ### 2. Bins
        1. Escolha as dimensões do bin em unidades Gridfinity
        2. Selecione opções adicionais (etiqueta, rampa, divisórias)
        3. Clique em "Gerar Bin" e faça o download
        
        ## Smart Tiling (Divisão Inteligente)
        
        Se você possui uma **Bambu Lab A1 Mini** (volume 180×180×180mm), o sistema 
        automaticamente divide baseplates grandes em peças menores que cabem na mesa.
        
        **Exemplo:** Uma gaveta que precisa de grid 6×6:
        - Peça 1: 4×4 (bloco principal)
        - Peça 2: 2×4 (restante do eixo X)
        - Peça 3: 4×2 (restante do eixo Y)
        - Peça 4: 2×2 (canto)
        
        Todas as peças vêm em um único arquivo STL. Ao abrir no Bambu Studio, 
        use "Auto-Arrange" para posicioná-las na mesa.
        
        ## Sobre Bins
        
        ⚠️ **Importante:** Diferente de baseplates, bins NÃO podem ser divididos 
        automaticamente, pois são estruturas únicas. Se você tentar criar um bin 
        maior que 4×4 unidades com a opção A1 Mini ativada, receberá um alerta.
        
        ## Dicas de Impressão
        
        - Use **0.2mm layer height** para boa qualidade
        - **15-20% infill** é suficiente para bins
        - Para baseplates, **3 wall loops** garantem rigidez
        - Material recomendado: **PLA ou PETG**
        """)
        
        st.divider()
        
        st.markdown("""
        ## 📚 Recursos
        
        - [Gridfinity Original (YouTube)](https://www.youtube.com/watch?v=ra_9zU-mnl8)
        - [Printables - Gridfinity Collection](https://www.printables.com/model/174715-gridfinity-specification)
        - [Build123d Documentation](https://build123d.readthedocs.io/)
        """)


if __name__ == "__main__":
    main()
