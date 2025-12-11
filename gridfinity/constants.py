"""
Constantes do padrão Gridfinity
"""

# Dimensões base do Gridfinity
GRID_UNIT = 42.0  # mm - tamanho de uma unidade
GRID_HEIGHT_UNIT = 7.0  # mm - altura de uma unidade

# Dimensões do baseplate
BASEPLATE_HEIGHT = 4.65  # mm
BASEPLATE_LIP_HEIGHT = 2.15  # mm
BASEPLATE_LIP_WIDTH = 0.8  # mm
BASEPLATE_CORNER_RADIUS = 3.75  # mm
BASEPLATE_MAGNET_HOLE_DIAMETER = 6.5  # mm
BASEPLATE_MAGNET_HOLE_DEPTH = 2.4  # mm
BASEPLATE_SCREW_HOLE_DIAMETER = 3.0  # mm

# Dimensões do bin
BIN_WALL_THICKNESS = 1.2  # mm
BIN_BOTTOM_THICKNESS = 0.8  # mm
BIN_CORNER_RADIUS = 3.75  # mm
BIN_LIP_HEIGHT = 4.4  # mm
BIN_LIP_WIDTH = 2.6  # mm

# Limites da Bambu Lab A1 Mini
A1_MINI_BUILD_VOLUME_X = 180  # mm
A1_MINI_BUILD_VOLUME_Y = 180  # mm
A1_MINI_BUILD_VOLUME_Z = 180  # mm
A1_MINI_MAX_UNITS = 4  # máximo de unidades por eixo (4 * 42 = 168mm < 180mm)

# Espaçamento para exportação lado a lado
EXPORT_SPACING = 45.0  # mm (42mm + 3mm de folga visual)
