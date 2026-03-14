# -------------------------------------------------------------------
# Copyright (c) 2026 altugrakay-commits. All rights reserved.
# -------------------------------------------------------------------
import os

# PRIVACY: Use relative paths for local file lookup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# In a real pipeline, this value is parsed from the generator's output
# Here we use an example volume based on your successful render
FLANGE_VOLUME_MM3 = 145230.45 

# Material Database: Density (g/cm3) and Market Cost (USD/kg)
MATERIALS = {
    "316 Stainless Steel": {"density": 8.0, "cost_per_kg": 4.50},
    "6061-T6 Aluminum": {"density": 2.7, "cost_per_kg": 2.85}
}

def run_cost_analysis():
    print("--- Smart Pressure Flange: Cost Estimation ---")
    print(f"Calculated Volume: {FLANGE_VOLUME_MM3:.2f} mm3\n")
    
    for mat, props in MATERIALS.items():
        # Convert mm3 to cm3, then to kg using density
        mass_kg = (FLANGE_VOLUME_MM3 / 1000 * props["density"]) / 1000
        total_cost = mass_kg * props["cost_per_kg"]
        
        print(f"Material: {mat}")
        print(f" - Calculated Mass: {mass_kg:.3f} kg")
        print(f" - Estimated Raw Material Cost: ${total_cost:.2f}\n")

if __name__ == "__main__":
    run_cost_analysis()
