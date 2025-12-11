"""
Testes unitários para o módulo Gridfinity Generator
"""

import pytest
from gridfinity.constants import (
    GRID_UNIT, A1_MINI_MAX_UNITS, GRID_HEIGHT_UNIT
)


class TestConstants:
    """Testes para as constantes do Gridfinity."""
    
    def test_grid_unit_value(self):
        """Verifica se a unidade de grid está correta."""
        assert GRID_UNIT == 42.0
    
    def test_a1_mini_max_units(self):
        """Verifica limite da A1 Mini."""
        assert A1_MINI_MAX_UNITS == 4
        # 4 unidades * 42mm = 168mm < 180mm (volume A1 Mini)
        assert A1_MINI_MAX_UNITS * GRID_UNIT < 180
    
    def test_grid_height_unit(self):
        """Verifica altura da unidade."""
        assert GRID_HEIGHT_UNIT == 7.0
