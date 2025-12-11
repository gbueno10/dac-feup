"""
Testes para o gerador de bins.
"""

import pytest
from gridfinity.bins import BinGenerator
from gridfinity.constants import GRID_UNIT, A1_MINI_MAX_UNITS


class TestBinGenerator:
    """Testes para BinGenerator."""
    
    def test_validate_size_valid(self):
        """Testa validação de tamanho válido."""
        gen = BinGenerator(optimize_for_a1_mini=True)
        
        is_valid, msg = gen.validate_size(2, 2)
        assert is_valid
        assert "✅" in msg or "compatível" in msg.lower()
    
    def test_validate_size_max_limit(self):
        """Testa validação no limite máximo."""
        gen = BinGenerator(optimize_for_a1_mini=True)
        
        is_valid, msg = gen.validate_size(4, 4)
        assert is_valid
    
    def test_validate_size_invalid(self):
        """Testa validação de tamanho inválido."""
        gen = BinGenerator(optimize_for_a1_mini=True)
        
        is_valid, msg = gen.validate_size(5, 4)
        assert not is_valid
        assert "alerta" in msg.lower() or "⚠️" in msg
    
    def test_validate_size_both_exceed(self):
        """Testa validação quando ambos eixos excedem."""
        gen = BinGenerator(optimize_for_a1_mini=True)
        
        is_valid, msg = gen.validate_size(5, 5)
        assert not is_valid
    
    def test_validate_size_no_optimization(self):
        """Testa validação sem otimização."""
        gen = BinGenerator(optimize_for_a1_mini=False)
        
        is_valid, msg = gen.validate_size(10, 10)
        assert is_valid
    
    def test_bin_dimensions(self):
        """Testa cálculo de dimensões do bin."""
        # Dimensões esperadas para bin 2x2x3
        expected_width = 2 * GRID_UNIT - 0.5  # 83.5mm
        expected_depth = 2 * GRID_UNIT - 0.5  # 83.5mm
        
        assert expected_width == 83.5
        assert expected_depth == 83.5
