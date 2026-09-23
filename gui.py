"""
gui.py - tkinter interface for the Smart Pressure Flange Generator
==================================================================

This module provides a desktop GUI that lets the user:
    1. Pick DN, PN, temperature, pressure, material, bolt material, gasket
    2. Run the mechanical design calculation (engine.FlangeDesigner)
    3. View the resulting design report (geometry, pressure rating,
       thickness, hoop stress, bolt analysis, rigidity)
    4. Generate the CAD model (cad_generator.build_flange_geometry)
    5. Preview it in PyVista (visualization.visualize_flange)
    6. Export STEP and STL files
    7. See the weight and cost breakdown (cost_analysis.estimate_cost)

The GUI uses only tkinter (built into Python) — no extra dependencies.

Usage
-----
    python gui.py
or
    python main.py --gui
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path

from config import (
    EN1092_DIMENSIONS,
    STANDARD_MATERIALS,
    OUT_DIR,
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
from visualization import visualize_flange
from cost_analysis import estimate_cost


# ============================================================================
# 0. HELPER FUNCTIONS
# ============================================================================

def _pretty_bolt_name(key: str) -> str:
    return BOLT_MATERIALS[key]["name"]

def _pretty_gasket_name(key: str) -> str:
    return GASKET_TYPES[key]["name"]

def _pretty_material_name(key: str) -> str:
    return STANDARD_MATERIALS[key]["name"]

def _dn_from_label(label: str) -> str:
    """Extract 'DN50' from 'DN50 (50 mm)'."""
    return label.split()[0]

def _pn_from_label(label: str) -> str:
    """Extract 'PN16' from 'PN16 (1.6 MPa)'."""
    return label.split()[0]

# ============================================================================
# 1. MAIN GUI CLASS
# ============================================================================

class FlangeDesignerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Smart Pressure Flange Generator")
        self.root.geometry("780x820")

        # State: last successful design result (used by Preview/Export/Cost)
        self.last_result = None

        # Build the widget layout
        self._build_widgets()
        self._on_dn_changed()   # populate PN dropdown for the default DN

    # ------------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------------
    def _build_widgets(self):
        # --- Header ---
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")
        ttk.Label(
            header,
            text="Smart Pressure Flange Generator",
            font=("TkDefaultFont", 14, "bold")
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="EN 1092-1 Type 11 welding-neck flange with temperature derating",
            font=("TkDefaultFont", 9, "italic")
        ).pack(anchor="w")

        # --- Input frame ---
        input_frame = ttk.LabelFrame(self.root, text="Design Inputs", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        # DN
        ttk.Label(input_frame, text="DN size").grid(row=0, column=0, sticky="e", padx=5, pady=4)
        self.dn_var = tk.StringVar()
        self.dn_combo = ttk.Combobox(
            input_frame, textvariable=self.dn_var, width=28, state="readonly"
        )
        self.dn_combo.grid(row=0, column=1, sticky="w", padx=5, pady=4)
        self.dn_combo.bind("<<ComboboxSelected>>", lambda e: self._on_dn_changed())

        # PN
        ttk.Label(input_frame, text="PN rating").grid(row=1, column=0, sticky="e", padx=5, pady=4)
        self.pn_var = tk.StringVar()
        self.pn_combo = ttk.Combobox(input_frame, textvariable=self.pn_var, width=28, state="readonly")
        self.pn_combo.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        # Design temperature
        ttk.Label(input_frame, text="Design temperature (°C):").grid(row=2, column=0, sticky="e", padx=5, pady=4)
        self.temp_var = tk.StringVar(value="200")
        ttk.Entry(input_frame, textvariable=self.temp_var, width=30).grid(row=2, column=1, sticky="w", padx=5, pady=4)

        # Opeating Pressure
        ttk.Label(input_frame, text="Operating pressure (MPa):").grid(row=3, column=0, sticky="e", padx=5, pady=4)
        self.press_var = tk.StringVar(value="1.2")
        ttk.Entry(input_frame, textvariable=self.press_var, width=30).grid(row=3, column=1, sticky="w", padx=5, pady=4)

        # Flange material
        ttk.Label(input_frame, text="Flange material:").grid(row=4, column=0, sticky="e", padx=5, pady=4)
        self.mat_var = tk.StringVar()
        self.mat_combo = ttk.Combobox(input_frame, textvariable=self.mat_var, width=28, state="readonly", values=[_pretty_material_name(k) for k in list_standard_materials()])
        self.mat_combo.grid(row=4, column=1, sticky="w", padx=5, pady=4)

        # Bolt material
        ttk.Label(input_frame, text="Bolt material:").grid(row=5, column=0, sticky="e", padx=5, pady=4)
        self.bolt_var = tk.StringVar()
        self.bolt_combo = ttk.Combobox(input_frame, textvariable=self.bolt_var, width=28, state="readonly", values=[_pretty_bolt_name(k) for k in BOLT_MATERIALS.keys()])
        self.bolt_combo.grid(row=5, column=1, sticky="w", padx=5, pady=4)

        # Gasket type
        ttk.Label(input_frame, text="Gasket type:").grid(row=6, column=0, sticky="e", padx=5, pady=4)
        self.gasket_var = tk.StringVar()
        self.gasket_combo = ttk.Combobox(input_frame, textvariable=self.gasket_var, width=28, state="readonly", values=[_pretty_gasket_name(k) for k in GASKET_TYPES.keys()])
        self.gasket_combo.grid(row=6, column=1, sticky="w", padx=5, pady=4)

        # Set sensible defaults
        self.mat_combo.current(0)       # PS50GH
        self.bolt_combo.current(0)      # A193 D7
        self.gasket_combo.current(0)    # Spiral-wound graphite

        # --- Action buttons ---
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x")

        self.run_btn = ttk.Button(btn_frame, text="Run Design", command=self._on_run_design)
        self.run_btn.grid(row=0, column=0, padx=4, pady=4)

        self.preview_btn = ttk.Button(btn_frame, text="Preview Flange", command=self._on_preview)
        self.preview_btn.grid(row=0, column=1, padx=4, pady=4)
        self.preview_btn.state(["disabled"])

        self.export_btn = ttk.Button(btn_frame, text="Export STEP + STL", command=self._on_export)
        self.export_btn.grid(row=0, column=2, padx=4, pady=4)
        self.export_btn.state(["disabled"])

        self.cost_btn = ttk.Button(btn_frame, text="Cost Analysis", command=self._on_cost)
        self.cost_btn.grid(row=0, column=3, padx=4, pady=4)
        self.cost_btn.state(["disabled"])

        # --- Output frame ---
        out_frame = ttk.LabelFrame(self.root, text="Design Report", padding=5)
        out_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.output_text = scrolledtext.ScrolledText(
            out_frame, wrap="word", font=("Consolas", 9), height=28,
        )
        self.output_text.pack(fill="both", expand=True)

        # --- Status bar ---
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(
            self.root, textvariable=self.status_var, relief="sunken", anchor="w",
        ).pack(fill="x", side="bottom")

    # ------------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------------
    def _on_dn_changed(self):
        """When DN changes, repopulate PN dropdown with available ratings."""
        # Show DN labels like "DN50 (50 mm)"
        dn_labels = [f"{dn} ({EN1092_DIMENSIONS[dn]['nominal_bore']:.0f} mm)"
                     for dn in list_dn_sizes()]
        self.dn_combo["values"] = dn_labels
        if not self.dn_var.get() or self.dn_var.get() not in dn_labels:
            self.dn_combo.current(0)

        # Get the DN key (first token)
        dn_key = _dn_from_label(self.dn_var.get())

        # Repopulate PN values
        pn_keys = list_pn_ratings(dn_key)
        pn_labels = [
            f"{pn} ({float(pn.replace('PN','')) * 0.1:.1f} MPa)"
            for pn in pn_keys
        ]
        self.pn_combo["values"] = pn_labels
        # Prefer PN16 if available
        if "PN16" in pn_keys:
            self.pn_combo.current(pn_keys.index("PN16"))
        else:
            self.pn_combo.current(0)

    def _collect_inputs(self) -> DesignInputs:
        """Read the GUI fields and return a DesignInputs object."""
        # Map display labels back to keys
        dn_key = _dn_from_label(self.dn_var.get())
        pn_key = _pn_from_label(self.pn_var.get())

        mat_display = self.mat_var.get()
        mat_key = next((k for k in STANDARD_MATERIALS if _pretty_material_name(k) == mat_display), None,)

        bolt_display = self.bolt_var.get()
        bolt_key = next((k for k in BOLT_MATERIALS if _pretty_bolt_name(k) == bolt_display), None)
 
        gasket_display = self.gasket_var.get()
        gasket_key = next((k for k in GASKET_TYPES if _pretty_gasket_name(k) == gasket_display), None)

        if not all([mat_key, bolt_key, gasket_key]):
            raise ValueError("One or more material keys could not be resolved.")

        return DesignInputs(
            dn=dn_key,
            pn=pn_key,
            design_temperature_c=float(self.temp_var.get()),
            material_key=mat_key,
            bolt_material_key=bolt_key,
            gasket_type=gasket_key,
            operating_pressure_mpa=float(self.press_var.get()),
            verification_method="EN_1092"
        )

    def _on_run_design(self):
        """Run the design calculation and display the report."""
        try:
            inputs = self._collect_inputs()
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return

        self.status_var.set("Running design calculation...")
        self._set_buttons_enabled(False)

        try:
            result = FlangeDesigner(inputs).compute()
            self.last_result = result

            # Print the report
            report_text = format_report(result)
            self._set_output(report_text)

            # Enable follow-up buttons only if the design passed
            if result.overall_pass:
                self.preview_btn.state(["!disabled"])
                self.export_btn.state(["!disabled"])
                self.cost_btn.state(["!disabled"])
                self.status_var.set("Design PASSED. Ready to provide preview or export.")
            else:
                self.preview_btn.state(["disabled"])
                self.export_btn.state(["disabled"])
                self.cost_btn.state(["disabled"])
                self.status_var.set("Design FAILED. See report for details.")

        except Exception as e:
            messagebox.showerror("Design error", str(e))
            self.status_var.set("Design failed with an exception.")

        finally:
            self._set_buttons_enabled(True)

    def _on_preview(self):
        """Generate the CAD model and open it in PyVista"""
        if self.last_result is None:
            return
        self.status_var.set("Generating CAD and opening PyVista...")
        try:
            output = generate_flange_from_result(self.last_result)
            stl_path: Path = output["stl_path"]
            # Launch PyVista in a background thread so that GUI stays responsive.
            threading.Thread(
                target=visualize_flange,
                args=(stl_path,),
                kwargs={"show": True},
                daemon=True
            ).start()
            self.status_var.set(f"Preview launch: {stl_path.name}")
        except Exception as e:
            messagebox.showerror("Preview error", str(e))
            self.status_var.set("Preview failed.")

    def _on_export(self):
        """Generate STEP + STL files and report their paths."""
        if self.last_result is None:
            return
        self.status_var.set("Exporting CAD files...")
        try:
            output = generate_flange_from_result(self.last_result)
            self._append_output(
                f"\n📁 STEP: {output['step_path']}\n"
                f"📁 STL: {output['stl_path']}\n"
            )
            messagebox.showinfo(
                "Export Complete",
                f"STEP: {output['step_path']}\n\nSTL: {output['stl_path']}"
            )
            self.status_var.set("Export complete.")
        except Exception as e:
            messagebox.showerror("Export error", str(e))
            self.status_var.set("Export failed.")

    def _on_cost(self):
        """Run the cost analysis and display it in the output panel."""
        if self.last_result is None:
            return
        self.status_var.set("Estimating cost...")
        try:
            breakdown = estimate_cost(self.last_result)
            self._append_output(breakdown.format_report())
            self.status_var.set("Cost analysis complete.")
        except Exception as e:
            messagebox.showerror("Cost error", str(e))
            self.status_var.set("Cost analysis failed.")

    # ------------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------------

    def _set_output(self, text: str):
        """Replace the entire output text."""
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", text)

    def _append_output(self, text: str):
        """Append text to the missing output."""
        self.output_text.insert("end", text)
        self.output_text.see("end")

    def _set_buttons_enabled(self, enabled: bool):
        """Replace the entire output text."""
        state = ["!disabled"] if enabled else ["disabled"]
        self.run_btn.state(state)
        
        
# ============================================================================
# 2. ENTRY POINT
# ============================================================================
def run_gui():
    """Launch the tkinter GUI. Called from main.py --gui or directly."""
    root = tk.Tk()
    app = FlangeDesignerGUI(root)   # noqa: F841 (kept alive by tkinter)
    root.mainloop()

if __name__ == "__main__":
    run_gui()