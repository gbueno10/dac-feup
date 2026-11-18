include <gridfinity_modules.scad>

// Parameters
width = 4;
depth = 4;
plate_height = 4.5; // Slightly deeper to ensure good fit? 5mm is standard unit, but baseplates vary.

// Connector / Splitting parameters
side_conn_top = false;
side_conn_right = false;
side_conn_bottom = false;
side_conn_left = false;

module butterfly_cutout() {
    // A simple butterfly/bowtie shape for the joiner
    // 5mm deep into the plate
    // Shape: two triangles or trapezoids
    
    neck_w = 4;
    head_w = 8;
    length = 5;
    total_l = length * 2; // 10mm total length of key (5mm per side)
    
    linear_extrude(plate_height + 1)
    polygon([
        [0, -neck_w/2],
        [length, -head_w/2],
        [length, head_w/2],
        [0, neck_w/2],
        [-length, head_w/2],
        [-length, -head_w/2]
    ]);
}

module butterfly_clip() {
    neck_w = 3.8; // Tolerance 0.2
    head_w = 7.8;
    length = 5; // Length from center to side
    
    // Make it slightly shorter in height to not flush perfectly (easier to install)
    clip_h = plate_height - 0.5;
    
    linear_extrude(clip_h)
    polygon([
        [0, -neck_w/2],
        [length - 0.2, -head_w/2],
        [length - 0.2, head_w/2],
        [0, neck_w/2],
        [-(length - 0.2), head_w/2],
        [-(length - 0.2), -head_w/2]
    ]);
}

module baseplate(num_x, num_y, conn_top=false, conn_right=false, conn_bottom=false, conn_left=false) {
    gridfinity_pitch = 42;
    total_width = num_x * gridfinity_pitch;
    total_depth = num_y * gridfinity_pitch;
    
    // We want a frame-style baseplate, or a solid block with cutouts.
    // Solid block is easier to print if weighted not needed.
    
