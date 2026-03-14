# -------------------------------------------------------------------
# Copyright (c) 2026 altugrakay-commits. All rights reserved.
# -------------------------------------------------------------------
import Part, math, os
import FreeCAD as App

# Setup dynamic paths for GitHub portability
BASE_DIR = os.getcwd() 
INPUT_PATH = os.path.join(BASE_DIR, "optimum_design.txt")
EXPORT_PATH = os.path.join(BASE_DIR, "Smart_Pressure_Flange.step")

def run_generation():
    try:
        # 1. Load data from the optimizer
        with open(INPUT_PATH, 'r') as f:
            lines = f.readlines()
            bore = float(lines[0].split(':')[1])
            thick = float(lines[1].split(':')[1])

        # 2. Define geometry variables
        inner_r = bore / 2
        outer_r = inner_r + thick
        plate_r = outer_r + 25   # Outer disk radius
        plate_h = 12             # Disk thickness
        hub_h = 35               # Vertical neck height

        # 3. Build the Base Solids
        # Create a hollow cylinder for the neck (hub)
        hub = Part.makeCylinder(outer_r, hub_h).cut(Part.makeCylinder(inner_r, hub_h))
        # Create a hollow cylinder for the base plate
        plate = Part.makeCylinder(plate_r, plate_h).cut(Part.makeCylinder(inner_r, plate_h))
        # Boolean Union: Combine both into one single solid body
        flange = plate.fuse(hub)

        # 4. Structural Refinement (Fillets & Chamfers)
        # Find the circular edge where hub meets plate for a 5mm fillet (Stress reduction)
        f_edges = [e for e in flange.Edges if hasattr(e.Curve, 'Radius') 
                   and abs(e.BoundBox.Center.z - plate_h) < 0.01 
                   and abs(e.Curve.Radius - outer_r) < 0.01]
        if f_edges: flange = flange.makeFillet(5.0, f_edges)

        # Find top edges of the hub for a 1.5mm chamfer (Assembly ease)
        c_edges = [e for e in flange.Edges if hasattr(e.Curve, 'Radius') 
                   and abs(e.BoundBox.Center.z - hub_h) < 0.01]
        if c_edges: flange = flange.makeChamfer(1.5, c_edges)

        # 5. Bolt Hole Pattern
        # Pattern of 4 holes placed 15mm outside the hub
        bolt_circle_r = outer_r + 15
        for i in range(4):
            angle = math.radians(i * 90)
            hole = Part.makeCylinder(4.5, plate_h) # M9 size
            hole.translate(App.Vector(bolt_circle_r * math.cos(angle), bolt_circle_r * math.sin(angle), 0))
            flange = flange.cut(hole) # Boolean Subtraction

        # 6. Final Outputs
        flange.exportStep(EXPORT_PATH) # Save for manufacturing
        Part.show(flange) # Show in FreeCAD viewer
        print(f"CAD Generated. Volume: {flange.Volume:.2f} mm3")

    except Exception as e:
        print(f"Error in CAD pipeline: {e}")

if __name__ == "__main__":
    run_generation()
