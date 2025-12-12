"""
Gerador de Baseplates Gridfinity com Travamento Dovetail (Rabo de Andorinha)
Otimizado para Bambu Lab A1 Mini - Versão Standalone
"""

from build123d import *
from typing import List, Tuple, Optional, Dict
from .constants import *

class BasePlateGenerator:
    def __init__(self, optimize_for_a1_mini: bool = True):
        self.optimize_for_a1_mini = optimize_for_a1_mini
        self.max_units = A1_MINI_MAX_UNITS if optimize_for_a1_mini else 20

    # --- Lógica de Cálculo ---

    def calculate_grid_from_drawer(self, drawer_x_mm: float, drawer_y_mm: float) -> Tuple[int, int, float, float]:
        """Calcula unidades e a sobra total em cada eixo."""
        units_x = max(1, int(drawer_x_mm // GRID_UNIT))
        units_y = max(1, int(drawer_y_mm // GRID_UNIT))
        
        # Sobra para espaçadores
        sobra_x = drawer_x_mm - (units_x * GRID_UNIT)
        sobra_y = drawer_y_mm - (units_y * GRID_UNIT)
        
        # Margem de segurança
        if sobra_x > 1.0: sobra_x -= 0.5 
        else: sobra_x = 0
        if sobra_y > 1.0: sobra_y -= 0.5
        else: sobra_y = 0

        return units_x, units_y, sobra_x, sobra_y

    def calculate_tiling_strategy(self, total_x: int, total_y: int, spacer_x: float = 0, spacer_y: float = 0) -> List[Tuple[int, int, int, int]]:
        """
        Calcula a estratégia de divisão em tiles.
        
        IMPORTANTE: Considera spacers e conectores para garantir que cada peça caiba na mesa.
        Fórmula do limite: grid + spacer + conector_macho ≤ 180mm
        """
        # Calcula max_units efetivo considerando spacers e conectores
        # Peças de CANTO têm spacer de um lado + conector do outro
        # Pior caso: spacer + grid + conector ≤ 180
        max_spacer = max(spacer_x, spacer_y)
        available_for_grid = A1_MINI_BUILD_VOLUME_X - max_spacer - self.DOVETAIL_DEPTH
        effective_max_units = int(available_for_grid // GRID_UNIT)
        effective_max_units = max(1, min(effective_max_units, self.max_units))
        
        tiles = []
        for x in range(0, total_x, effective_max_units):
            for y in range(0, total_y, effective_max_units):
                chunk_x = min(effective_max_units, total_x - x)
                chunk_y = min(effective_max_units, total_y - y)
                tiles.append((x, y, chunk_x, chunk_y))
        return tiles

    # --- Geometria do Dovetail (Rabo de Andorinha) ---
    
    # Constantes do conector (acessíveis para cálculos)
    DOVETAIL_DEPTH = 2.0  # Profundidade do conector macho (quanto sai da peça)

    def _create_dovetail_solid(self, height: float, tolerance: float = 0.0) -> Part:
        """
        Cria o sólido 3D do rabo de andorinha (trapézio pequeno e discreto).
        O conector é criado apontando para +X, com base em X=0.
        
        IMPORTANTE: O conector ocupa apenas METADE da altura (parte inferior).
        Isso mantém a estrutura mais sólida e facilita a impressão.
        
        Args:
            height: Altura TOTAL da peça (o conector usará metade)
            tolerance: Folga adicional para o corte fêmea (0.0 para macho, 0.20 para fêmea)
        
        Dimensões otimizadas para FDM:
        - Profundidade: 2.0mm (avanço)
        - Largura na ponta: 6.0mm
        - Largura no pescoço: 4.0mm
        - Altura: metade da altura da peça
        """
        # Dimensões do Conector
        depth = 2.0       # Profundidade (avanço)
        width_max = 6.0   # Largura na ponta (maior)
        width_min = 4.0   # Largura no pescoço (menor)
        
        # Aplica tolerância (aumenta o buraco fêmea)
        w_max = width_max + tolerance
        w_min = width_min + tolerance
        d = depth + tolerance  # Fêmea um pouco mais funda também
        
        # MEIA ALTURA - conector só na parte inferior
        connector_height = height / 2
        
        # Desenha o trapézio no plano XY, apontando para +X
        # Para o FÊMEA funcionar, precisamos que a base comece um pouco ANTES da borda
        start_x = -0.5 if tolerance > 0 else 0  # Fêmea começa 0.5mm antes
        
        with BuildPart() as dovetail:
            with BuildSketch(Plane.XY):
                with BuildLine():
                    pts = [
                        (start_x, -w_min/2),           # Base esquerda baixo
                        (start_x, w_min/2),            # Base esquerda cima
                        (start_x + d, w_max/2),        # Ponta cima
                        (start_x + d, -w_max/2),       # Ponta baixo
                        (start_x, -w_min/2)            # Fecha
                    ]
                    Polyline(pts)
                make_face()
            # Extrude apenas MEIA ALTURA (parte inferior, Z=0 até Z=height/2)
            extrude(amount=connector_height)
        
        return dovetail.part

    # --- Geometria do Baseplate ---

    def _create_simple_baseplate(self, size_x: int, size_y: int, tiling_info: Dict, spacers: Dict) -> Part:
        """
        Gera o baseplate com conectores Dovetail nas bordas apropriadas.
        
        IMPORTANTE: Os conectores são gerados POR CÉLULA, não por placa!
        Uma placa 4x4 terá 4 conectores em cada borda de interface.
        
        tiling_info: Diz se tem vizinho na {has_left, has_right, has_top, has_bottom}
        """
        grid_width = size_x * GRID_UNIT
        grid_depth = size_y * GRID_UNIT
        
        # Dimensões totais com espaçadores
        total_width = grid_width + spacers['left'] + spacers['right']
        total_depth = grid_depth + spacers['top'] + spacers['bottom']
        
        # Ajuste do centro geométrico
        center_offset_x = (spacers['right'] - spacers['left']) / 2
        center_offset_y = (spacers['top'] - spacers['bottom']) / 2

        # Altura do conector (mesma altura da base)
        conn_height = BASEPLATE_HEIGHT

        with BuildPart() as base:
            # 1. Base Sólida Principal
            with BuildSketch(Plane.XY):
                with Locations((center_offset_x, center_offset_y)):
                    RectangleRounded(total_width, total_depth, BASEPLATE_CORNER_RADIUS)
            extrude(amount=BASEPLATE_HEIGHT)

            # 2. Recortes Gridfinity (Padrão) + Conectores Dovetail POR CÉLULA
            for ix in range(size_x):
                for iy in range(size_y):
                    # Centro desta célula (relativo ao centro do grid)
                    cx = (ix - (size_x - 1) / 2) * GRID_UNIT
                    cy = (iy - (size_y - 1) / 2) * GRID_UNIT
                    
                    # === Recortes Gridfinity (padrão) ===
                    # Top Lip
                    with BuildSketch(Plane.XY.offset(BASEPLATE_HEIGHT)):
                        with Locations((cx, cy)):
                            RectangleRounded(GRID_UNIT - 0.5, GRID_UNIT - 0.5, BASEPLATE_CORNER_RADIUS - 0.25)
                    extrude(amount=-BASEPLATE_LIP_HEIGHT, mode=Mode.SUBTRACT)

                    # Bottom Square
                    with BuildSketch(Plane.XY.offset(BASEPLATE_HEIGHT - BASEPLATE_LIP_HEIGHT)):
                        with Locations((cx, cy)):
                            RectangleRounded(
                                GRID_UNIT - 0.5 - BASEPLATE_LIP_WIDTH*2, 
                                GRID_UNIT - 0.5 - BASEPLATE_LIP_WIDTH*2, 
                                BASEPLATE_CORNER_RADIUS - 0.5
                            )
                    extrude(amount=-(BASEPLATE_HEIGHT - BASEPLATE_LIP_HEIGHT), mode=Mode.SUBTRACT)

                    # === Conectores Dovetail POR CÉLULA ===
                    # Regra de Polaridade:
                    # - Direita (+X) e Cima (+Y): MACHO (Union)
                    # - Esquerda (-X) e Baixo (-Y): FÊMEA (Subtract com tolerância)
                    
                    # --- BORDA DIREITA: Se esta célula está na última coluna E tem vizinho à direita ---
                    if ix == (size_x - 1) and tiling_info.get('has_right'):
                        male = self._create_dovetail_solid(conn_height, tolerance=0.0)
                        # Posiciona na borda direita do grid, alinhado ao centro Y desta célula
                        male = male.move(Location((grid_width/2, cy, 0)))
                        add(male, mode=Mode.ADD)
                    
                    # --- BORDA ESQUERDA: Se esta célula está na primeira coluna E tem vizinho à esquerda ---
                    if ix == 0 and tiling_info.get('has_left'):
                        female = self._create_dovetail_solid(conn_height, tolerance=0.20)
                        # O sólido aponta para +X. Para cortar na esquerda, precisamos que ele
                        # ENTRE na peça vindo de fora. Posicionamos a BASE do trapézio na borda
                        # e ele avança para DENTRO (+X).
                        # Posição X: -grid_width/2 (borda esquerda, base do trapézio começa aqui)
                        female = female.move(Location((-grid_width/2, cy, 0)))
                        add(female, mode=Mode.SUBTRACT)
                    
                    # --- BORDA SUPERIOR: Se esta célula está na última linha E tem vizinho acima ---
                    if iy == (size_y - 1) and tiling_info.get('has_top'):
                        male = self._create_dovetail_solid(conn_height, tolerance=0.0)
                        # Rotaciona 90° para apontar para +Y
                        male = male.rotate(Axis.Z, 90)
                        # Posiciona na borda superior, alinhado ao centro X desta célula
                        male = male.move(Location((cx, grid_depth/2, 0)))
                        add(male, mode=Mode.ADD)
                    
                    # --- BORDA INFERIOR: Se esta célula está na primeira linha E tem vizinho abaixo ---
                    if iy == 0 and tiling_info.get('has_bottom'):
                        female = self._create_dovetail_solid(conn_height, tolerance=0.20)
                        # Rotaciona 90° para apontar para +Y (entrando na peça de baixo para cima)
                        female = female.rotate(Axis.Z, 90)
                        # Posiciona na borda inferior, alinhado ao centro X desta célula
                        female = female.move(Location((cx, -grid_depth/2, 0)))
                        add(female, mode=Mode.SUBTRACT)

        return base.part

    def _center_part_on_origin(self, part: Part) -> Part:
        """
        Centraliza a peça na origem (0,0) para facilitar alinhamento no slicer.
        O Z fica no chão (z=0).
        """
        bb = part.bounding_box()
        center_x = (bb.min.X + bb.max.X) / 2
        center_y = (bb.min.Y + bb.max.Y) / 2
        min_z = bb.min.Z
        
        return part.move(Location((-center_x, -center_y, -min_z)))

    # --- Fluxo Principal ---

    def generate_from_drawer(
        self, 
        drawer_x_mm: float, 
        drawer_y_mm: float, 
        include_connectors: bool = True,  # Mantido para compatibilidade (agora intrínseco)
        center_on_origin: bool = True
    ) -> Tuple[Compound, int, int, List[Tuple[int, int, int, int]], int]:
        
        # 1. Calcula Grid e Sobras
        units_x, units_y, sobra_x, sobra_y = self.calculate_grid_from_drawer(drawer_x_mm, drawer_y_mm)
        spacer_x = sobra_x / 2
        spacer_y = sobra_y / 2
        
        # 2. Define Tiles (passa spacers para cálculo correto do limite)
        tiles = self.calculate_tiling_strategy(units_x, units_y, spacer_x, spacer_y)
        
        parts_export = []
        spacing = A1_MINI_MAX_UNITS * GRID_UNIT + 20

        # 3. Gera cada Tile
        for idx, (pos_x, pos_y, size_x, size_y) in enumerate(tiles):
            # Informação de Vizinhança (Tiling Info)
            tiling_info = {
                'has_right': (pos_x + size_x) < units_x,
                'has_left': pos_x > 0,
                'has_top': (pos_y + size_y) < units_y,
                'has_bottom': pos_y > 0
            }

            # Spacers (Abas) - Só aplicados nas bordas externas que tocam a gaveta
            my_spacers = {
                'left': spacer_x if not tiling_info['has_left'] else 0,
                'right': spacer_x if not tiling_info['has_right'] else 0,
                'bottom': spacer_y if not tiling_info['has_bottom'] else 0,
                'top': spacer_y if not tiling_info['has_top'] else 0
            }

            # Gera a peça
            part = self._create_simple_baseplate(size_x, size_y, tiling_info, my_spacers)
            
            # Centraliza na origem se solicitado
            if center_on_origin:
                part = self._center_part_on_origin(part)
            
            # Posiciona para exportação (visualização explodida no slicer)
            if len(tiles) > 1:
                loc_x = (idx % 3) * spacing
                loc_y = (idx // 3) * spacing
                part_copy = Part(part.wrapped).move(Location((loc_x, loc_y, 0)))
            else:
                part_copy = Part(part.wrapped)
            
            parts_export.append(part_copy)

        # Retorna Compound (0 conectores avulsos, pois agora são integrados)
        return Compound(children=parts_export), units_x, units_y, tiles, 0

    def get_generation_summary(self, ux, uy, tiles, n_conn):
        return f"Grid {ux}x{uy} ({len(tiles)} partes com encaixe Dovetail)"

    def get_tiling_description(self, tiles):
        if len(tiles) == 1: 
            return "Peça única."
        return f"Dividido em {len(tiles)} partes intertravadas."

    def needs_tiling(self, ux, uy):
        return ux > self.max_units or uy > self.max_units