    difference() {
        translate([0,0,0])
        cube([total_width, total_depth, plate_height]);
        
        // Remove material for the feet of bins to fit in.
        // The top of the baseplate acts like the top of a bin.
        // We use pad_oversize(1,1,1) to get the profile with clearance.
        
        gridcopy(num_x, num_y) 
        translate([0, 0, plate_height - 5]) // 5mm is typical nesting depth?
        // pad_oversize is ~5mm tall.
        // If plate_height is 4.5, and we translate to -0.5, we cut through.
        // Let's align top of pad with top of plate.
        // pad_oversize height is ~5mm.
        // If we want it flush with top, we need it at Z = plate_height - pad_height?
        // Actually grid_block subtracts it at `gridfinity_zpitch*num_z`.
        // So aligns the BOTTOM of the pad (Z=0) with Z=height.
        // Wait, grid_block subtracts pad_oversize shifted UP?
        // Let's re-read grid_block.
        // translate([0, 0, gridfinity_zpitch*num_z]) pad_oversize(...).
        // It subtracts the pad WHICH STARTS AT Z=0.
        // So it subtracts a shape that exists from Z=height upwards.
        // This effectively trims the top of the block?
        // NO. Difference { block; pad }.
        // If pad is ABOVE the block, difference does nothing.
        // Unless pad_oversize GOES DOWN?
        // line 149: translate([0, 0, -axialdown]).
        // It builds UP.
        // So grid_block:
        // difference {
        //   ... cube(..., totalht) ...
        //   translate([..., num_z * 7]) pad_oversize(...)
        // }
        // num_z * 7 is the height of the LIP.
        // totalht = num_z * 7 + 3.75.
        // So the block is taller than the grid unit.
        // And we subtract the pad starting at num_z*7.
        // So we are sculpting the LIP.
        
        // But for a BASEPLATE, we want HOLES for feet.
        // A bin has FEET at the BOTTOM.
        // A baseplate receives the FEET.
        // So the baseplate profile should be the INVERSE of the FEET.
        // The FEET are defined by what is LEFT after grid_block logic?
        // No, grid_block defines the bin.
        // The bin fits ON TOP of another bin.
        // So the TOP of a bin (which grid_block shapes) accepts the BOTTOM of a bin.
        // So the BASEPLATE should look like the TOP of a bin.
        // Which is exactly what grid_block logic does: it creates the lip.
        
        // So a Baseplate is just a very short Gridfinity Bin (height=0?), but only the top part.
        // We want the TOP profile.
        // So we can arguably use grid_block with height=0? No.
        
        // Let's construct it manually.
        // Take a block of plate_height.
        // Sculpt the top to look like the top of a bin.
        // The top of a bin is created by taking a block and subtracting `pad_oversize` at `gridfinity_pitch`?
        // No, the LIP is the material remaining AROUND the `pad_oversize` shape.
        // So `pad_oversize` is the NEGATIVE space (the spot where the foot goes).
        // Correct! The bin ABOVE has a foot that fits into the hole.
        
        // So, we want to subtract `pad_oversize` from our base block.
        // We want the top of `pad_oversize` to align with top of base block?
        // Or roughly.
        // The standard "lip" is ~4-5mm high.
        // If we make plate_height=4.5mm.
        // We want the pattern to be cut into it.
        // We should translate `pad_oversize` so it sits at the right height.
        // In grid_block, it is at height 7 * num_z (which is the top of the main body, below the lip).
        // So the pad starts at "floor" level and goes up.
        // Wait, pad_oversize IS the shape of the foot.
        // So we want to subtract the foot from our block.
        // The foot goes INTO the baseplate.
        // So we should position the foot at Z = plate_height - foot_penetration?
        // Or rather, the foot sits ON the desk? No, the foot goes INTO the baseplate.
        // The baseplate sits on the desk.
        // So the foot cannot go deeper than Z=0.
        // If plate_height is 4.5mm.
        // The foot is ~5mm?
        // Then it would poke through. That's fine for a frame.
        
        // Let's try aligning it such that the "shelf" of the foot matches.
        // `pad_oversize` has `bevel2_bottom = 2.6`, `bevel2_top = 5`.
        // The "shelf" is probably at bevel2_bottom?
        // Let's just assume we want to subtract it starting from some Z.
        // If we want the top of the baseplate to be flush with the "lip" of a bin.
        
        // Let's just try putting it at Z = plate_height - 5.
        // And see if it looks right. 
        // 5 is roughly the height of pad_oversize (bevel2_top=5).
        // So if we translate to plate_height - 5, the top of pad (at Z=5) will be at plate_height.
        // This implies the cut goes all the way to the top surface.
        // This is correct: the hole is open at the top.
        
        translate([0, 0, plate_height - 5]) 
        pad_oversize(1, 1, 1);
        
        // Connector Slots
        // We place one connector every unit, or maybe just some?
        // Let's place one per unit center to be safe and modular.
        
        // Top Edge (Y = max)
        if (conn_top) {
             for (xi=[1:num_x]) 
                 translate([gridfinity_pitch*(xi-0.5), total_depth, 0]) 
                 butterfly_cutout();
        }
        
        // Bottom Edge (Y = 0)
        if (conn_bottom) {
             for (xi=[1:num_x]) 
                 translate([gridfinity_pitch*(xi-0.5), 0, 0]) 
                 butterfly_cutout();
        }
        
        // Right Edge (X = max)
        if (conn_right) {
             for (yi=[1:num_y]) 
                 translate([total_width, gridfinity_pitch*(yi-0.5), 0]) 
                 rotate([0,0,90])
                 butterfly_cutout();
        }
        
        // Left Edge (X = 0)
        if (conn_left) {
             for (yi=[1:num_y]) 
                 translate([0, gridfinity_pitch*(yi-0.5), 0]) 
                 rotate([0,0,90])
                 butterfly_cutout();
        }
    }
}

// If this file is run directly with render_key=true, make the clip
render_key = false;

if (render_key) {
    butterfly_clip();
} else {
    baseplate(width, depth, side_conn_top, side_conn_right, side_conn_bottom, side_conn_left);
}
