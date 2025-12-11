"""
Gerador de Baseplates Gridfinity - Versão Standalone com Espaçadores de Centralização
Desenha a geometria "na mão" para garantir compatibilidade e controle total.
"""

from build123d import *
from typing import List, Tuple, Optional
from .constants import *

class BasePlateGenerator:
    def __init__(self, optimize_for_a1_mini: bool = True):
        self.optimize_for_a1_mini = optimize_for_a1_mini
        self.max_units = A1_MINI_MAX_UNITS if optimize_for_a1_mini else 20

    # --- Lógica de Cálculo (Matemática) ---

    def calculate_grid_from_drawer(self, drawer_x_mm: float, drawer_y_mm: float) -> Tuple[int, int, float, float]:
        """
        Calcula unidades e a sobra total em cada eixo.
        Retorna: (units_x, units_y, sobra_x, sobra_y)
        """
        units_x = int(drawer_x_mm // GRID_UNIT)
        units_y = int(drawer_y_mm // GRID_UNIT)
        
        # Garante pelo menos 1 unidade
        units_x = max(1, units_x)
        units_y = max(1, units_y)

        # Calcula a sobra total (espaço vazio que precisa ser preenchido)
        # Ex: Gaveta 300mm, Grid 7x42=294mm -> Sobra 6mm
        sobra_x = drawer_x_mm - (units_x * GRID_UNIT)
        sobra_y = drawer_y_mm - (units_y * GRID_UNIT)
        
        # Margem de segurança para não ficar apertado demais (0.5mm total)
        # Se a sobra for muito pequena (<1mm), ignoramos para não criar paredes finas demais que quebram
        if sobra_x > 1.0: sobra_x -= 0.5 
        else: sobra_x = 0
            
        if sobra_y > 1.0: sobra_y -= 0.5
        else: sobra_y = 0

        return units_x, units_y, sobra_x, sobra_y

    def calculate_tiling_strategy(self, total_x: int, total_y: int) -> List[Tuple[int, int, int, int]]:
        tiles = []
        for x in range(0, total_x, self.max_units):
            for y in range(0, total_y, self.max_units):
                chunk_x = min(self.max_units, total_x - x)
                chunk_y = min(self.max_units, total_y - y)
                tiles.append((x, y, chunk_x, chunk_y))
        return tiles

    # --- Geometria dos Conectores (Gridfinity Refined) ---

    def _get_connector_cutout_shape(self) -> Part:
        """Cria o formato do BURACO do conector (fêmea)"""
        middle_width = 6.0 / 2
        middle_height = 3.0
        thickness = 10.0 
        
        with BuildPart() as part:
            with BuildSketch() as sketch:
                with BuildLine():
                    l0 = Line((0, 0), (middle_width, 0))
                    l1 = Line(l0 @ 1, (middle_width, middle_height))
                    l2 = Line(l1 @ 1, ((l1 @ 1).X + 4, (l1 @ 1).Y + 3))
                    l3 = Line(l2 @ 1, ((l2 @ 1).X, (l2 @ 1).Y + 3))
                    Line(l3 @ 1, (0, (l3 @ 1).Y))
                    mirror(about=Plane.YZ)
                make_face()
            extrude(sketch.sketch, thickness)
        return part.part

    def _create_connector_clip(self) -> Part:
        """Cria o CLIP físico (macho)"""
        middle_width = 5.8 / 2
        middle_height = 6.5 / 2
        thickness = 2.8
        chamfer_value = 0.4

        with BuildPart() as part:
            with BuildSketch() as sketch:
                with BuildLine():
                    l1 = Line((middle_width, 0), (middle_width, middle_height))
                    l2 = Line(l1 @ 1, ((l1 @ 1).X + 3.9, (l1 @ 1).Y + 2.92))
                    l3 = Line(l2 @ 1, ((l2 @ 1).X, (l2 @ 1).Y + 2.53))
                    Line(l3 @ 1, (0, (l3 @ 1).Y))
                    mirror(about=Plane.XZ)
                    mirror(about=Plane.YZ)
                make_face()
            extrude(sketch.sketch, thickness)
            try:
                faces = [face.edges() for face in part.faces().filter_by(Axis.Z)]
                chamfer(faces, chamfer_value)
            except:
                pass 
        return part.part

    # --- Geometria do Baseplate (Modo Verboso/Manual) ---

    def _create_simple_baseplate(self, size_x: int, size_y: int, has_cutouts: dict, spacers: dict) -> Part:
        """
        Cria o baseplate com possíveis espaçadores laterais (abas).
        spacers: dict {'left': float, 'right': float, 'top': float, 'bottom': float} (em mm)
        """
        grid_width = size_x * GRID_UNIT
        grid_depth = size_y * GRID_UNIT
        
        # Calcula dimensões totais incluindo espaçadores
        # O corpo principal cresce para os lados
        total_width = grid_width + spacers['left'] + spacers['right']
        total_depth = grid_depth + spacers['top'] + spacers['bottom']
        
        # O centro do retângulo base precisa ser deslocado para compensar os espaçadores assimétricos
        # Se eu adiciono 5mm na esquerda, o centro move 2.5mm para a esquerda
        center_offset_x = (spacers['right'] - spacers['left']) / 2
        center_offset_y = (spacers['top'] - spacers['bottom']) / 2

        with BuildPart() as base:
            # 1. Base Sólida (Grid + Espaçadores)
            with BuildSketch(Plane.XY):
                with Locations((center_offset_x, center_offset_y)):
                    RectangleRounded(total_width, total_depth, BASEPLATE_CORNER_RADIUS)
            extrude(amount=BASEPLATE_HEIGHT)

            # 2. Recortes dos "Squares" (Gridfinity Profile)
            # O Grid deve começar alinhado à esquerda/baixo "lógico" da peça, ignorando o espaçador
            # A origem (0,0) do nosso sistema de coordenadas local deve ser o centro do GRID, não da peça total
            # Mas como mudamos o centro do retângulo, precisamos ajustar onde os furos caem.
            
            # Simplificação: Iterar relativo ao centro geométrico do GRID
            for ix in range(size_x):
                for iy in range(size_y):
                    # Posição do centro de cada célula relativa ao centro do GRID puro
                    cx = (ix - (size_x - 1) / 2) * GRID_UNIT
                    cy = (iy - (size_y - 1) / 2) * GRID_UNIT
                    
                    # Corte superior
                    with BuildSketch(Plane.XY.offset(BASEPLATE_HEIGHT)):
                        with Locations((cx, cy)):
                            RectangleRounded(GRID_UNIT - 0.5, GRID_UNIT - 0.5, BASEPLATE_CORNER_RADIUS - 0.25)
                    extrude(amount=-BASEPLATE_LIP_HEIGHT, mode=Mode.SUBTRACT)

                    # Corte inferior
                    with BuildSketch(Plane.XY.offset(BASEPLATE_HEIGHT - BASEPLATE_LIP_HEIGHT)):
                        with Locations((cx, cy)):
                            RectangleRounded(
                                GRID_UNIT - 0.5 - BASEPLATE_LIP_WIDTH*2, 
                                GRID_UNIT - 0.5 - BASEPLATE_LIP_WIDTH*2, 
                                BASEPLATE_CORNER_RADIUS - 0.5
                            )
                    extrude(amount=-(BASEPLATE_HEIGHT - BASEPLATE_LIP_HEIGHT), mode=Mode.SUBTRACT)

            # 3. Cortes Laterais (Conectores)
            cutout_tool = self._get_connector_cutout_shape()
            
            # As posições dos cortes são relativas ao centro do GRID
            if has_cutouts.get('right'):
                tool = cutout_tool.rotate(Axis.X, -90).rotate(Axis.Z, -90)
                tool = tool.move(Location((grid_width/2, 0, BASEPLATE_HEIGHT/2)))
                add(tool, mode=Mode.SUBTRACT)

            if has_cutouts.get('left'):
                tool = cutout_tool.rotate(Axis.X, -90).rotate(Axis.Z, 90)
                tool = tool.move(Location((-grid_width/2, 0, BASEPLATE_HEIGHT/2)))
                add(tool, mode=Mode.SUBTRACT)

            if has_cutouts.get('top'):
                tool = cutout_tool.rotate(Axis.X, -90).rotate(Axis.Z, 180)
                tool = tool.move(Location((0, grid_depth/2, BASEPLATE_HEIGHT/2)))
                add(tool, mode=Mode.SUBTRACT)

            if has_cutouts.get('bottom'):
                tool = cutout_tool.rotate(Axis.X, -90)
                tool = tool.move(Location((0, -grid_depth/2, BASEPLATE_HEIGHT/2)))
                add(tool, mode=Mode.SUBTRACT)

        return base.part

    # --- Fluxo Principal ---

    def generate_from_drawer(
        self, 
        drawer_x_mm: float, 
        drawer_y_mm: float, 
        include_connectors: bool = True
    ) -> Tuple[Compound, int, int, List[Tuple[int, int, int, int]], int]:
        
        # 1. Calcula Grid e Sobras
        units_x, units_y, sobra_x, sobra_y = self.calculate_grid_from_drawer(drawer_x_mm, drawer_y_mm)
        
        # Calcula tamanho do espaçador por lado (divide a sobra por 2)
        spacer_x = sobra_x / 2
        spacer_y = sobra_y / 2
        
        # 2. Define Tiles
        tiles = self.calculate_tiling_strategy(units_x, units_y)
        
        parts_export = []
        spacing = A1_MINI_MAX_UNITS * GRID_UNIT + 20 # Aumentei um pouco o espaçamento visual

        # 3. Gera cada Tile
        for idx, (pos_x, pos_y, size_x, size_y) in enumerate(tiles):
            # Lógica de Conectores (quem é meu vizinho?)
            has_right = (pos_x + size_x) < units_x
            has_left = pos_x > 0
            has_top = (pos_y + size_y) < units_y
            has_bottom = pos_y > 0
            
            cutouts = {
                'right': has_right,
                'left': has_left,
                'top': has_top,
                'bottom': has_bottom
            }

            # Lógica de Espaçadores (quem toca a borda da gaveta?)
            # Se eu estou na borda esquerda (x=0), recebo o spacer_x na esquerda
            my_spacers = {
                'left': spacer_x if pos_x == 0 else 0,
                'right': spacer_x if (pos_x + size_x) == units_x else 0,
                'bottom': spacer_y if pos_y == 0 else 0,
                'top': spacer_y if (pos_y + size_y) == units_y else 0
            }

            # Gera a peça com os espaçadores específicos
            part = self._create_simple_baseplate(size_x, size_y, cutouts, my_spacers)
            
            # Posiciona para exportação
            loc_x = (idx % 3) * spacing
            loc_y = (idx // 3) * spacing
            
            # Adiciona cópia independente
            part_copy = Part(part.wrapped).move(Location((loc_x, loc_y, 0)))
            parts_export.append(part_copy)

        # 4. Gera Clipes (Macho)
        num_connectors = 0
        if len(tiles) > 1 and include_connectors:
            clip = self._create_connector_clip()
            num_connectors = len(tiles) * 2 
            
            for i in range(num_connectors):
                # Coloca os clips numa área separada
                clip_copy = Part(clip.wrapped).move(Location((-50, i * 20, 0)))
                parts_export.append(clip_copy)

        return Compound(children=parts_export), units_x, units_y, tiles, num_connectors

    def get_tiling_description(self, tiles):
        if len(tiles) == 1:
            return "Peça única."
        return f"Dividido em {len(tiles)} partes."

    def get_generation_summary(self, ux, uy, tiles, n_conn):
        return f"Grid {ux}x{uy} ({len(tiles)} partes + {n_conn} conectores)"

    def needs_tiling(self, ux, uy):
        return ux > self.max_units or uy > self.max_units