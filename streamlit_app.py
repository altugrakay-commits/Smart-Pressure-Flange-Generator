"""
streamlit_app.py - Web interface for the Smart Pressure Flange Generator
=========================================================================

This module exposes the flange design pipeline as a Streamlit web app.
It reuses the same backend as the CLI and GUI:

    engine.FlangeDesigner          → design calculations
    cad_generator                  → STEP + STL export
    cost_analysis.estimate_cost    → weight and cost breakdown

Layout
------
    Left column:  input form (DN, PN, temperature, pressure, materials)
    Right column: design report + download buttons
    Below:        3D preview (static PyVista screenshot, rendered off-screen)

Deployment
----------
This file is designed for Streamlit Cloud. The repository must contain:
    - streamlit_app.py       (this file)
    - requirements.txt
    - packages.txt           (libgl1)
    - runtime.txt            (python-3.11)
"""

import io
import os
import tempfile
from pathlib import Path

import streamlit as st

from config import (
    EN1092_DIMENSIONS,
    OUT_DIR,
    STANDARD_MATERIALS,
    list_dn_sizes,
    list_pn_ratings,
    list_standard_materials,
)
from engine import (
    BOLT_MATERIALS,
    GASKET_TYPES,
    DesignInputs,
    FlangeDesigner,
    format_report,
)
from cad_generator import generate_flange_from_result
from cost_analysis import estimate_cost

from visualization import load_flange_mesh
import pyvista as pv

# ============================================================================
# 0. PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Smart Pressure Flange Generator",
    page_icon="🔩",
    layout="wide"
)

st.title("🔩 Smart Pressure Flange Generator")
st.markdown(
    "Parametric EN 1092-1 Type 11 welding-neck flange design "
    "with temperature derating, ASME VIII bolt analysis, "
    "3D CAD export, and cost estimation."
)

# ============================================================================
# 1. SIDEBAR - INPUT FORM
# ============================================================================

with st.sidebar:
    st.header("⚙️ Design Inputs")

    # --- DN selection ---
    dn_keys = list_dn_sizes()
    dn_labels = [
        f"{dn} ({EN1092_DIMENSIONS[dn]['nominal_bore']:.0f} mm)"
        for dn in dn_keys
    ]
    dn_label = st.selectbox("DN size", dn_labels, index=dn_keys.index("DN50"))
    dn_key = dn_label.split()[0]

    # --- PN selection (filtered by DN) ---
    pn_keys = list_pn_ratings(dn_key)
    pn_labels = [
        f"{pn} ({float(pn.replace('PN', '')) * 0.1:.1f} MPa)"
        for pn in pn_keys
    ]
    pn_index = pn_keys.index("PN16") if "PN16" in pn_keys else 0
    pn_label = st.selectbox("PN rating", pn_labels, index=pn_index)
    pn_key = pn_label.split()[0]

    # --- Temperature and pressure ---
    temp = st.number_input("Design temperature (°C)", value=200.0, step=10.0)
    pressure = st.number_input("Operating Pressure (MPa)", value=1.2, step=0.1)

    # --- Materials ---
    material_labels = [STANDARD_MATERIALS[k]["name"] for k in list_standard_materials()]
    material_label = st.selectbox("Flange material", material_labels, index=0)
    material_key = next(
        k for k in list_standard_materials()
        if STANDARD_MATERIALS[k]["name"] == material_label
    )

    bolt_labels = [BOLT_MATERIALS[k]["name"] for k in BOLT_MATERIALS.keys()]
    bolt_label = st.selectbox("Bolt material", bolt_labels, index=0)
    bolt_key = next(
        k for k in BOLT_MATERIALS.keys()
        if BOLT_MATERIALS[k]["name"] == bolt_label
    )

    gasket_labels = [GASKET_TYPES[k]["name"] for k in GASKET_TYPES.keys()]
    gasket_label = st.selectbox("Gasket type", gasket_labels, index=0)
    gasket_key = next(
        k for k in GASKET_TYPES.keys()
        if GASKET_TYPES[k]["name"] == gasket_label 
    )

    # --- Verification method ---
    verification = st.radio(
        "Verification method",
        ["EN_1092", "ASME_VIII_App2"],
        index=0,
        help=(
            "EN_1092: design-by-rule, warnings only. "
            "ASME_VIII_App2: design_by_analysis, strict failure."
        )
    )

    # --- Action button ---
    run_clicked = st.button("🚀 Run Design", type="primary", use_container_width=True)

