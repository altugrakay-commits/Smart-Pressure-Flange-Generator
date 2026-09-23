"""
cost_analysis.py - Material cost and weight estimation for the
Smart Pressure Flange Generator
================================================================

This module estimates the weight and material cost of a flange from:
    1. Its volume (computed by cad_generator.get_flange_volume_mm³)
    2. The material density and cost per kg (from config.STANDARD_MATERIALS)

The output is a small dataclass (`CostBreakdown`) so it can be consumed
easily by the CLI, the GUI, and the Streamlit interface.

The default material cost in config.py is the raw-material cost (USD/kg).
For a more realistic industrial estimate, a manufacturing multiplier is
also applied.

References
----------
- EN 1092-1: Flange dimensions (via config.py)
- Material properties: EN 10222-2 (via config.py)
"""

from dataclasses import dataclass
from config import STANDARD_MATERIALS
from cad_generator import get_flange_volume_mm3
from engine import DesignInputs, FlangeDesigner

# ============================================================================
# 0. COST FACTORS
# ============================================================================
# These multipliers convert raw material cost to a rough finished-part cost.
# They are indicative only and would be refined by a real workshop quote.
# ----------------------------------------------------------------------------

# Machining + handling + QA overhead as a multiple of raw-material cost.
MANUFACTURING_MULTIPLIER = 2.5

# Waste factor: chips, offcuts, and scrap loss.
WASTE_FACTOR = 1.15

# Currency label used in the report.
CURRENCY = "USD"

# ============================================================================
# 1. RESULT STRUCTURE
# ============================================================================

@dataclass
class CostBreakDown:
    """Weight and cost estimate for a single flange design."""
    material_name: str
    volume_mm3: float
    density_g_cm3: float
    mass_kg: float
    raw_material_cost: float        # mass x coss_per_kg
    adjusted_material_cost: float   # raw cost x WASTE_FACTOR
    finished_part_cost: float   # adjusted cost x MANUFACTURING_MULTIPLIER
    currency: str = CURRENCY

    def format_report(self) -> str:
        """Return a human-readable text report."""
        return(
            f"\n"
            f"========== COST & WEIGHT ANALYSIS ==========\n"
            f"  Material:                 {self.material_name}\n"
            f"  Volume:                   {self.volume_mm3:,.0f} mm³\n"
            f"  Density:                  {self.density_g_cm3:.2f} g/cm³\n"
            f"  Mass:                     {self.mass_kg:.3f} kg\n"
            f"  ----------------------------------------\n"
            f"  Raw material cost:        {self.raw_material_cost:,.2f} {self.currency}\n"
            f"  With waste factor (×{WASTE_FACTOR}):\n"
            f"  Adjusted material cost:   {self.adjusted_material_cost:,.2f} {self.currency}\n"
            f"  Finished part cost (×{MANUFACTURING_MULTIPLIER}):\n"
            f"  Estimated total:          {self.finished_part_cost:,.2f} {self.currency}\n"
            f"===========================================\n"
        )

# ============================================================================
# 2. COST ESTIMATION
# ============================================================================

def estimate_cost(result) -> CostBreakDown:
    """
    Compute weight and cost for a flange design.

    Parameters
    ----------
    result : engine.DesignResult
        Result of FlangeDesigner.compute(), which contains the material key
        and the geometry parameters.

    Returns
    -------
    CostBreakdown
    """

    # --- 1. Look up the material ---
    material_key = result.inputs.material_key
    if material_key not in STANDARD_MATERIALS:
        raise KeyError(f" Material '{material_key}' not in standard database.")

    material = STANDARD_MATERIALS[material_key]
    density = material["density_g_cm3"]         # g/cm³
    cost_per_kg = material["cost_usd_per_kg"]   # USD/kg

    # --- 2. Compute volume via cad_generator ---
    volume_mm3 = get_flange_volume_mm3(result)

    # --- 3. Convert volume to mass ---
    # mm³ → cm³  (÷ 1000)
    # cm³ x g/cm³ → g
    # g → kg (÷ 1000)

    volume_cm3 = volume_mm3 / 1000
    mass_kg = (volume_cm3 * density) / 1000

    # --- 4. Cost Layers ---
    raw_cost = mass_kg * cost_per_kg
    adjusted_cost = raw_cost * WASTE_FACTOR
    finished_cost = adjusted_cost * MANUFACTURING_MULTIPLIER

    return CostBreakDown(
        material_name=material["name"],
        volume_mm3=volume_mm3,
        density_g_cm3=density,
        mass_kg=mass_kg,
        raw_material_cost=raw_cost,
        adjusted_material_cost=adjusted_cost,
        finished_part_cost=finished_cost
    )

# ============================================================================
# 3. SELF-TEST
# ============================================================================

if __name__ =="__main__":

    # Example: DN50, PN16, 200°C, 1.2 MPa
    inputs = DesignInputs(
        dn="DN50", pn="PN16", design_temperature_c=200.0,
        material_key="P250GH", bolt_material_key="A193_B7",
        gasket_type="spiral_wound_graphite", operating_pressure_mpa=1.2,
        verification_method="EN_1092"
    )
    result = FlangeDesigner(inputs).compute()
    breakdown = estimate_cost(result)
    print(breakdown.format_report())

    from engine import DesignInputs, FlangeDesigner
    from cost_analysis import estimate_cost

    for mat in ["P250GH", "16Mo3", "1.4301", "1.4401"]:
        inputs = DesignInputs(
            dn="DN50", pn="PN16", design_temperature_c=200.0,
            material_key=mat, bolt_material_key="A193_B7",
            gasket_type="spiral_wound_graphite", operating_pressure_mpa=1.2,
        )
        result = FlangeDesigner(inputs).compute()
        c = estimate_cost(result)
        print(f"{mat:8s}  {c.mass_kg:.2f} kg   {c.finished_part_cost:>8.2f} USD")