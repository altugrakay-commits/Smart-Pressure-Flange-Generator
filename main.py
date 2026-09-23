"""
main.py - Command-line entry point for the Smart Pressure Flange Generator
==========================================================================

This module is the user-facing entry point for the tool. It supports:

    1. Command-line design runs:
           python main.py --dn DN50 --pn PN16 --temp 200 --pressure 1.2
    2. Interactive mode (tkinter GUI):
           python main.py --gui
    3. Export of STEP and STL files:
           python main.py --dn DN80 --pn PN25 --export
    4. Optional PyVista preview:
           python main.py --dn DN50 --pn PN16 --preview

If no arguments are given, the tool prints a short help message. If only
--gui is passed, the tkinter interface is launched and no design is run.

The CLI pipeline performs the following sequence:
    DesignInputs  →  FlangeDesigner.compute()  →  format_report()
                  →  generate_flange_from_result()   (if --export)
                  →  visualize_flange()              (if --preview)
                  →  estimate_cost()                 (if --cost)

Usage examples
--------------
    # Minimal run (defaults: DN50, PN16, 200 °C, 1.2 MPa)
    python main.py

    # Full CLI run with export and cost
    python main.py --dn DN80 --pn PN25 --temp 250 --pressure 1.6 \
                   --material 16Mo3 --export --cost

    # Just launch the GUI
    python main.py --gui
"""

import argparse
import sys
from pathlib import Path

from cad_generator import generate_flange_from_result
from cost_analysis import estimate_cost

from config import OUT_DIR
from visualization import visualize_flange
from gui import run_gui

from config import (
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

# ============================================================================
# 1. ARGUMENT PARSER
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Smart Pressure Flange Generator - CLI entry point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py --gui\n"
            "  python main.py --dn DN50 --pn PN16 --temp 200 --pressure 1.2\n"
            "  python main.py --dn DN80 --pn PN25 --material 16Mo3 --export --cost\n"
        ),
    )

    # --- Mode selection ---
    parser.add_argument(
        "--gui", action="store_true",
        help="Launch the tkinter GUI instead of running a single design pass"
    )

    # --- Design inputs ---
    parser.add_argument(
        "--dn", type=str, default="DN50",
        choices=list_dn_sizes(),
        help="Nominal size (e.g. DN50)."
    )

    parser.add_argument(
        "--pn", type=str, default="PN16",
        help="Pressure rating (e.g. PN16). Validated against the DN."
    )

    parser.add_argument(
        "--temp", type=float, default=200,
        help="Design temperature in °C (default: 200)."
    )

    parser.add_argument(
        "--pressure", type=float, default=1.2,
        help="Operating pressure in MPa (default: 1.2)."
    )

    parser.add_argument(
        "--material", type=str, default="P250GH",
        help="Flange material key (default: P250GH)."
    )

    parser.add_argument(
        "--bolt", type=str, default="A193_B7",
        choices=list(BOLT_MATERIALS.keys()),
        help="Bolt material key (default: A193_B7)."
    )

    parser.add_argument(
        "--gasket", type=str, default="spiral_wound_graphite",
        choices=list(GASKET_TYPES.keys()),
        help="Gasket type key (default: spiral_wound_graphite)."
    )

    parser.add_argument(
        "--verification", type=str, default="EN_1092",
        choices=["EN_1092", "ASME_VIII_App2"],
        help="Design philosophy (default: EN_1092)."
    )

    # ---Output actions ---
    parser.add_argument(
        "--export", action="store_true",
        help="Export the flange as STEP and STL files."
    )

    parser.add_argument(
        "--preview", action="store_true",
        help="Open the flange in a PyVista window."
    )

    parser.add_argument(
        "--cost", action="store_true",
        help="Include a weight and cost breakdown in the report."
    )

    parser.add_argument("--no-report", action="store_true",
        help="Suppress the text report (useful when scripting)."
    )

    return parser

# ============================================================================
# 2. CLI PIPELINE
# ============================================================================

def run_design(args) -> int:

    """
    Execute the CLI design pipeline.

    Sequence
    --------
    1. Build DesignInputs from the parsed args.
    2. Run the mechanical design calculation.
    3. Print the text report (unless --no-report).
    4. If --export, write STEP + STL.
    5. If --cost, print the cost breakdown.
    6. If --preview, open PyVista.

    Returns
    -------
    int
        Exit code: 0 on success, 1 on failure.
    """

    # --- 1. Build the DesignInputs ---

    try:
        inputs = DesignInputs(
            dn=args.dn,
            pn=args.pn,
            design_temperature_c=args.temp,
            material_key=args.material,
            bolt_material_key=args.bolt,
            gasket_type=args.gasket,
            operating_pressure_mpa=args.pressure,
            verification_method=args.verification
        )
    except Exception as e:
        print(f"❌ Invalid inputs: {e}", file=sys.stderr)
        return 1
    
    # --- 2. Run the design ---

    try:
        result = FlangeDesigner(inputs).compute()
    except Exception as e:
        print(f"❌ Design calculation failed: {e}", file=sys.stderr)
        return 1
    
    # --- 3. Print the report ---

    if not args.no_report:
        print(format_report(result))
    
    # --- 4. Export ---

    if args.export:
        if not result.overall_pass:
            print(
                "\n❌ Design failed. Export skipped.\n"
                "   Fix the errors above before exporting.",
                file=sys.stderr
            )
        else:
            try:
                generate_flange_from_result(result)
            except Exception as e:
                print(f"❌ Export failed: {e}", file=sys.stderr)

    # --- 5. Cost breakdown ---

    if args.cost:
        if not result.overall_pass:
            print("\n❌ Design failed. Cost skipped.", file=sys.stderr)
        else:
            try:
                breakdown = estimate_cost(result)
                print(breakdown.format_report())
            except Exception as e:
                print(f"❌ Cost analysis failed: {e}", file=sys.stderr)
    
    # --- 6. PyVista preview ---
    
    if args.preview:
        if not result.overall_pass:
            print("\n❌ Design failed. Preview skipped.", file=sys.stderr)
        else:
            try:
                output = generate_flange_from_result(result)
                stl_path: Path = output["stl_path"]
                visualize_flange(stl_path, show=True)
            except Exception as e:
                print(f"❌ Preview failed: {e}", file=sys.stderr)

    return 0 if result.overall_pass else 1

# ============================================================================
# 3. ENTRY POINT
# ============================================================================

def main():
    """Parses arguments and dispatch to the GUI or CLI pipeline."""
    parser = build_parser()
    args = parser.parse_args()

    # --- No arguments at all → show help ---
    if len(sys.argv) == 1:
        parser.print_help()
        print("\nHint: use --gui to launch the interactive interface,")
        print("         or provide --dn / --pn / --temp to run a design pass.")
        return

    # --- GUI mode ---
    if args.gui:
        run_gui()
        return

    # -- CLI mode ---
    exit_code = run_design(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()