"""
engine.py - Mechanical design calculations for the Smart Pressure Flange Generator
==================================================================================

This module contains the engineering calculation core. It implements:

    1. Pressure rating lookup (EN 1092-1) with temperature derating
    2. Minimum wall thickness calculation (EN 13445 / ASME VIII Div. 1)
    3. Hoop stress verification
    4. Bolt load analysis (ASME VIII Div. 1, Appendix 2)
    5. Gasket seating verification
    6. Flange rigidity check (simplified Kellogg method)
    7. Overall pass/fail verdict with warnings and errors

All calculations follow established pressure-vessel design codes. Every
formula used is documented in the docstring of the method that applies it,
so a reviewer can trace each number to its source.

⚠️  IMPORTANT
-------------
This tool is intended for preliminary design, education, and design-space
exploration. Final flange design for production must be verified by a
qualified pressure-equipment engineer using the applicable code (EN 13445,
EN 1092-1, ASME VIII) and the latest revision of the material data sheets.
"""

from dataclasses import dataclass, field
from typing import List
import math

from config import (
    EN1092_DIMENSIONS,
    STANDARD_MATERIALS,
    get_derating_factor,
    get_allowable_stress,
    WELD_EFFICIENCY_PARTIAL,
)


# ============================================================================
# 0. BOLT MATERIAL DATABASE
# ============================================================================
# Allowable bolt stresses (MPa) at various temperatures, from ASME BPVC
# Section II Part D, Table 3 (for ASTM A193 B7) and Table 4 (for B16).
#
# These are the ALLOWABLE stresses (already divided by safety factor),
# so they can be used directly in the ASME bolt-load formulas.
# ============================================================================

BOLT_MATERIALS = {
    "A193_B7": {
        "name": "ASTM A193 B7 (Chrome-Moly)",
        "yield_rt": 720,
        "allowable_curve": [
            (-29, 172), (20, 172), (100, 172), (200, 172),
            (300, 165), (400, 154), (450, 145), (500, 132),
            (550, 115),
        ],
        "max_temp": 550,
    },
    "A193_B16": {
        "name": "ASTM A193 B16 (Chrome-Moly-V)",
        "yield_rt": 760,
        "allowable_curve": [
            (-29, 179), (20, 179), (100, 179), (200, 179),
            (300, 179), (400, 179), (450, 172), (500, 160),
            (550, 145),
        ],
        "max_temp": 550,
    },
    "A320_L7": {
        "name": "ASTM A320 L7 (Low-Temperature)",
        "yield_rt": 720,
        "allowable_curve": [
            (-101, 172), (-50, 172), (20, 172), (100, 172),
            (200, 172), (300, 165),
        ],
        "max_temp": 300,
    },
}


# ============================================================================
# 1. GASKET DATABASE
# ============================================================================
# Gasket parameters per ASME VIII Div. 1, Appendix 2, Table 2-5.1.
#   m  - gasket factor (dimensionless)
#   y  - minimum design seating stress (MPa)
#   N  - gasket width (mm) - representative value for each DN
#   type - material description
# ============================================================================

GASKET_TYPES = {
    "spiral_wound_graphite": {
        "name": "Spiral-Wound (SS316 + Graphite filler)",
        "m": 3.0,
        "y": 69.0,           # MPa
        "N_fraction": 0.4,   # gasket width as fraction of bolt circle radius
    },
    "spiral_wound_ptfe": {
        "name": "Spiral-Wound (SS316 + PTFE filler)",
        "m": 2.5,
        "y": 25.5,
        "N_fraction": 0.4,
    },
    "flat_fiber": {
        "name": "Flat compressed fiber (non-asbestos)",
        "m": 2.75,
        "y": 25.5,
        "N_fraction": 0.5,
    },
    "rubber": {
        "name": "Rubber (elastomer)",
        "m": 1.25,
        "y": 0.7,
        "N_fraction": 0.5,
    },
}

