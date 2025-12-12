"""
Gerador de Bins (Caixas) Gridfinity
"""

from build123d import *
from typing import Tuple, Optional
from .constants import *


class BinGenerator:
    """
    Gera bins (caixas) Gridfinity personalizados.
    """
    
    def __init__(self, optimize_for_a1_mini: bool = True):
        """
        Inicializa o gerador de bins.
        
        Args:
            optimize_for_a1_mini: Se True, valida contra limite de 4x4 unidades
        """
        self.optimize_for_a1_mini = optimize_for_a1_mini
        self.max_units = A1_MINI_MAX_UNITS if optimize_for_a1_mini else 999
    
    def validate_size(self, units_x: int, units_y: int) -> Tuple[bool, str]:
        """
        Valida se o tamanho do bin é compatível com a impressora.
        
        Args:
            units_x: Unidades no eixo X
            units_y: Unidades no eixo Y
            
        Returns:
            Tuple com (is_valid, message)
        """
        if not self.optimize_for_a1_mini:
            return True, "Validação desativada."
        
        width_mm = units_x * GRID_UNIT
        depth_mm = units_y * GRID_UNIT
        
        if units_x > self.max_units or units_y > self.max_units:
            return False, (
                f"⚠️ ALERTA DE INCOMPATIBILIDADE: "
                f"Bin {units_x}x{units_y} ({width_mm:.0f}x{depth_mm:.0f}mm) "
                f"excede o limite da A1 Mini (máximo {self.max_units}x{self.max_units} = "
                f"{self.max_units * GRID_UNIT:.0f}mm). "
                f"Diferente de baseplates, bins não podem ser divididos e remontados."
            )
        
        return True, f"✅ Bin {units_x}x{units_y} compatível com A1 Mini."
    
    def generate_bin(
        self,
        units_x: int,
        units_y: int,
        height_units: int = 3,
        with_label: bool = False,
        wall_thickness: float = BIN_WALL_THICKNESS
    ) -> Part:
        """
        Gera um bin Gridfinity com perfil de encaixe correto (por célula).
        
        Args:
            units_x: Número de unidades no eixo X
            units_y: Número de unidades no eixo Y
            height_units: Altura em unidades (1 unidade = 7mm)
            with_label: Adiciona área para etiqueta na frente
            wall_thickness: Espessura da parede
            
        Returns:
            Objeto Part representando o bin
        """
        width = units_x * GRID_UNIT - 0.5  # Folga para encaixe
        depth = units_y * GRID_UNIT - 0.5
        height = height_units * GRID_HEIGHT_UNIT
        
        internal_width = width - wall_thickness * 2
        internal_depth = depth - wall_thickness * 2
        
        # Constantes do perfil de encaixe (lip) - baseado no padrão Gridfinity
        # O perfil encaixa nos recortes do baseplate
        lip_base_size = GRID_UNIT - 0.5  # 41.5mm - tamanho do recorte no baseplate
        lip_inner_size = lip_base_size - BASEPLATE_LIP_WIDTH * 2  # Parte inferior do lip
        lip_total_height = BASEPLATE_HEIGHT  # 4.65mm - altura total do lip
        lip_step_height = BASEPLATE_LIP_HEIGHT  # 2.15mm - altura do degrau superior
        
        # Altura interna: do fundo (acima do lip + bottom) até o topo
        internal_height = height - lip_total_height - BIN_BOTTOM_THICKNESS
        
        with BuildPart() as bin_part:
            # 1. Corpo externo do bin (começa ACIMA do lip)
            with BuildSketch(Plane.XY.offset(lip_total_height)) as outer:
                RectangleRounded(
                    width=width,
                    height=depth,
                    radius=BIN_CORNER_RADIUS
                )
            extrude(amount=height - lip_total_height)
            
            # 2. Cavidade interna
            with BuildSketch(Plane.XY.offset(lip_total_height + BIN_BOTTOM_THICKNESS)) as inner:
                RectangleRounded(
                    width=internal_width,
                    height=internal_depth,
                    radius=BIN_CORNER_RADIUS - wall_thickness
                )
            extrude(amount=internal_height, mode=Mode.SUBTRACT)
            
            # 3. Lip (borda superior) para empilhamento
            lip_outer = BIN_LIP_WIDTH  # 2.6mm
            lip_height = BIN_LIP_HEIGHT  # 4.4mm
            
            with BuildSketch(Plane.XY.offset(height)) as lip:
                RectangleRounded(
                    width=width,
                    height=depth,
                    radius=BIN_CORNER_RADIUS
                )
                RectangleRounded(
                    width=width - lip_outer * 2,
                    height=depth - lip_outer * 2,
                    radius=BIN_CORNER_RADIUS - lip_outer,
                    mode=Mode.SUBTRACT
                )
            extrude(amount=-lip_height, mode=Mode.SUBTRACT)
            
            # 4. PERFIS DE ENCAIXE NO BASEPLATE (por célula!)
            # Cada célula do bin precisa de seu próprio perfil que encaixa no baseplate
            for ix in range(units_x):
                for iy in range(units_y):
                    # Centro desta célula (relativo ao centro do bin)
                    cx = (ix - (units_x - 1) / 2) * GRID_UNIT
                    cy = (iy - (units_y - 1) / 2) * GRID_UNIT
                    
                    # Parte SUPERIOR do lip (degrau) - encaixa no recorte superior do baseplate
                    # Tamanho: 41.5mm, altura: do topo (4.65mm) descendo 2.15mm
                    with BuildSketch(Plane.XY.offset(lip_total_height)):
                        with Locations((cx, cy)):
                            RectangleRounded(
                                lip_base_size,
                                lip_base_size,
                                BASEPLATE_CORNER_RADIUS - 0.25
                            )
                    extrude(amount=-lip_step_height)
                    
                    # Parte INFERIOR do lip (base mais estreita) - encaixa no recorte inferior
                    # Tamanho: 41.5 - 1.6 = 39.9mm, altura: 4.65 - 2.15 = 2.5mm
                    with BuildSketch(Plane.XY.offset(lip_total_height - lip_step_height)):
                        with Locations((cx, cy)):
                            RectangleRounded(
                                lip_inner_size,
                                lip_inner_size,
                                BASEPLATE_CORNER_RADIUS - 0.5
                            )
                    extrude(amount=-(lip_total_height - lip_step_height))
            
            # 5. Recursos opcionais - Label (etiqueta)
            if with_label:
                label_width = width * 0.8
                label_height = 12  # mm
                label_depth = 0.6  # profundidade do rebaixo
                
                with BuildSketch(Plane.XZ.offset(-depth / 2)) as label:
                    with Locations([(0, height - label_height / 2 - 2)]):
                        RectangleRounded(
                            width=label_width,
                            height=label_height,
                            radius=1.5
                        )
                extrude(amount=label_depth, mode=Mode.SUBTRACT)
        
        return bin_part.part
    
    def generate_divider_bin(
        self,
        units_x: int,
        units_y: int,
        height_units: int = 3,
        divisions_x: int = 1,
        divisions_y: int = 1
    ) -> Part:
        """
        Gera um bin com divisórias internas.
        
        Args:
            units_x: Unidades no eixo X
            units_y: Unidades no eixo Y
            height_units: Altura em unidades
            divisions_x: Número de divisões no eixo X
            divisions_y: Número de divisões no eixo Y
            
        Returns:
            Objeto Part representando o bin com divisórias
        """
        # Primeiro, gera o bin base
        base_bin = self.generate_bin(units_x, units_y, height_units)
        
        width = units_x * GRID_UNIT - 0.5
        depth = units_y * GRID_UNIT - 0.5
        height = height_units * GRID_HEIGHT_UNIT
        
        internal_width = width - BIN_WALL_THICKNESS * 2
        internal_depth = depth - BIN_WALL_THICKNESS * 2
        
        # Altura das divisórias: mesma altura da cavidade interna
        # Fundo = BASEPLATE_HEIGHT + BIN_BOTTOM_THICKNESS = 5.45mm
        # Topo = height (mesmo da cavidade, que vai até o topo do bin)
        divider_base_z = BASEPLATE_HEIGHT + BIN_BOTTOM_THICKNESS
        divider_height = height - divider_base_z  # Igual à cavidade interna
        
        divider_thickness = 1.0  # mm
        
        with BuildPart() as bin_with_dividers:
            add(base_bin)
            
            # Divisórias no eixo X
            # Usamos Plane.YZ no offset X, o retângulo tem (largura_Y, altura_Z)
            if divisions_x > 1:
                cell_width = internal_width / divisions_x
                for i in range(1, divisions_x):
                    x_pos = -internal_width / 2 + cell_width * i
                    # Desenha na base Z e extrude para cima
                    with BuildSketch(Plane.YZ.offset(x_pos)):
                        # Centro do retângulo no meio da altura da divisória
                        center_z = divider_base_z + divider_height / 2
                        with Locations((0, center_z)):
                            Rectangle(internal_depth, divider_height)
                    extrude(amount=divider_thickness / 2, both=True)
            
            # Divisórias no eixo Y
            if divisions_y > 1:
                cell_depth = internal_depth / divisions_y
                for i in range(1, divisions_y):
                    y_pos = -internal_depth / 2 + cell_depth * i
                    with BuildSketch(Plane.XZ.offset(y_pos)):
                        center_z = divider_base_z + divider_height / 2
                        with Locations((0, center_z)):
                            Rectangle(internal_width, divider_height)
                    extrude(amount=divider_thickness / 2, both=True)
        
        return bin_with_dividers.part
