"""
cad_generator.py - Parametric geometry generation for the Smart Pressure Flange Generator
=========================================================================================

This module builds a 3D solid model of an EN 1092-1 Type 11 welding-neck flange
using CadQuery. The geometry is fully parametric and driven by the dimension
tables in `config.py` and the design results from `engine.py`.

The output is a dict of CadQuery Workplane objects:
    {
        'flange':  <the complete flange solid>,
    }

Additionally, the module exports:
    - .step  file (for manufacturing / import into FEA software)
    - .stl   file (for viewing / 3D printing)

References
----------
- EN 1092-1:2018+A1:2019, Table 6 (welding neck flange dimensions)
- EN 1092-1, Type 11 (welding neck, raised face)
"""
import math
from pathlib import Path
from typing import Optional

import cadquery as cq
from cadquery.selectors import NearestToPointSelector
from engine import DesignInputs, FlangeDesigner

from engine import GASKET_DIMENSIONS
from config import EN1092_DIMENSIONS, OUT_DIR

# ============================================================================
# 0. GEOMETRY CONSTANTS
# ============================================================================
# These values are held fixed because they are determined by the standard.
# ----------------------------------------------------------------------------

# Raised face height (EN 1092-1, standard):
RAISED_FACE_HEIGHT_MM = 2.0

# Raised face diameter: typically 2 mm larger than the gasket OD.
# We approximate it as bore + 2 * N (gasket width) + 2 mm.
RAISED_FACE_MARGIN_MM = 2.0

# Fillet radius at the hub-to-flange junction (typical values: 3-8 mm)
FILLET_RADIUS_FRACTION = 0.15   # of hub_d

# Chamger at the hub top (welding prep, typically 1-2 mm)
CHAMFER_SIZE_MM = 1.5

# Hub bottom diameter (at the junction with the flange disc):
# from EN 1092-1, this is typically 1.2-1.4x the hub top diameter.
HUB_BOTTOM_FACTOR = 1.35


# ============================================================================
# 1. GEOMETRY BUILDER
# ============================================================================

def build_flange_geometry(
        dn: str,
        pn: str,
        bore: float,
        hub_top_d: float,
        hub_height: float,
        flange_thickness: float,
        gasket_outer_d: Optional[float] = None
) -> cq.Workplane:
    """
    Build an EN 1092-1 Type 11 welding-neck flange solid using CadQuery.

    Parameters
    ----------
    dn : str
        Nominal size, e.g. "DN50".
    pn : str
        Pressure rating, e.g. "PN16".
    bore : float
        Inner diameter of the pipe (mm).
    hub_top_d : float
        Hub outside diameter at the weld end (top of hub, mm).
        Corresponds to `hub_d` in config.py.
    hub_height : float
        Total height of the hub above the flange disc (mm).
    flange_thickness : float
        Thickness of the flange disc (mm).
    gasket_outer_d : float, optional
        Outer diameter of the gasket. If not provided, calculated from
        the gasket dimensions table in `engine.py`.

    Returns
    -------
    cq.Workplane
        The complete flange solid.
    """
    # --- 1. Look up the dimension spec ---
    if dn not in EN1092_DIMENSIONS:
        raise ValueError(f"DN size '{dn}' not found in EN 1092-1 table.")
    if pn not in EN1092_DIMENSIONS[dn]:
        raise ValueError(f"PN rating '{pn}' unavailable for {dn}.")

    spec = EN1092_DIMENSIONS[dn][pn]
    D_out = spec["D"]           # flange outer diameter
    bolt_circle = spec["K"]     # bolt circle diameter
    bolt_hole_d = spec["L"]     # bolt hole diameter
    n_bolts = spec["n_bolts"]   # number of bolts

    # --- 2. Derived dimensions ---
    # --- 2. Derived dimensions ---
    hub_bottom_d = hub_top_d * HUB_BOTTOM_FACTOR
    hub_bottom_r = hub_bottom_d / 2.0

    # Clearance from the hub to the bolt holes (with 1 mm safety margin)
    bolt_hole_inner_r = bolt_circle / 2.0 - bolt_hole_d / 2.0
    gap_to_holes = bolt_hole_inner_r - hub_bottom_r - 1.0

    # Fillet radius: proportional to the hub, capped by
    #   (a) flange thickness, and (b) clearance to the bolt holes.
    fillet_r = FILLET_RADIUS_FRACTION * hub_top_d
    fillet_r = min(fillet_r, 0.6 * flange_thickness)
    fillet_r = min(fillet_r, gap_to_holes)

    if gasket_outer_d is None:
        # Fallback: assume the raised face is just outside the bore.
        raised_face_d = bore + 2 * RAISED_FACE_MARGIN_MM
    else:
        raised_face_d = gasket_outer_d + RAISED_FACE_MARGIN_MM

    # --- 3. Build the base solid (flange disc) ---
    # Start with a cylinder of the flange OD and thickness.
    flange = (
        cq.Workplane("XY")
        .circle(D_out / 2.0)
        .extrude(flange_thickness)
    )

    # --- 4. Add the hub (tapered, above the disc) ---
    # The hub is a loft between the hub-bottom diameter (at Z = thickness)
    # and the hub-top diameter (at Z = thickness + hub_height).
    hub = (
        cq.Workplane("XY")
        .workplane(offset=flange_thickness)
        .circle(hub_bottom_d / 2.0)
        .workplane(offset=hub_height)
        .circle(hub_top_d / 2.0)
        .loft(combine=True)
    )
    flange = flange.union(hub)

    # --- 5. Add the raised face on the top of the disc ---
    # Standard raised face: a small cylinder above the flange disc, but
    # concentric and slightly inside the flange 0D.
    raised_face = (
        cq.Workplane("XY")
        .workplane(offset=-RAISED_FACE_HEIGHT_MM)
        .circle(raised_face_d / 2.0)
        .extrude(RAISED_FACE_HEIGHT_MM)
    )
    flange = flange.union(raised_face)

    # --- 6. Cut the central bore ---
    # Through bore from Z = -1 to z = thickness + hub_height + 1
    total_height = flange_thickness + hub_height + RAISED_FACE_HEIGHT_MM
    bore_cutter = (
        cq.Workplane("XY")
        .workplane(offset=-1.0)
        .circle(bore / 2.0)
        .extrude(total_height + 2.0)
    )
    flange = flange.cut(bore_cutter)

    # --- 7. Cut the bolt holes ---
    # Bolt holes are cut through the flange disc only (not the raised face).
    bolt_holes_cutter = (
        cq.Workplane("XY")
        .workplane(offset=-1.0)
        .polarArray(bolt_circle / 2.0, 0.0, 360.0, n_bolts)
        .circle(bolt_hole_d / 2.0)
        .extrude(flange_thickness + 2.0)
    )
    flange = flange.cut(bolt_holes_cutter)

    # --- 8. Fillet the hub-to-disc junction ---
    # Find the circulat edge where the hub meets the flange disc.
    try:
        junction_selector = NearestToPointSelector(
            (hub_bottom_d / 2.0, 0.0, flange_thickness)
        )
        flange = flange.edges(junction_selector).fillet(fillet_r)
        print(f"✅ Fillet applied r = {fillet_r:.2f} mm")
    except Exception as ex:
        print(f"⚠️ Fillet skipped: {ex}")

    # --- 9. Chamfer the top of the hub (welding preparation) ---
    try:
        flange = flange.faces(">Z").edges().chamfer(CHAMFER_SIZE_MM)
        print(f"✅ Chamfer applied: {CHAMFER_SIZE_MM:.2f} mm")
    except Exception as ex:
        print(f"⚠️ Chamfer skipped: {ex}")

    return flange


