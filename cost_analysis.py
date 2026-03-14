# -------------------------------------------------------------------
# Copyright (c) 2026 altugrakay-commits. All rights reserved.
# -------------------------------------------------------------------

# In a full project, this could import the Volume directly from the CAD script
volume_mm3 = 145000.0 # Example volume from your render

# Material Properties
# Density (g/cm3), Cost per kg (USD)
materials = {
    "316 Stainless Steel": {"density": 8.0, "cost": 4.50},
    "6061 Aluminum": {"density": 2.7, "cost": 2.80}
}

print("--- Flange Cost Estimation ---")
for mat, props in materials.items():
    # Convert mm3 to cm3 (divide by 1000)
    mass_kg = (volume_mm3 / 1000 * props["density"]) / 1000
    total_cost = mass_kg * props["cost"]
    
    print(f"{mat}: {mass_kg:.3f} kg | Estimated Cost: ${total_cost:.2f}")