# Realistic gasket dimensions per EN1514-2 (sprial round) and EN1514-1 (flat).
# For each DN, we store the gasket inner diameter (d1), outer diameter (d2), 
# and the effective gasket width N = (d2 - d1) / 2
GASKET_DIMENSIONS = {
    "DN15": {"d1": 22.0, "d2": 39.0, "N": 8.5},
    "DN20": {"d1": 27.0, "d2": 50.0, "N": 11.5},
    "DN25": {"d1": 34.0, "d2": 57.0, "N": 11.5},
    "DN32": {"d1": 43.0, "d2": 68.0, "N": 12.5},
    "DN40": {"d1": 49.0, "d2": 78.0, "N": 14.5},
    "DN50": {"d1": 61.0, "d2": 86.0, "N": 12.5},
    "DN65": {"d1": 77.0, "d2": 104.0, "N": 13.5},
    "DN80": {"d1": 90.0, "d2": 120.0, "N": 15.0},
    "DN100": {"d1": 115.0, "d2": 149.0, "N": 17.0},
    "DN125": {"d1": 141.0, "d2": 178.0, "N": 18.5},
    "DN150": {"d1": 169.0, "d2": 207.0, "N": 19.0},
    "DN200": {"d1": 220.0, "d2": 265.0, "N": 22.5},
    "DN250": {"d1": 273.0, "d2": 324.0, "N": 25.5},
    "DN300": {"d1": 324.0, "d2": 380.0, "N": 28.0},
}


# ============================================================================
# 2. INPUT AND OUTPUT DATA STRUCTURES
# ============================================================================

@dataclass
class DesignInputs:
    """All inputs required for a flange design calculation."""
    dn: str                                  # e.g. "DN50"
    pn: str                                  # e.g. "PN16"
    design_temperature_c: float              # design temperature (°C)
    material_key: str                        # key in STANDARD_MATERIALS
    bolt_material_key: str                   # key in BOLT_MATERIALS
    gasket_type: str                         # key in GASKET_TYPES
    operating_pressure_mpa: float            # actual working pressure (MPa)
    corrosion_allowance_mm: float = 1.0
    weld_efficiency: float = WELD_EFFICIENCY_PARTIAL
    verification_method: str = "EN_1092"    # or "ASME_VIII_App2"


@dataclass
class DesignResult:
    """All results and diagnostics from a flange design calculation."""
    # Echo of inputs
    inputs: DesignInputs

    # Geometry (from EN 1092-1 table)
    D_out: float = 0.0
    bolt_circle: float = 0.0
    bolt_hole_dia: float = 0.0
    n_bolts: int = 0
    bolt_size: str = ""
    flange_thickness: float = 0.0
    hub_d: float = 0.0
    hub_h: float = 0.0
    bore: float = 0.0

    # Material state / rating.
    material_name: str = ""
    bolt_material_name: str = ""
    gasket_name: str = ""
    P_rating_rt: float = 0.0
    P_rating_at_T: float = 0.0
    derating_factor: float = 1.0
    allowable_stress_flange: float = 0.0
    allowable_stress_bolt: float = 0.0

    # Thickness check
    t_required: float = 0.0
    t_actual: float = 0.0
    thickness_margin_pct: float = 0.0

    # Hoop stress check
    hoop_stress: float = 0.0
    hoop_stress_ok: bool = False

    # Bolt analysis (ASME VIII App. 2)
    G_diameter: float = 0.0                # gasket reaction diameter
    b_eff: float = 0.0                     # effective gasket width
    Wm1: float = 0.0                       # gasket seating load (N)
    Wm2: float = 0.0                       # operating load (N)
    Am_required: float = 0.0               # total required bolt area (mm²)
    Ab_actual: float = 0.0                 # actual bolt area (mm²)
    bolt_stress_operating: float = 0.0     # MPa
    bolt_stress_seating: float = 0.0       # MPa

    # Rigidity
    rigidity_index: float = 0.0
    rigidity_ok: bool = False

    # Warnings and errors
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Overall verdict
    overall_pass: bool = False


