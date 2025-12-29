from build123d import *

# Define dimensions (Gridfinity standard-ish)
width = 42.0
depth = 42.0
height = 30.0
radius = 4.0
wall_thickness = 2.0
bottom_thickness = 2.0

inner_width = width - 2 * wall_thickness
inner_depth = depth - 2 * wall_thickness
# Ensure inner radius is valid
inner_radius = max(0.1, radius - wall_thickness)
inner_height = height - bottom_thickness

print(f"Creating bin with dimensions:")
print(f"  Outer: {width}x{depth}x{height}, r={radius}")
print(f"  Inner: {inner_width}x{inner_depth}x{inner_height}, r={inner_radius}")
print(f"  Bottom thickness: {bottom_thickness}")

# USER'S CODE
with BuildPart() as bin:
    # Step 1: 2D Profile Drawing (Sketch)
    with BuildSketch():
        RectangleRounded(width, depth, radius)
    # Step 2: Extrusion to 3D
    extrude(amount=height)
    
    # Step 3: Boolean Cut Operation (Subtract) with topological selection
    with BuildSketch(Plane.XY.offset(bottom_thickness)):
        RectangleRounded(inner_width, inner_depth, inner_radius)
    extrude(amount=inner_height, mode=Mode.SUBTRACT)

# Export to verify
if bin.part.is_valid():
    print("Bin created successfully and is valid.")
    export_stl(bin.part, "test_simple_bin.stl")
    print("Exported to test_simple_bin.stl")
else:
    print("Error: Generated part is invalid.")
