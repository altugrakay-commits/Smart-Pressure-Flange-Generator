# -------------------------------------------------------------------
# Copyright (c) 2026 altugrakay-commits. All rights reserved.
# -------------------------------------------------------------------
import os

# --- 1. DATA INPUT ---
# In a fully integrated pipeline, this volume is fetched from the CAD solid.
# Based on your successful FreeCAD render:
FLANGE_VOLUME_MM3 = 145230.45 

# --- 2. MATERIAL DATABASE ---
# Density is in g/cm3 | Cost is in USD per kg
MATERIALS = {
    "316 Stainless Steel": {"density": 8.0, "cost_per_kg": 4.50},
    "6061-T6 Aluminum": {"density": 2.7, "cost_per_kg": 2.85},
    "Carbon Steel": {"density": 7.85, "cost_per_kg": 1.20}
}

def run_cost_analysis():
    """Calculates weight and material cost based on 3D volume."""
    print("--- Smart Pressure Flange: Cost & Weight Analysis ---")
    print(f"Total Design Volume: {FLANGE_VOLUME_MM3:.2f} mm3\n")
    
    for mat, props in MATERIALS.items():
        # Convert mm3 to cm3 (divide by 1000)
        volume_cm3 = FLANGE_VOLUME_MM3 / 1000
        # Calculate mass in kg
        mass_kg = (volume_cm3 * props["density"]) / 1000
        # Calculate total cost
        total_cost = mass_kg * props["cost_per_kg"]
        
        print(f"Material: {mat}")
        print(f" - Calculated Mass: {mass_kg:.3f} kg")
        print(f" - Estimated Raw Material Cost: ${total_cost:.2f}\n")

if __name__ == "__main__":
    run_cost_analysis()