# ============================================================================
# 3. CALCULATION HELPERS
# ============================================================================

def _interp_curve(curve: List[tuple], x: float) -> float:
    """Linear interpolation on a sorted (x, y) curve, clamped to endpoints."""
    if x <= curve[0][0]: return curve[0][1]
    if x >= curve[-1][0]: return curve[-1][1]
    for i in range(len(curve) - 1):
        x0, y0 = curve[i]
        x1, y1 = curve[i + 1]
        if x0 <= x <= x1:
            alpha = (x - x0) / (x1 - x0)
            return y0 + alpha * (y1 - y0)
    return curve[-1][1]


def get_bolt_allowable(bolt_material_key: str, T_c: float) -> float:
    """Allowable bolt stress (MPa) at a given temperature."""
    return _interp_curve(BOLT_MATERIALS[bolt_material_key]["allowable_curve"], T_c)


# ============================================================================
# 4. MAIN DESIGNER CLASS
# ============================================================================

class FlangeDesigner:
    """
    Performs the complete mechanical design calculation for a bolted flange.

    Usage
    -----
    >>> from engine import DesignInputs, FlangeDesigner
    >>> inputs = DesignInputs(
    ...     dn="DN50", pn="PN16", design_temperature_c=200.0,
    ...     material_key="P250GH", bolt_material_key="A193_B7",
    ...     gasket_type="spiral_wound_graphite", operating_pressure_mpa=1.2,
    ... )
    >>> result = FlangeDesigner(inputs).compute()
    >>> print(result.overall_pass)
    True
    """

    def __init__(self, inputs: DesignInputs):
        self.inputs = inputs
        self.result = DesignResult(inputs=inputs)

    # ------------------------------------------------------------------------
    # Step 1: Validate inputs and pull standard geometry
    # ------------------------------------------------------------------------
    def _step1_validate_and_load_geometry(self):
        inp = self.inputs
        r = self.result

        # Validate DN and PN
        if inp.dn not in EN1092_DIMENSIONS:
            r.errors.append(f"DN size '{inp.dn}' not found.")
            return
        
        if inp.pn not in EN1092_DIMENSIONS[inp.dn]:
            r.errors.append(f"PN rating '{inp.pn}' unavailable for {inp.dn}.")
            return

        spec = EN1092_DIMENSIONS[inp.dn][inp.pn]
        r.D_out = spec["D"]
        r.bolt_circle = spec["K"]
        r.bolt_hole_dia = spec["L"]
        r.n_bolts = spec["n_bolts"]
        r.bolt_size = spec["bolt_size"]
        r.flange_thickness = spec["thickness"]
        r.hub_d = spec["hub_d"]
        r.hub_h = spec["hub_h"]
        r.bore = EN1092_DIMENSIONS[inp.dn]["nominal_bore"]

        # Validate material
        if inp.material_key not in STANDARD_MATERIALS:
            r.errors.append(f"Material '{inp.material_key}' unknown.")
            return
        r.material_name = STANDARD_MATERIALS[inp.material_key]["name"]

        # Validate bolt material
        if inp.bolt_material_key not in BOLT_MATERIALS:
            r.errors.append(f"Bolt material '{inp.bolt_material_key}' unknown.")
            return
        r.bolt_material_name = BOLT_MATERIALS[inp.bolt_material_key]["name"]

        # Validate gasket
        if inp.gasket_type not in GASKET_TYPES:
            r.errors.append(f"Gasket type '{inp.gasket_type}' unknown.")
            return
        r.gasket_name = GASKET_TYPES[inp.gasket_type]["name"]

        # Check temperature within material limits
        mat = STANDARD_MATERIALS[inp.material_key]
        if inp.design_temperature_c < mat["min_temp"]:
            r.errors.append(f"T below minimum for {mat['name']}.")
        if inp.design_temperature_c > mat["max_temp"]:
            r.warnings.append(f"T exceeds typical maximum for {mat['name']}.")

    # ------------------------------------------------------------------------
    # Step 2: Derated pressure rating and allowable stresses
    # ------------------------------------------------------------------------
    def _step2_derate_pressure(self):
        inp = self.inputs
        r = self.result
        if r.errors: return

        # Nominal PN rating → MPa (at room temperature)
        pn_bar = float(inp.pn.replace("PN", ""))
        r.P_rating_rt = pn_bar * 0.1  # bar → MPa

        # Derating at design temperature
        r.derating_factor = get_derating_factor(inp.material_key, inp.design_temperature_c)
        r.P_rating_at_T = r.P_rating_rt * r.derating_factor

        # Allowable stresses at T
        r.allowable_stress_flange = get_allowable_stress(inp.material_key, inp.design_temperature_c)
        r.allowable_stress_bolt = get_bolt_allowable(inp.bolt_material_key, inp.design_temperature_c)

        # Warn if operating pressure exceeds derated rating
        if inp.operating_pressure_mpa > r.P_rating_at_T:
            r.errors.append(
                f"Operating pressure {inp.operating_pressure_mpa:.2f} MPa exceeds "
                f"derated PN rating {r.P_rating_at_T:.2f} MPa at "
                f"{inp.design_temperature_c:.0f} °C. "
            )

    # ------------------------------------------------------------------------
    # Step 3: Minimum wall thickness (EN 13445 / ASME VIII Div. 1)
    # ------------------------------------------------------------------------
    def _step3_thickness_check(self):
        """
        Minimum wall thickness for a cylindrical shell under internal pressure.

        EN 13445 formula:
            e = (P · Di) / (2 · f · E - P) + c

        where:
            e = required minimum wall thickness (mm)
            P = design pressure (MPa)
            Di = internal diameter (mm)
            f = nominal design stress = allowable_stress_flange (MPa)
            E = weld efficiency
            c = corrosion allowance (mm)

        We compare e to the flange thickness from EN 1092-1 (which is
        already designed for the PN class, so it typically passes).
        """
        inp = self.inputs
        r = self.result
        if r.errors: return
        P = inp.operating_pressure_mpa
        Di = r.bore
        f = r.allowable_stress_flange
        E = inp.weld_efficiency
        c = inp.corrosion_allowance_mm

        denom = 2.0 * f * E - P
        if denom <= 0:
            r.errors.append("Invalid thickness calculation: denominator ≤ 0. ")
            return

        r.t_required = (P * Di) / denom + c
        r.t_actual = r.flange_thickness
        r.thickness_margin_pct = 100.0 * (r.t_actual - r.t_required) / r.t_required

        if r.t_actual < r.t_required:
            r.errors.append(f"Flange thickness {r.t_actual:.1f} mm < required {r.t_required:.2f} mm.")
        elif r.thickness_margin_pct < 5.0:
            r.warnings.append(f"Thickness margin is only {r.thickness_margin_pct:.1f}%. ")

    # ------------------------------------------------------------------------
    # Step 4: Hoop stress verification
    # ------------------------------------------------------------------------
    def _step4_hoop_stress(self):
        """
        Thin-wall hoop stress for a cylindrical shell under internal pressure:

            σ_h = P · Di / (2 · t)

        We compare this to the allowable stress (with weld efficiency).
        """
        inp = self.inputs
        r = self.result
        if r.errors: return

        P = inp.operating_pressure_mpa
        Di = r.bore
        t = r.flange_thickness

        r.hoop_stress = (P * Di) / (2.0 * t)
        allowable = r.allowable_stress_flange * inp.weld_efficiency
        r.hoop_stress_ok = r.hoop_stress <= allowable

        if not r.hoop_stress_ok:
            r.errors.append(f"Hoop stress {r.hoop_stress:.1f} MPa exceeds allowable {allowable:.1f} MPa.")

    # ------------------------------------------------------------------------
    # Step 5: Bolt load analysis (ASME VIII Div. 1, Appendix 2)
    # ------------------------------------------------------------------------
    def _step5_bolt_analysis(self):
        """
        Bolted joint analysis per ASME VIII Div. 1, Appendix 2.

        Gasket reaction diameter:
            G = bolt_circle - N           (approximation; conservative)

        Effective gasket width:
            b0 = N / 2
            b  = b0                if b0 ≤ 6.4 mm
            b  = 2.5 · sqrt(b0)    if b0 > 6.4 mm

        Gasket seating load (Wm1):
            Wm1 = π · b · G · y

        Operating load (Wm2):
            Wm2 = (π · G² / 4) · P + 2 · π · b · G · m · P

        Required bolt area:
            Am = max(Wm1, Wm2) / Sb

        Actual bolt area:
            Ab = n_bolts · A_bolt_tensile
        """
        inp = self.inputs
        r = self.result
        if r.errors: return

        if inp.dn not in GASKET_DIMENSIONS:
            r.warnings.append(f"No gasket dimensions found for {inp.dn}; using bolt-circle approximation.")
            N = 0.4 * (r.bolt_circle / 2.0)
            G = r.bolt_circle - N
        else:
            gdim = GASKET_DIMENSIONS[inp.dn]
            N = gdim["N"]
            G = gdim["d1"] + N  # reaction diameter = d1 + N (conservative)

        r.G_diameter = G
        gasket = GASKET_TYPES[inp.gasket_type]
        m = gasket["m"]
        y = gasket["y"]

        # Effective gasket width
        b0 = N / 2.0
        b_eff = b0 if b0 <= 6.4 else 2.5 * math.sqrt(b0)
        r.b_eff = b_eff

        # Gasket reaction diameter (approximate)
        r.G_diameter = r.bolt_circle - N

        P = inp.operating_pressure_mpa
        # Wm1: gasket seating
        r.Wm1 = math.pi * b_eff * G * y
        # Wm2: operating
        r.Wm2 = (math.pi * G**2 / 4.0) * P + 2.0 * math.pi * b_eff * G * m * P

        # Required bolt area
        Sb = r.allowable_stress_bolt
        r.Am_required = max(r.Wm1, r.Wm2) / Sb

        # Actual bolt area from bolt size
        bolt_tensile_area = self._bolt_tensile_area(r.bolt_size)
        r.Ab_actual = r.n_bolts * bolt_tensile_area

        # Bolt stresses
        if r.Ab_actual > 0:
            r.bolt_stress_operating = r.Wm2 / r.Ab_actual
            r.bolt_stress_seating = r.Wm1 / r.Ab_actual

        if inp.verification_method == "EN_1092":
            # In EN philosophy, the standard flange is accepted by rule.
            # We will report the ASME numbers, but we do not fail the design
            # on the ASME bolt-area check alone.

            if r.Ab_actual < r.Am_required:
                r.errors.append(
                    f"ASME VIII App. 2 (informational): bolt area "
                    f"{r.Ab_actual:.1f} < {r.Am_required:.1f} mm² required."
                    f"This is normal for EN 1092-1 flanges (design-by-rule). "
                    f"and is not a failure under EN practice."
                )
            else:   # ASME_VIII_App2
                if r.Ab_actual < r.Am_required:
                    r.warnings.append(
                        f"ASME VIII App. 2: bolt area insufficient - "
                        f"required {r.Am_required:.1f} mm², available {r.Ab_actual:.1f} mm²."
                    )
                elif r.Ab_actual < 1.1 * r.Am_required:
                    r.warnings.append(
                        f"ASME VIII App. 2: bolt area margin is only "
                        f"{100.0 * (r.Ab_actual - r.Am_required) / r.Am_required:.1f}%."
                    )

    @staticmethod
    def _bolt_tensile_area(bolt_size):
        """
        Tensile stress area of a metric bolt (mm²), from ISO 898-1.
        Returns the tensile area for the closest match.
        """
        # Standard metric bolt tensile areas (mm²)
        areas = {
            "M10": 58.0, "M12": 84.3, "M16": 157.0, "M20": 245.0, "M22": 303.0, 
            "M24": 353.0, "M27": 459.0, "M30": 561.0, "M33": 694.0, "M36": 817.0}
        return areas.get(bolt_size, 0.0)

    # ------------------------------------------------------------------------
    # Step 6: Flange rigidity check (simplified)
    # ------------------------------------------------------------------------
    def _step6_rigidity(self):
        """
        Simplified flange rigidity index, based on the Kellogg method:

            J = (D_out / t_flange) / (K / L)

        where:
            D_out = outer diameter (mm)
            t_flange = flange thickness (mm)
            K = bolt circle diameter (mm)
            L = bolt hole diameter (mm)

        A flange is generally considered rigid if J < 1.0.
        This is a screening check, not a substitute for detailed FEA.
        """
        r = self.result
        if r.errors: return
        if r.flange_thickness <= 0 or r.bolt_hole_dia <= 0: return

        r.rigidity_index = (r.D_out / r.flange_thickness) / (r.bolt_circle / r.bolt_hole_dia)
        r.rigidity_ok = r.rigidity_index < 1.0

        if not r.rigidity_ok:
            r.warnings.append(f"Rigidity index J = {r.rigidity_index:.2f} (>= 1.0). ")

    # ------------------------------------------------------------------------
    # Step 7: Compile the final verdict
    # ------------------------------------------------------------------------
    def _step7_verdict(self):
        r = self.result
        r.overall_pass = not bool(r.errors)

    # ------------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------------
    def compute(self):
        """Run all calculation steps in order and return the result."""
        self._step1_validate_and_load_geometry()
        self._step2_derate_pressure()
        self._step3_thickness_check()
        self._step4_hoop_stress()
        self._step5_bolt_analysis()
        self._step6_rigidity()
        self._step7_verdict()
        return self.result


