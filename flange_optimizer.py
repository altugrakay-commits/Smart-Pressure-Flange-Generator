# -------------------------------------------------------------------
# Copyright (c) 2026 altugrakay-commits. All rights reserved.
# -------------------------------------------------------------------
import os

# --- ENGINEERING LOGIC ---
# In a real scenario, these values would be derived from Hoop Stress 
# formulas: Thickness = (Pressure * Radius) / (Allowable Stress)
optimized_bore = 50.0  # Internal diameter (mm)
optimized_thickness = 5.0 # Wall thickness based on safety factor (mm)

# --- PORTABLE FILE HANDLING ---
# Get current folder path to avoid exposing local PC directories
base_path = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(base_path, "optimum_design.txt")

# Save parameters to a handshake file for the CAD script to read
with open(output_file, "w") as f:
    f.write(f"Bore:{optimized_bore}\n")
    f.write(f"Thickness:{optimized_thickness}")

print(f"Optimization complete. Parameters sent to: {output_file}")
