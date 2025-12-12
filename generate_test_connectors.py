"""
Gera peças de teste para validar o encaixe Dovetail (Rabo de Andorinha).
Cria dois mini baseplates 1x1 com conectores macho e fêmea.
"""

from build123d import *

# Constantes do Gridfinity
GRID_UNIT = 42.0
BASEPLATE_HEIGHT = 4.65
BASEPLATE_CORNER_RADIUS = 3.75

# Constantes do Dovetail
DOVETAIL_DEPTH = 2.0
DOVETAIL_WIDTH_MAX = 6.0
DOVETAIL_WIDTH_MIN = 4.0
DOVETAIL_TOLERANCE = 0.20


def create_dovetail_solid(height: float, tolerance: float = 0.0):
    """Cria o sólido do conector dovetail."""
    depth = DOVETAIL_DEPTH
    width_max = DOVETAIL_WIDTH_MAX
    width_min = DOVETAIL_WIDTH_MIN
    
    w_max = width_max + tolerance
    w_min = width_min + tolerance
    d = depth + tolerance
    
    connector_height = height / 2  # Meia altura
    start_x = -0.5 if tolerance > 0 else 0
    
    with BuildPart() as dovetail:
        with BuildSketch(Plane.XY):
            with BuildLine():
                pts = [
                    (start_x, -w_min/2),
                    (start_x, w_min/2),
                    (start_x + d, w_max/2),
                    (start_x + d, -w_max/2),
                    (start_x, -w_min/2)
                ]
                Polyline(pts)
            make_face()
        extrude(amount=connector_height)
    
    return dovetail.part


def create_test_piece_male():
    """Cria peça de teste 1x1 com conector MACHO na direita."""
    grid_size = GRID_UNIT
    
    with BuildPart() as piece:
        # Base 1x1
        with BuildSketch(Plane.XY):
            RectangleRounded(grid_size, grid_size, BASEPLATE_CORNER_RADIUS)
        extrude(amount=BASEPLATE_HEIGHT)
        
        # Conector macho na borda direita
        male = create_dovetail_solid(BASEPLATE_HEIGHT, tolerance=0.0)
        male = male.move(Location((grid_size/2, 0, 0)))
        add(male, mode=Mode.ADD)
    
    return piece.part


def create_test_piece_female():
    """Cria peça de teste 1x1 com conector FÊMEA na esquerda."""
    grid_size = GRID_UNIT
    
    with BuildPart() as piece:
        # Base 1x1
        with BuildSketch(Plane.XY):
            RectangleRounded(grid_size, grid_size, BASEPLATE_CORNER_RADIUS)
        extrude(amount=BASEPLATE_HEIGHT)
        
        # Conector fêmea na borda esquerda
        female = create_dovetail_solid(BASEPLATE_HEIGHT, tolerance=DOVETAIL_TOLERANCE)
        female = female.move(Location((-grid_size/2, 0, 0)))
        add(female, mode=Mode.SUBTRACT)
    
    return piece.part


if __name__ == "__main__":
    print("Gerando peças de teste do encaixe Dovetail...")
    print(f"  Tolerância fêmea: {DOVETAIL_TOLERANCE}mm")
    print(f"  Profundidade: {DOVETAIL_DEPTH}mm")
    print(f"  Largura: {DOVETAIL_WIDTH_MIN}mm → {DOVETAIL_WIDTH_MAX}mm")
    print()
    
    # Gera as peças
    male_piece = create_test_piece_male()
    female_piece = create_test_piece_female()
    
    # Exporta STLs usando export_stl do build123d
    from build123d import export_stl
    
    export_stl(male_piece, "test_connector_MALE.stl")
    print("✅ Exportado: test_connector_MALE.stl")
    
    export_stl(female_piece, "test_connector_FEMALE.stl")
    print("✅ Exportado: test_connector_FEMALE.stl")
    
    print()
    print("📐 Dimensões de cada peça:")
    print(f"   Base: {GRID_UNIT}x{GRID_UNIT}mm")
    print(f"   Altura: {BASEPLATE_HEIGHT}mm")
    print(f"   Conector: meia altura ({BASEPLATE_HEIGHT/2:.2f}mm)")
    print()
    print("🔧 Para testar:")
    print("   1. Imprima ambos os STLs")
    print("   2. Encaixe o MACHO no FÊMEA deslizando lateralmente")
    print("   3. Se muito apertado: aumente DOVETAIL_TOLERANCE")
    print("   4. Se muito solto: diminua DOVETAIL_TOLERANCE")