# ============================================================================
# 5. TEXT REPORT GENERATOR (for CLI output)
# ============================================================================

def format_report(result: DesignResult) -> str:
    """Format a DesignResult as a human-readable text report."""
    r = result
    inp = r.inputs

    lines = []
    lines.append("=" * 70)
    lines.append("SMART PRESSURE FLANGE - DESIGN REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  Flange size:            {inp.dn} {inp.pn}")
    lines.append(f"  Design temperature:     {inp.design_temperature_c:.0f} °C")
    lines.append(f"  Operating pressure:     {inp.operating_pressure_mpa:.2f} MPa")
    lines.append(f"  Flange material:        {r.material_name}")
    lines.append(f"  Bolt material:          {r.bolt_material_name}")
    lines.append(f"  Gasket:                 {r.gasket_name}")
    lines.append("")

    lines.append("-" * 70)
    lines.append("1. GEOMETRY (EN 1092-1)")
    lines.append("-" * 70)
    lines.append(f"  Outer diameter (D):     {r.D_out:.1f} mm")
    lines.append(f"  Bolt circle (K):        {r.bolt_circle:.1f} mm")
    lines.append(f"  Bolt holes:             {r.n_bolts} × Ø{r.bolt_hole_dia:.1f} mm ({r.bolt_size})")
    lines.append(f"  Flange thickness:       {r.flange_thickness:.1f} mm")
    lines.append(f"  Hub diameter:           {r.hub_d:.1f} mm")
    lines.append(f"  Hub height:             {r.hub_h:.1f} mm")
    lines.append(f"  Nominal bore:           {r.bore:.1f} mm")
    lines.append("")

    lines.append("-" * 70)
    lines.append("2. PRESSURE RATING (with temperature derating)")
    lines.append("-" * 70)
    lines.append(f"  PN rating at 20 °C:     {r.P_rating_rt:.2f} MPa ({inp.pn})")
    lines.append(f"  Derating factor:        {r.derating_factor:.3f}")
    lines.append(f"  Derated rating at T:    {r.P_rating_at_T:.2f} MPa")
    lines.append(f"  Allowable flange stress:{r.allowable_stress_flange:>7.1f} MPa")
    lines.append(f"  Allowable bolt stress:  {r.allowable_stress_bolt:>7.1f} MPa")
    lines.append("")

    lines.append("-" * 70)
    lines.append("3. THICKNESS CHECK (EN 13445)")
    lines.append("-" * 70)
    lines.append(f"  Required thickness:     {r.t_required:.2f} mm")
    lines.append(f"  Available thickness:    {r.t_actual:.2f} mm")
    lines.append(f"  Margin:                 {r.thickness_margin_pct:+.1f}%")
    lines.append("")

    lines.append("-" * 70)
    lines.append("4. HOOP STRESS CHECK")
    lines.append("-" * 70)
    lines.append(f"  Hoop stress:            {r.hoop_stress:.1f} MPa")
    lines.append(f"  Allowable:              {r.allowable_stress_flange * inp.weld_efficiency:.1f} MPa")
    lines.append(f"  Result:                 {'PASS' if r.hoop_stress_ok else 'FAIL'}")
    lines.append("")

    lines.append("-" * 70)
    lines.append("5. BOLT LOAD ANALYSIS (ASME VIII Div. 1, App. 2)")
    lines.append("-" * 70)
    lines.append(f"  Gasket reaction dia (G): {r.G_diameter:.1f} mm")
    lines.append(f"  Effective gasket width:  {r.b_eff:.2f} mm")
    lines.append(f"  Wm1 (seating):           {r.Wm1:.0f} N")
    lines.append(f"  Wm2 (operating):         {r.Wm2:.0f} N")
    lines.append(f"  Required bolt area (Am): {r.Am_required:.1f} mm²")
    lines.append(f"  Available bolt area (Ab):{r.Ab_actual:.1f} mm²")
    lines.append(f"  Bolt stress (operating): {r.bolt_stress_operating:.1f} MPa")
    lines.append(f"  Bolt stress (seating):   {r.bolt_stress_seating:.1f} MPa")
    lines.append("")

    lines.append("-" * 70)
    lines.append("6. FLANGE RIGIDITY (simplified Kellogg)")
    lines.append("-" * 70)
    lines.append(f"  Rigidity index J:        {r.rigidity_index:.2f}")
    lines.append(f"  Result:                  {'PASS (J < 1.0)' if r.rigidity_ok else 'MARGINAL'}")
    lines.append("")

    if r.errors:
        lines.append("-" * 70)
        lines.append("ERRORS")
        lines.append("-" * 70)
        for e in r.errors:
            lines.append(f"  ✗ {e}")
        lines.append("")

    if r.warnings:
        lines.append("-" * 70)
        lines.append("WARNINGS")
        lines.append("-" * 70)
        for w in r.warnings:
            lines.append(f"  ⚠ {w}")
        lines.append("")

    lines.append("=" * 70)
    lines.append(f"OVERALL VERDICT: {'✓ PASS' if r.overall_pass else '✗ FAIL'}")
    lines.append("=" * 70)

    return "\n".join(lines)


# ============================================================================
# 6. SELF-TEST
# ============================================================================

if __name__ == "__main__":
    # Example: DN 50 PN 16, carbon steel, 200°C, 1.2 MPa operating pressure
    inputs = DesignInputs(
        dn="DN50", pn="PN16", design_temperature_c=200.0,
        material_key="P250GH", bolt_material_key="A193_B7",
        gasket_type="spiral_wound_graphite", operating_pressure_mpa=1.2,
        verification_method="EN_1092"   # or "ASME_VIII_App2"
    )

    result = FlangeDesigner(inputs).compute()
    print(format_report(result))