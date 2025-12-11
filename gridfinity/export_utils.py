"""
Utilitários para exportação de arquivos STL e ZIP
"""

import io
import zipfile
import tempfile
import os
from typing import List, Tuple, Optional
from build123d import Compound, Part, export_stl


def export_to_stl_bytes(shape: Compound | Part, tolerance: float = 0.001) -> bytes:
    """
    Exporta um shape para bytes STL.
    
    Args:
        shape: Objeto Compound ou Part do build123d
        tolerance: Tolerância para tessellation
        
    Returns:
        Bytes do arquivo STL
    """
    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        export_stl(shape, tmp_path, tolerance=tolerance)
        with open(tmp_path, 'rb') as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def create_download_zip(
    baseplate: Optional[Compound | Part] = None,
    bins: Optional[List[Tuple[str, Part]]] = None,
    baseplate_filename: str = "baseplate_full_set_a1mini.stl"
) -> bytes:
    """
    Cria arquivo ZIP contendo baseplate e bins.
    
    Args:
        baseplate: Compound com todas as peças do baseplate
        bins: Lista de tuplas (nome_arquivo, Part) para os bins
        baseplate_filename: Nome do arquivo do baseplate no ZIP
        
    Returns:
        Bytes do arquivo ZIP
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Adiciona baseplate
        if baseplate is not None:
            stl_bytes = export_to_stl_bytes(baseplate)
            zf.writestr(baseplate_filename, stl_bytes)
        
        # Adiciona bins
        if bins:
            for filename, bin_part in bins:
                stl_bytes = export_to_stl_bytes(bin_part)
                zf.writestr(filename, stl_bytes)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def get_file_size_str(size_bytes: int) -> str:
    """Converte bytes para string legível."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
