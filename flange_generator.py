# -------------------------------------------------------------------
# Copyright (c) 2026 altugrakay-commits. All rights reserved.
# Licensed under MIT License.
# -------------------------------------------------------------------
import Part, math, os
import FreeCAD as App

# DYNAMIC PATHS: No local user directories exposed
BASE_DIR = os.getcwd() 
INPUT_PATH = os.path.join(BASE_DIR, "optimum_design.txt")
EXPORT_PATH = os.path.join(BASE_DIR, "Smart_Pressure_Flange.step")

def run_generation():
    try:
        if not os.path.exists(INPUT_PATH):
            print("Error: optimum_design.txt not found in current folder.")
            return

        with open(INPUT_PATH, 'r') as f:
            lines = f.readlines()
            bore = float(lines[0].split(':')[1])
            thick = float(lines[1].split(':')[1])

        # Geometry Setup
        inner_r, outer_r = bore/2, (bore/2) + thick
        plate_r, plate_h, hub_h = outer_r + 25, 12, 35
        fillet_r, chamfer_s = 5.0, 1.5

        # Modeling logic
        hub = Part.makeCylinder(outer_r, hub_h).cut(Part.makeCylinder(inner_r, hub_h))
        plate = Part.makeCylinder(plate_r, plate_h).cut(Part.makeCylinder(inner_r, plate_h))
        flange = plate.fuse(hub)

        # Refinements
        f_edges = [e for e in flange.Edges if hasattr(e.Curve, 'Radius') 
                   and abs(e.BoundBox.Center.z - plate_h) < 0.01 
                   and abs(e.Curve.Radius - outer_r) < 0.01]
        if f_edges: flange = flange.makeFillet(fillet_r, f_edges)

        c_edges = [e for e in flange.Edges if hasattr(e.Curve, 'Radius') 
                   and abs(e.BoundBox.Center.z - hub_h) < 0.01]
        if c_edges: flange = flange.makeChamfer(chamfer_s, c_edges)

        # Pattern of 4 bolt holes
        bc, hr = outer_r + 15, 4.5
        for i in range(4):
            angle = math.radians(i * 90)
            hole = Part.makeCylinder(hr, plate_h)
            hole.translate(App.Vector(bc * math.cos(angle), bc * math.sin(angle), 0))
            flange = flange.cut(hole)

        # Final Export & Display
        flange.exportStep(EXPORT_PATH)
        Part.show(flange)
        
        volume = flange.Volume
        print(f"Success! STEP exported. Total Volume: {volume:.2f} mm^3")

    except Exception as e:
        print(f"CAD Generation failed: {e}")

if __name__ == "__main__":
    run_generation()