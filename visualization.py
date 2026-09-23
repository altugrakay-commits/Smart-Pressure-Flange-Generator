"""
visualization.py - PyVista rendering for the Smart Pressure Flange Generator
============================================================================

This module loads the exported STL of a flange and renders it with PyVista,
overlaying:
    - The key dimensional annotations (D, K, thickness, hub height, bore)
    - The IADC-style legend for the material
    - Isometric view with axes

References
----------
- PyVista documentation: https://docs.pyvista.org/
- trimesh documentation: https://trimesh.org/
"""

from pathlib import Path
from typing import Optional

import pyvista as pv
import trimesh

from config import OUT_DIR

# ============================================================================
# 1. LOAD AND PREPARE THE MESH
# ============================================================================

def load_flange_mesh(stl_path: Path) -> Optional[pv.PolyData]:

    """
    Load an STL file with trimesh and wrap it as a PyVista PolyData object.
    
    Parameters
    ----------
    stl_path : Path
        Path to the STL file exported by cad_generator.py.
    
    Returns
    -------
    pv.PolyData or None
    """

    if not stl_path.exists():
        print(f"⚠️ STL not found: {stl_path}")
        return None

    mesh = trimesh.load_mesh(str(stl_path))
    if mesh.is_empty:
        print(f"⚠️ STL is empty: {stl_path}")
        return None

    return pv.wrap(mesh)

# ============================================================================
# 2. RENDER THE FLANGE
# ============================================================================

def visualize_flange(
    stl_path: Path,
    title: Optional[str] = None,
    show: bool = True,
    screenshot_path: Optional[Path] = None
) -> Optional[pv.Plotter]:
    
    """
    Render the flange with PyVista.
    
    Parameters
    ----------
    stl_path : Path
        Path to the STL file.
    title : str, optional
        Title overlaid on the render. If None, auto-generated from filename.
    show : bool
        If True, opens the interactive window.
    screenshot_path : Path, optional
        If provided, saves a PNG to the render.
    
    Returns
    -------
    pv.Plotter or None
    """

    pv_mesh = load_flange_mesh(stl_path)
    if pv_mesh is None:
        return None

    # Derive a title if none was provided.
    if title is None:
        title = stl_path.stem.replace("_", " ")
    plotter = pv.Plotter()

    # --- Body: metallic grey, no edges (looks smoother) ---
    plotter.add_mesh(
        pv_mesh,
        color="silver",
        smooth_shading=True,
        specular=0.4,
        specular_power=15,
        show_edges=False
    )

    # --- Optional: show a subtle wirefram overlay for clarity ---
    plotter.add_mesh(
        pv_mesh,
        style="wireframe",
        color="dim_gray",
        line_width=0.3,
        opacity=0.3
    )

    # --- Axes and view ---
    plotter.add_text(
        title,
        position="upper_left",
        font_size=12,
        color="black"
    )
    plotter.add_axes()          # type: ignore
    plotter.view_isometric()    # type: ignore
    plotter.camera.zoom(1.2)

    # --- Optional screenshot ---
    if screenshot_path is not None:
        was_off_screen = plotter.off_screen
        plotter.off_screen = True
        plotter.screenshot(str(screenshot_path))
        print(f"✅ Screenshot saved to: {screenshot_path}")
        plotter.off_screen = was_off_screen

    if show:
        plotter.show()

# ============================================================================
# 3. OPTIONAL: SIDE-BY-SIDE COMPARISON OF TWO FLANGES
# ============================================================================

def visualize_flange_pair(
        stl_path_left: Path,
        stl_path_right: Path,
        label_left: str = "Design A",
        label_right: str = "Design B",
        show: bool = True
) -> Optional[pv.Plotter]:
    
    """
    Render two flange STLs side by side for comparison. 
    Useful for comparing two DN/PN classes.
    """

    mesh_left = load_flange_mesh(stl_path_left)
    mesh_right = load_flange_mesh(stl_path_right)
    if mesh_left is None or mesh_right is None:
        return None

    plotter = pv.Plotter(shape=(1,2))

    # Left subplot
    plotter.subplot(0,0)
    plotter.add_mesh(mesh_left, color="silver", smooth_shading=True)
    plotter.add_text(label_left, position="upper_left", font_size=10)
    plotter.add_axes()          # type: ignore
    plotter.view_isometric()    # type: ignore

    # Right subplot
    plotter.subplot(0,1)
    plotter.add_mesh(mesh_right, color="light_steel_blue", smooth_shading=True)
    plotter.add_text(label_right, position="upper_left", font_size=10)
    plotter.add_axes()          # type: ignore
    plotter.view_isometric()    # type: ignore

    if show:
        plotter.show()

    return plotter

# ============================================================================
# 4. SELF-TEST
# ============================================================================

if __name__ == "__main__":
    visualize_flange(
        stl_path=OUT_DIR / "flange_DN50_PN16.stl", 
        screenshot_path=OUT_DIR / "flange_DN50_PN16_screenshot.png",
        show=True)