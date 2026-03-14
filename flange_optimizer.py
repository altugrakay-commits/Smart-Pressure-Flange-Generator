# -------------------------------------------------------------------
# Copyright (c) 2026 altugrakay-commits. All rights reserved.
# This software is part of the Smart Pressure Flange Project.
# -------------------------------------------------------------------
import os

# Your optimized parameters (calculated from your Jupyter logic)
optimized_bore = 50.0  
optimized_thickness = 5.0

# PORTABLE PATH: Saves to the same folder as this script
base_path = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(base_path, "optimum_design.txt")

with open(output_file, "w") as f:
    f.write(f"Bore:{optimized_bore}\n")
    f.write(f"Thickness:{optimized_thickness}")

print(f"Data saved to {output_file}")