# ============================================================================
# 2. MAIN AREA - REPORT
# ============================================================================

# Left/right Layout for report and download.
col_report, col_download = st.columns([3, 1])

if run_clicked:
    # --- Build inputs ---
    try:
        inputs = DesignInputs(
            dn=dn_key,
            pn=pn_key,
            design_temperature_c=float(temp),
            material_key=material_key,
            bolt_material_key=bolt_key,
            gasket_type=gasket_key,
            operating_pressure_mpa=float(pressure),
            verification_method=verification
        )
    except Exception as e:
        st.error(f"❌ Invalid inputs: {e}")
        st.stop()

    # --- Run Design ---
    with st.spinner("Running design calcuation..."):
        try:
            result = FlangeDesigner(inputs).compute()
        except Exception as e:
            st.error(f"❌ Invalid inputs: {e}")
            st.stop()

    # --- Display verdict banner ---
    if result.overall_pass:
        st.success(f"✅ DESIGN PASSED - {dn_key} {pn_key}")
    else:
        st.error(f"❌ DESIGN FAILED - {dn_key} {pn_key}")

    # --- Report ---
    with col_report:
        st.subheader("📋 Design Report")
        st.code(format_report(result), language="text")

    # --- Downoad and follow-up actions ---
    with col_download:
        st.subheader("📥 Export")

        if not result.overall_pass:
            st.warning("Design must pass before export.")
        else:
            # Generate the CAD model once
            with st.spinner("Generating CAD model..."):
                try:
                    output = generate_flange_from_result(result)
                    step_path: Path = output["step_path"]
                    stl_path: Path = output["stl_path"]
                except Exception as e:
                    st.error(f"❌ CAD generation failed: {e}")
                    st.stop()

            # STEP download
            with open(step_path, "rb") as f:
                st.download_button(
                    "Download STEP",
                    data=f,
                    file_name=step_path.name,
                    mime="application/step",
                    use_container_width=True
                )

            # STL download
            with open(stl_path, "rb") as f:
                st.download_button(
                    "Download STL",
                    data=f,
                    file_name=stl_path.name,
                    mime="application/sla",
                    use_container_width=True
                )

            # Cost breakdown
            st.markdown("---")
            st.subheader("💰 Cost Analysis")
            try:
                breakdown = estimate_cost(result)
                st.metric("Mass", f"{breakdown.mass_kg:.2f} kg")
                st.metric(
                    "Estimated cost",
                    f"{breakdown.finished_part_cost:,.2f} {breakdown.currency}"
                )
                with st.expander("Show detailed breakdown"):
                    st.code(breakdown.format_report(), language="text")
            except Exception as e:
                st.warning(f"Cost analysis failed: {e}")

            # --- Optional 3D preview ---
            st.markdown("---")
            st.subheader("🖼️ 3D Preview")
            try:
                # Render off-screen, capture PNG, display in Streamlit
                pv_mesh = load_flange_mesh(stl_path)
                if pv_mesh is not None:
                    plotter = pv.Plotter(off_screen=True, window_size=(600, 400)) # type: ignore
                    plotter.add_mesh(
                        pv_mesh,
                        color="silver",
                        smooth_shading=True,
                        specular=0.4,
                        specular_power=15
                    )
                    plotter.view_isometric() # type: ignore
                    plotter.camera.zoom(1.2)
                    img = plotter.screenshot(return_img=True)
                    st.image(img, caption=f"{dn_key} {pn_key}", use_container_width=True)
                    plotter.close()

            except Exception as e:
                st.info(f"3D preview unavailable: {e}")

else:
    with col_report:
        st.info("👈 Set the design parameters in the sidebar and click **Run Design**.")

# ============================================================================
# 3. FOOTER
# ============================================================================
st.markdown("---")
st.caption(
    "**Smart Pressure Flange Generator** · "
    "EN 1092-1 Type 11 · "
    "Standards-based design with temperature derating · "
    "Not a substitute for final engineering verification."
)