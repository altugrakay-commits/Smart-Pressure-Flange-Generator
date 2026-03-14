# -------------------------------------------------------------------
# Copyright (c) 2026 altugrakay-commits. All rights reserved.
# Project: Smart Pressure Flange Generative Design
# -------------------------------------------------------------------
import Part, math, os
import FreeCAD as App

# PRIVACY FIX: Get the directory where THIS script is saved to avoid hardcoded paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "optimum_design.txt")
OUTPUT_FILE = os.path.join(BASE_DIR, "Smart_Flange_Export.step")

def generate_flange():
    try:
        # --- 1. DATA EXCHANGE ---
        # Reads dimensions calculated by the optimizer (flange_optimizer.py)
        if not os.path.exists(INPUT_FILE):
            print(f"Error: {INPUT_FILE} not found. Run optimization first.")
            return

        with open(INPUT_FILE, 'r') as f:
            lines = f.readlines()
            bore = float(lines[0].split(':')[1]) # Internal diameter
            thick = float(lines[1].split(':')[1]) # Wall thickness

        # --- 2. DIMENSION DEFINITIONS ---
        # Derived values based on optimized bore and thickness
        inner_r, outer_r = bore/2, (bore/2) + thick
        plate_r = outer_r + 25   # Outer radius of the base plate
        plate_h = 12             # Thickness of the base plate
        hub_h = 35               # Total height of the hub (neck)
        fillet_r = 5.0           # Structural fillet radius
        chamfer_s = 1.5          # Assembly chamfer size

        # --- 3. PRIMARY GEOMETRY CONSTRUCTION ---
        # Create the vertical hub neck
        hub = Part.makeCylinder(outer_r, hub_h).cut(Part.makeCylinder(inner_r, hub_h))
        # Create the horizontal base plate
        plate = Part.makeCylinder(plate_r, plate_h).cut(Part.makeCylinder(inner_r, plate_h))
        # Fuse components into a single manifold solid
        flange = plate.fuse(hub)

        # --- 4. TOPOLOGICAL REFINEMENT ---
        # Apply 5mm Fillet at the junction (Z = plate_h) to reduce stress concentration
        f_edges = [e for e in flange.Edges if hasattr(e.Curve, 'Radius') 
                   and abs(e.BoundBox.Center.z - plate_h) < 0.01 
                   and abs(e.Curve.Radius - outer_r) < 0.01]
        if f_edges: flange = flange.makeFillet(fillet_r, f_edges)

        # Apply 1.5mm Chamfer at the top (Z = hub_h) for assembly ease
        c_edges = [e for e in flange.Edges if hasattr(e.Curve, 'Radius') 
                   and abs(e.BoundBox.Center.z - hub_h) < 0.01]
        if c_edges: flange = flange.makeChamfer(chamfer_s, c_edges)

        # --- 5. MECHANICAL FEATURES ---
        # Add 4-bolt pattern for standard flange mounting
        bc_radius, hole_r = outer_r + 15, 4.5
        for i in range(4):
            angle = math.radians(i * 90)
            hole = Part.makeCylinder(hole_r, plate_h)
            hole.translate(App.Vector(bc_radius * math.cos(angle), bc_radius * math.sin(angle), 0))
            flange = flange.cut(hole)

        # --- 6. OUTPUTS & DATA ANALYSIS ---
        # Export as STEP for manufacturing and show in viewer
        flange.exportStep(OUTPUT_FILE)
        Part.show(flange)
        
        # Calculate final volume for mass/cost estimation
        print(f"Final Volume: {flange.Volume:.2f} mm3")
        print(f"Successfully exported to: {OUTPUT_FILE}")

    except Exception as e:
        print(f"CAD Generation Error: {e}")

if __name__ == "__main__":
    generate_flange()
