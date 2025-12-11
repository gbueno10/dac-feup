"""
Testes para o gerador de baseplates.
"""

import pytest
from gridfinity.baseplate import BasePlateGenerator
from gridfinity.constants import GRID_UNIT, A1_MINI_MAX_UNITS


class TestBasePlateGenerator:
    """Testes para BasePlateGenerator."""
    
    def test_calculate_grid_from_drawer(self):
        """Testa cálculo de grid a partir da gaveta."""
        gen = BasePlateGenerator(optimize_for_a1_mini=True)
        
        # 300mm / 42mm = 7.14 -> 7 unidades
        units_x, units_y = gen.calculate_grid_from_drawer(300, 200)
        assert units_x == 7
        assert units_y == 4
    
    def test_calculate_grid_minimum(self):
        """Testa que sempre retorna pelo menos 1 unidade."""
        gen = BasePlateGenerator()
        units_x, units_y = gen.calculate_grid_from_drawer(30, 30)
        assert units_x >= 1
        assert units_y >= 1
    
    def test_tiling_strategy_no_split(self):
        """Testa estratégia sem divisão (3x3)."""
        gen = BasePlateGenerator(optimize_for_a1_mini=True)
        tiles = gen.calculate_tiling_strategy(3, 3)
        
        assert len(tiles) == 1
        assert tiles[0] == (0, 0, 3, 3)
    
    def test_tiling_strategy_with_split(self):
        """Testa estratégia com divisão (6x6)."""
        gen = BasePlateGenerator(optimize_for_a1_mini=True)
        tiles = gen.calculate_tiling_strategy(6, 6)
        
        # 6x6 deve gerar 4 peças: 4x4, 2x4, 4x2, 2x2
        assert len(tiles) == 4
        
        # Verifica as peças esperadas
        expected_sizes = {(4, 4), (2, 4), (4, 2), (2, 2)}
        actual_sizes = {(t[2], t[3]) for t in tiles}
        assert actual_sizes == expected_sizes
    
    def test_tiling_strategy_7x4(self):
        """Testa estratégia 7x4 (exemplo do PRD)."""
        gen = BasePlateGenerator(optimize_for_a1_mini=True)
        tiles = gen.calculate_tiling_strategy(7, 4)
        
        # 7x4 deve gerar 2 peças: 4x4 e 3x4
        assert len(tiles) == 2
        
        sizes = [(t[2], t[3]) for t in tiles]
        assert (4, 4) in sizes
        assert (3, 4) in sizes
    
    def test_needs_tiling_false(self):
        """Testa que 4x4 não precisa divisão."""
        gen = BasePlateGenerator(optimize_for_a1_mini=True)
        assert not gen.needs_tiling(4, 4)
        assert not gen.needs_tiling(3, 3)
        assert not gen.needs_tiling(1, 1)
    
    def test_needs_tiling_true(self):
        """Testa que grids maiores precisam divisão."""
        gen = BasePlateGenerator(optimize_for_a1_mini=True)
        assert gen.needs_tiling(5, 4)
        assert gen.needs_tiling(4, 5)
        assert gen.needs_tiling(6, 6)
    
    def test_no_optimization_mode(self):
        """Testa modo sem otimização."""
        gen = BasePlateGenerator(optimize_for_a1_mini=False)
        
        # Mesmo grids grandes não devem ser divididos
        tiles = gen.calculate_tiling_strategy(10, 10)
        assert len(tiles) == 1
        assert tiles[0] == (0, 0, 10, 10)
    
    def test_tiling_description_single(self):
        """Testa descrição para peça única."""
        gen = BasePlateGenerator(optimize_for_a1_mini=True)
        tiles = gen.calculate_tiling_strategy(3, 3)
        desc = gen.get_tiling_description(tiles)
        
        assert "peça única" in desc.lower() or "sem divisão" in desc.lower()
    
    def test_tiling_description_multiple(self):
        """Testa descrição para múltiplas peças."""
        gen = BasePlateGenerator(optimize_for_a1_mini=True)
        tiles = gen.calculate_tiling_strategy(6, 6)
        desc = gen.get_tiling_description(tiles)
        
        assert "4" in desc  # Deve mencionar 4 partes
        assert "4x4" in desc  # Deve mencionar tamanhos