# ============================================================================
# 2. HIGH-LEVEL EXPORT API
# ============================================================================
def _gasket_od_for(dn:str) -> Optional[float]:
    """
    Return the gasket outer diameter (d2) for a given DN, or None if 
    the DB is not in the gasket dimension table.
    """
    if dn in GASKET_DIMENSIONS:
        return GASKET_DIMENSIONS[dn]["d2"]
    return None

def generate_flange_from_result(result, output_dir: Path = OUT_DIR):
    """
    Build a flange solid from a DesignResult object and export it
    to STEP and STL files.
    """
    gasket_outer_d = _gasket_od_for(result.inputs.dn)

    # Build the solid
    flange = build_flange_geometry(
        dn=result.inputs.dn,
        pn=result.inputs.pn,
        bore=result.bore,
        hub_top_d=result.hub_d,
        hub_height=result.hub_h,
        flange_thickness=result.flange_thickness,
        gasket_outer_d=gasket_outer_d
    )

    # Export paths
    stem = f"flange_{result.inputs.dn}_{result.inputs.pn}"
    step_path = output_dir / f"{stem}.step"
    stl_path = output_dir / f"{stem}.stl"

    # Export
    cq.exporters.export(flange, str(step_path))
    cq.exporters.export(flange, str(stl_path))

    print(f"✅ STEP file written to: {step_path}")
    print(f"✅ STL  file written to: {stl_path}")

    return {
        "solid": flange,
        "step_path": step_path,
        "stl_path": stl_path
    }

def get_flange_volume_mm3(result) -> float:
    """
    Return the volume of the flange solid in mm³.
    """
    gasket_outer_d = _gasket_od_for(result.inputs.dn)

    flange = build_flange_geometry(
        dn=result.inputs.dn,
        pn=result.inputs.pn,
        bore=result.bore,
        hub_top_d=result.hub_d,
        hub_height=result.hub_h,
        flange_thickness=result.flange_thickness,
        gasket_outer_d=gasket_outer_d
    )
    return flange.val().Volume() # type: ignore

# ============================================================================
# 3. SELF-TEST
# ============================================================================

if __name__ == "__main__":

    # Example: DN50, PN16, 200°C, 1.2 MPa
    inputs = DesignInputs(
        dn="DN50", pn="PN16", design_temperature_c=200.0,
        material_key="P250GH", bolt_material_key="A193_B7",
        gasket_type="spiral_wound_graphite", operating_pressure_mpa=1.2,
        verification_method="EN_1092"
    )
    result = FlangeDesigner(inputs).compute()

    print("Generating flange geometry...")
    output = generate_flange_from_result(result)
    volume_mm3 = output["solid"].val().Volume()
    print(f"\nFlange volume: {volume_mm3:,.0f} mm³")
    print(f"Estimated mass (P250GH @ 7.85 g/cm³): "
          f"{volume_mm3 * 7.85e-6:.2f} kg")