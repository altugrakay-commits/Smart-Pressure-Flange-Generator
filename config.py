"""
config.py - Central configuration for the Smart Pressure Flange Generator
=========================================================================

This module contains all standards, tables, and material data used by the 
flange design tool. It is the single source truth for:
    1. EN 1092-1 flange dimensions (DN x PN combinations).
    2. Temperature derating factors for standard pressure-vessel steels.
    3. Standard material database (used by the core design layer).
    4. CSV-derived material database (used by the optional ML screening layer).
    5. Physics constants and unit-converstion helpers.

References
----------
 - EN 1092-1: Flanges and their joints - Circular flanges for pipes, valves, 
   fittings and accessories, PN designated.
 - EN 10222-2: Steel forgings for pressure purposes - Part 2:
   Ferritic and martensitic steels with specified elevated temperature properties.
 - ASME B16.5: Pipe Flanges and Flanged Fittings.
 - ASME BPVC: Section VIII: Div. 1: Rules for Construction of Pressure Vessels.

⚠️ IMPORTANT
-------------
The dimension and derating tables below are representative and match the EN1092-1 
standard for the listed combinations. For production work, ALWAYS verify against the 
latest revision of the standard (EN 1092-1: 2019 or newer).
"""

from pathlib import Path

# ================
# 0. PROJECT PATHS
# ================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"
OUT_DIR = BASE_DIR / "Output"
MODEL_DIR = BASE_DIR / "Models"

for d in (DATA_DIR, OUT_DIR, MODEL_DIR):
    d.mkdir(exist_ok=True)

# ======================================================================
# 1. EN 1092-1 FLANGE DIMENSIONS
# ======================================================================
# for each DN x PN combination, the following fields are provided:
# D             - Flange outside diameter                       (mm)
# K             - Bolt circle diameter                          (mm)
# L             - Bolt hole diameter                            (mm)
# n_bolts       - Number of bolts                               (-)
# bolt_size     - Metric bolt designations (e.g., "M16")        (-)
# thickness     - Flange thickness at the hub                   (mm)
# hub_d         - Hub diameter                                  (mm)
# hub_h         - Hub height                                    (mm)
# bore          - Nominal bore (inner diameter)                 (mm)
# 
# NOTE: Bore is the nominal DN in mm. For a "loose" flange, the bore is 
# larger than the pipe OD; for a welding-neck flange, the bore matches  
# the pipe OD. Here we report the nominal DN bore value.
# ======================================================================

EN1092_DIMENSIONS = {
    # -------------------- DN 15 (1/2") --------------------
    "DN15": {
        "nominal_bore": 15,
        "PN6": {"D": 80, "K": 55, "L": 11, "n_bolts": 4, "bolt_size": "M10", "thickness": 12, "hub_d": 30, "hub_h": 30},
        "PN10": {"D": 95, "K": 65, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 14, "hub_d": 30, "hub_h": 30},
        "PN16": {"D": 95, "K": 65, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 16, "hub_d": 30, "hub_h": 30},
        "PN25": {"D": 95, "K": 65, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 16, "hub_d": 30, "hub_h": 30},
        "PN40": {"D": 95, "K": 65, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 16, "hub_d": 30, "hub_h": 30}
    },
    # -------------------- DN 20 (3/4") --------------------
    "DN20": {
    "nominal_bore": 20,
        "PN6": {"D": 90, "K": 65, "L": 11, "n_bolts": 4, "bolt_size": "M10", "thickness": 14, "hub_d": 38, "hub_h": 32},
        "PN10": {"D": 105, "K": 75, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 16, "hub_d": 38, "hub_h": 32},
        "PN16": {"D": 105, "K": 75, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 18, "hub_d": 38, "hub_h": 32},
        "PN25": {"D": 105, "K": 75, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 18, "hub_d": 38, "hub_h": 32},
        "PN40": {"D": 105, "K": 75, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 18, "hub_d": 38, "hub_h": 32}
    },
    # -------------------- DN 25 (1") --------------------
    "DN25": {
    "nominal_bore": 25,
        "PN6": {"D": 100, "K": 75, "L": 11, "n_bolts": 4, "bolt_size": "M10", "thickness": 14, "hub_d": 42, "hub_h": 32},
        "PN10": {"D": 115, "K": 85, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 16, "hub_d": 42, "hub_h": 32},
        "PN16": {"D": 115, "K": 85, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 18, "hub_d": 42, "hub_h": 32},
        "PN25": {"D": 115, "K": 85, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 18, "hub_d": 42, "hub_h": 32},
        "PN40": {"D": 115, "K": 85, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 18, "hub_d": 42, "hub_h": 32}
    },
    # -------------------- DN 32 (1.25") --------------------
    "DN32": {
    "nominal_bore": 32,
        "PN6": {"D": 120, "K": 90, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 16, "hub_d": 50, "hub_h": 35},
        "PN10": {"D": 140, "K": 100, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 18, "hub_d": 50, "hub_h": 35},
        "PN16": {"D": 140, "K": 100, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 18, "hub_d": 50, "hub_h": 35},
        "PN25": {"D": 140, "K": 100, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 18, "hub_d": 50, "hub_h": 35},
        "PN40": {"D": 140, "K": 100, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 18, "hub_d": 50, "hub_h": 35}
    },
    # -------------------- DN 40 (1.5") --------------------
    "DN40": {
    "nominal_bore": 40,
        "PN6": {"D": 130, "K": 100, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 16, "hub_d": 58, "hub_h": 38},
        "PN10": {"D": 150, "K": 110, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 18, "hub_d": 58, "hub_h": 38},
        "PN16": {"D": 150, "K": 110, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 18, "hub_d": 58, "hub_h": 38},
        "PN25": {"D": 150, "K": 110, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 20, "hub_d": 58, "hub_h": 40},
        "PN40": {"D": 150, "K": 110, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 20, "hub_d": 58, "hub_h": 40}
    },
    # -------------------- DN 50 (2") --------------------
    "DN50": {
    "nominal_bore": 50,
        "PN6": {"D": 140, "K": 110, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 16, "hub_d": 68, "hub_h": 40},
        "PN10": {"D": 165, "K": 125, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 18, "hub_d": 68, "hub_h": 42},
        "PN16": {"D": 165, "K": 125, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 20, "hub_d": 68, "hub_h": 45},
        "PN25": {"D": 165, "K": 125, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 20, "hub_d": 68, "hub_h": 48},
        "PN40": {"D": 165, "K": 125, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 20, "hub_d": 72, "hub_h": 50}
    },
    # -------------------- DN 65 (2.5") --------------------
    "DN65": {
    "nominal_bore": 65,
        "PN6": {"D": 160, "K": 130, "L": 14, "n_bolts": 4, "bolt_size": "M12", "thickness": 16, "hub_d": 80, "hub_h": 42},
        "PN10": {"D": 185, "K": 145, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 18, "hub_d": 80, "hub_h": 45},
        "PN16": {"D": 185, "K": 145, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 20, "hub_d": 80, "hub_h": 48},
        "PN25": {"D": 185, "K": 145, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 22, "hub_d": 85, "hub_h": 52},
        "PN40": {"D": 185, "K": 145, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 22, "hub_d": 85, "hub_h": 55}
    },
    # -------------------- DN 80 (3") --------------------
    "DN80": {
    "nominal_bore": 80,
        "PN6": {"D": 190, "K": 150, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 18, "hub_d": 95, "hub_h": 45},
        "PN10": {"D": 200, "K": 160, "L": 18, "n_bolts": 8, "bolt_size": "M16", "thickness": 20, "hub_d": 95, "hub_h": 48},
        "PN16": {"D": 200, "K": 160, "L": 18, "n_bolts": 8, "bolt_size": "M16", "thickness": 22, "hub_d": 95, "hub_h": 52},
        "PN25": {"D": 200, "K": 160, "L": 18, "n_bolts": 8, "bolt_size": "M16", "thickness": 24, "hub_d": 100, "hub_h": 55},
        "PN40": {"D": 200, "K": 160, "L": 18, "n_bolts": 8, "bolt_size": "M16", "thickness": 24, "hub_d": 100, "hub_h": 58}
    },
    # -------------------- DN 100 (4") --------------------
    "DN100": {
    "nominal_bore": 100,
        "PN6": {"D": 210, "K": 170, "L": 18, "n_bolts": 4, "bolt_size": "M16", "thickness": 18, "hub_d": 115, "hub_h": 48},
        "PN10": {"D": 220, "K": 180, "L": 18, "n_bolts": 8, "bolt_size": "M16", "thickness": 20, "hub_d": 115, "hub_h": 52},
        "PN16": {"D": 220, "K": 180, "L": 18, "n_bolts": 8, "bolt_size": "M16", "thickness": 22, "hub_d": 115, "hub_h": 55},
        "PN25": {"D": 235, "K": 190, "L": 22, "n_bolts": 8, "bolt_size": "M20", "thickness": 24, "hub_d": 125, "hub_h": 60},
        "PN40": {"D": 235, "K": 190, "L": 22, "n_bolts": 8, "bolt_size": "M20", "thickness": 24, "hub_d": 125, "hub_h": 62}
    },
    # -------------------- DN 125 (5") --------------------
    "DN125": {
    "nominal_bore": 125,
        "PN6": {"D": 240, "K": 200, "L": 18, "n_bolts": 8, "bolt_size": "M16", "thickness": 20, "hub_d": 140, "hub_h": 52},
        "PN10": {"D": 250, "K": 210, "L": 18, "n_bolts": 8, "bolt_size": "M16", "thickness": 22, "hub_d": 140, "hub_h": 55},
        "PN16": {"D": 250, "K": 210, "L": 18, "n_bolts": 8, "bolt_size": "M16", "thickness": 24, "hub_d": 140, "hub_h": 58},
        "PN25": {"D": 270, "K": 220, "L": 26, "n_bolts": 8, "bolt_size": "M24", "thickness": 26, "hub_d": 150, "hub_h": 65},
        "PN40": {"D": 270, "K": 220, "L": 26, "n_bolts": 8, "bolt_size": "M24", "thickness": 28, "hub_d": 155, "hub_h": 68}
    },
    # -------------------- DN 150 (6") --------------------
    "DN150": {
    "nominal_bore": 150,
        "PN6": {"D": 265, "K": 225, "L": 18, "n_bolts": 8, "bolt_size": "M16", "thickness": 20, "hub_d": 165, "hub_h": 55},
        "PN10": {"D": 285, "K": 240, "L": 22, "n_bolts": 8, "bolt_size": "M20", "thickness": 22, "hub_d": 165, "hub_h": 58},
        "PN16": {"D": 285, "K": 240, "L": 22, "n_bolts": 8, "bolt_size": "M20", "thickness": 24, "hub_d": 165, "hub_h": 62},
        "PN25": {"D": 300, "K": 250, "L": 26, "n_bolts": 8, "bolt_size": "M24", "thickness": 28, "hub_d": 180, "hub_h": 70},
        "PN40": {"D": 300, "K": 250, "L": 26, "n_bolts": 8, "bolt_size": "M24", "thickness": 28, "hub_d": 185, "hub_h": 75}
    },
    # -------------------- DN 200 (8") --------------------
    "DN200": {
    "nominal_bore": 200,
        "PN6": {"D": 320, "K": 280, "L": 18, "n_bolts": 8, "bolt_size": "M16", "thickness": 22, "hub_d": 220, "hub_h": 62},
        "PN10": {"D": 340, "K": 295, "L": 22, "n_bolts": 8, "bolt_size": "M20", "thickness": 24, "hub_d": 220, "hub_h": 65},
        "PN16": {"D": 340, "K": 295, "L": 22, "n_bolts": 12, "bolt_size": "M20", "thickness": 26, "hub_d": 220, "hub_h": 70},
        "PN25": {"D": 360, "K": 310, "L": 26, "n_bolts": 12, "bolt_size": "M24", "thickness": 30, "hub_d": 235, "hub_h": 80},
        "PN40": {"D": 375, "K": 320, "L": 30, "n_bolts": 12, "bolt_size": "M27", "thickness": 34, "hub_d": 240, "hub_h": 88}
    },
    # -------------------- DN 250 (10") --------------------
    "DN250": {
    "nominal_bore": 250,
        "PN6": {"D": 375, "K": 335, "L": 18, "n_bolts": 12, "bolt_size": "M16", "thickness": 24, "hub_d": 270, "hub_h": 68},
        "PN10": {"D": 395, "K": 350, "L": 22, "n_bolts": 12, "bolt_size": "M20", "thickness": 26, "hub_d": 270, "hub_h": 72},
        "PN16": {"D": 405, "K": 355, "L": 22, "n_bolts": 12, "bolt_size": "M20", "thickness": 28, "hub_d": 270, "hub_h": 78},
        "PN25": {"D": 425, "K": 370, "L": 30, "n_bolts": 12, "bolt_size": "M27", "thickness": 32, "hub_d": 290, "hub_h": 88},
        "PN40": {"D": 445, "K": 385, "L": 33, "n_bolts": 12, "bolt_size": "M30", "thickness": 38, "hub_d": 295, "hub_h": 95}
    },
    # -------------------- DN 300 (12") --------------------
    "DN300": {
    "nominal_bore": 300,
        "PN6": {"D": 440, "K": 395, "L": 22, "n_bolts": 12, "bolt_size": "M20", "thickness": 24, "hub_d": 320, "hub_h": 72},
        "PN10": {"D": 445, "K": 400, "L": 22, "n_bolts": 12, "bolt_size": "M20", "thickness": 26, "hub_d": 320, "hub_h": 75},
        "PN16": {"D": 460, "K": 410, "L": 22, "n_bolts": 12, "bolt_size": "M20", "thickness": 28, "hub_d": 320, "hub_h": 82},
        "PN25": {"D": 485, "K": 430, "L": 30, "n_bolts": 16, "bolt_size": "M27", "thickness": 34, "hub_d": 340, "hub_h": 95},
        "PN40": {"D": 510, "K": 450, "L": 33, "n_bolts": 16, "bolt_size": "M30", "thickness": 42, "hub_d": 345, "hub_h": 105}
    },
}

# ============================================================================
# 2. TEMPERATURE DERATING FACTORS
# ============================================================================
# Fraction of the room-temperature (20°C) allowable stress at elevated
# temperatures. Derived from EN 10222-2 and ASME BPVC Section II Part D.
# 
# The first column is the temperature in °C; the second is the stress 
# ratio (σ_allowable(T) / σ_allowable(20°C))
# ============================================================================

DERATING_TABLES = {
    "carbon_steel": {
        # Representative of P250GH (=A105) - the most common flange material
        "name": "Carbon Steel (P250GH / A105)",
        "curve": [
            (-20, 1.00), (20, 1.00), (50, 0.97), (100, 0.93),
            (150, 0.88), (200, 0.83), (250, 0.79), (300, 0.73),
            (350, 0.68), (400, 0.62), (450, 0.55)
        ],
        "max_temp": 450
    },
    "alloy_steel": {
        # Representative of 16Mo3 - a common elevated-temperature flange steel
        "name": "Alloy Steel (16Mo3)",
        "curve": [
            (-20, 1.00), (20, 1.00), (50, 0.98), (100, 0.95),
            (150, 0.92), (200, 0.89), (250, 0.86), (300, 0.83),
            (350, 0.80), (400, 0.77), (450, 0.74), (500, 0.70)
        ],
        "max_temp": 500
    },
    "stainless_304": {
        "name": "Stainless Steel (304 / 1.4301)",
        "curve": [
            (-196, 1.00), (-100, 1.00), (20, 1.00), (100, 0.96),
            (200, 0.92), (300, 0.88), (400, 0.85), (500, 0.82),
            (600, 0.79)
        ],
        "max_temp": 600
    },
    "stainless_316": {
        "name": "Stainless Steel (316 / 1.4401)",
        "curve": [
            (-196, 1.00), (-100, 1.00), (20, 1.00), (100, 0.96),
            (200, 0.93), (300, 0.90), (400, 0.88), (500, 0.86),
            (600, 0.84)
        ],
        "max_temp": 600
    },
}

# ============================================================================
# 3. STANDARD MATERIAL DATABASE (Core Design Layer)
# ============================================================================
# These are the materials accepted by EN 1092-1 for pressure service.
# The "derating_key" points to the appropriate derating curve in
# DERATING_TABLES. "yield_strength_rt" is the room-temperature minimum
# yield strength (MPa). "allowable_rt" is the allowable stress at 20°C
# (MPa) per EN 10222-2, already including the safety factor.
# ============================================================================

STANDARD_MATERIALS = {
    "P250GH": {
        "name": "Carbon Steel (P250GH)",
        "standard": "EN 10222-2",
        "derating_key": "carbon_steel",
        "yield_strength_rt": 250,
        "uts_rt": 450,
        "allowable_rt": 140,
        "density_g_cm3": 7.85,
        "cost_usd_per_kg": 1.20,
        "min_temp": -20,
        "max_temp": 450
    },
    "P265GH": {
        "name": "Carbon Steel (P265GH)",
        "standard": "EN 10222-2",
        "derating_key": "carbon_steel",
        "yield_strength_rt": 265,
        "uts_rt": 470,
        "allowable_rt": 148,
        "density_g_cm3": 7.85,
        "cost_usd_per_kg": 1.25,
        "min_temp": -20,
        "max_temp": 450
    },
    "16Mo3": {
        "name": "Alloy Steel (16Mo3)",
        "standard": "EN 10222-2",
        "derating_key": "alloy_steel",
        "yield_strength_rt": 275,
        "uts_rt": 450,
        "allowable_rt": 155,
        "density_g_cm3": 7.85,
        "cost_usd_per_kg": 2.10,
        "min_temp": -20,
        "max_temp": 500
    },
    "1.4301": {
        "name": "Stainless Steel (304 / 1.4301)",
        "standard": "EN 10222-5",
        "derating_key": "stainless_304",
        "yield_strength_rt": 190,
        "uts_rt": 500,
        "allowable_rt": 130,
        "density_g_cm3": 7.90,
        "cost_usd_per_kg": 4.50,
        "min_temp": -196,
        "max_temp": 600
    },
    "1.4401": {
        "name": "Stainless Steel (316 / 1.4401)",
        "standard": "EN 10222-5",
        "derating_key": "stainless_316",
        "yield_strength_rt": 200,
        "uts_rt": 500,
        "allowable_rt": 140,
        "density_g_cm3": 8.00,
        "cost_usd_per_kg": 4.80,
        "min_temp": -196,
        "max_temp": 600
    },
}

# ============================================================================
# 4. CSV-DERIVED MATERIAL DATABASE (Optional ML Screening Layer)
# ============================================================================
# These entries come from the flange_generator.csv file and are used ONLY
# by the optional ML screening layer. They are NOT certified for pressure
# equipment and should be treated as indicative only.
#
# Each entry has:
#   chemistry     - C, Si, Mn, Cr, Ni, Mo (weight percent)
#   heat_treat    - (temp_°C, time_hours) tuple
#   yield_rt      - Room-temperature yield strength from the dataset (MPa)
#   uts_rt        - Room-temperature UTS from the dataset (MPa)
#   hardness_hb   - Brinell hardness from the dataset
#   source        - Where the data came from
# ============================================================================

CSV_MATERIALS = {
    "100Cr6_803D_QTb": {
        "name": "100Cr6 (803D_QTb)",
        "chemistry": {"C": 1.015, "Si": 0.275, "Mn": 0.35, "Cr": 1.50, "Ni": 0.125, "Mo": 0.04},
        "heat_treat": (860, 5),
        "yield_rt": 2000,
        "uts_rt": 2200,
        "hardness_hb": 615,
        "source": "flange_generator.csv"
    },
    "100Cr6_803D_SA": {
        "name": "100Cr6 (803D_SA)",
        "chemistry": {"C": 1.015, "Si": 0.275, "Mn": 0.35, "Cr": 1.50, "Ni": 0.125, "Mo": 0.04},
        "heat_treat": (820, 10),
        "yield_rt": 410,
        "uts_rt": 700,
        "hardness_hb": 210,
        "source": "flange_generator.csv"
    },
    "S35532_AR": {
        "name": "S35532_AR (as_rolled)",
        "chemistry": {"C": 0.13, "Si": 0.20, "Mn": 0.35, "Cr": 0.05, "Ni": 0.10, "Mo": 0.02},
        "heat_treat": (20, 0),
        "yield_rt": 355,
        "uts_rt": 490,
        "hardness_hb": 150,
        "source": "flange_generator.csv"
    },
    "C45_QT": {
        "name": "C45 (quenched & tempered)",
        "chemistry": {"C": 0.48, "Si": 0.25, "Mn": 0.65, "Cr": 0.15, "Ni": 0.15, "Mo": 0.05},
        "heat_treat": (850, 1),
        "yield_rt": 430,
        "uts_rt": 650,
        "hardness_hb": 190,
        "source": "flange_generator.csv"
    },
    "16MnCr5_U": {
        "name": "16MnCr5 (untreated)",
        "chemistry": {"C": 0.165, "Si": 0.25, "Mn": 1.175, "Cr": 0.975, "Ni": 0.10, "Mo": 0.05},
        "heat_treat": (20, 0),
        "yield_rt": 483,
        "uts_rt": 793,
        "hardness_hb": 230,
        "source": "flange_generator.csv"
    },
}

# ========================================================================
# 5. PHYSICS CONSTANTS
# ========================================================================

GRAVITY = 9.81                                  # m/s²
WATER_DENSITY = 1000.0                          # kg/m³
STEEL_DENSITY_DEFAULT = 7850.0                  # kg/m³

# Pressure unit conversions
BAR_TO_MPA = 0.1
MPA_TO_BAR = 10.0
PIS_TO_BAR = 0.0689476
BAR_TO_PSI = 14.5038

# Length unit conversions
MM_TO_M = 0.001
MM3_TO_CM3 = 0.001
MM3_TO_M3 = 1e-9

# Hoop stress formula safety factors (per EN 13445 / ASME VIII)
WELD_EFFICIENCY_FULL = 1.00         # For seamless or 100% radiographed welds
WELD_EFFICIENCY_PARTIAL = 0.85      # For spot-radiographed welds
WELD_EFFICIENCY_NONE = 0.70         # For non-radiographed welds
DESIGN_SAFETY_FACTOR = 1.5          # Typical for pressure equipment

# ============================================================================
# 6. HELPER FUNCTIONS
# ============================================================================

def list_dn_sizes():
    """Return the list of DN sizes available in the dimension table."""
    return sorted(EN1092_DIMENSIONS.keys(), key=lambda s: EN1092_DIMENSIONS[s]["nominal_bore"])

def list_pn_ratings(dn: str):
    """Return the list of PN ratings available for a given DN."""
    if dn not in EN1092_DIMENSIONS:
        return []
    return [k for k in EN1092_DIMENSIONS[dn].keys() if k.startswith("PN")]

def list_standard_materials():
    """Return the list of standard (EN-certified) material keys."""
    return list(STANDARD_MATERIALS.keys())

def list_csv_materials():
    """Return the list of CSV-derived material keys (screening only)."""
    return list(CSV_MATERIALS.keys())

def get_derating_factor(material_key: str, temperature_c: float) -> float:
    """
    Return the derating facto for a given standard material and temperature.
    
    Parameters
    ----------
    material_key : str
        key in STANDARD_MATERIALS (e.g., "P250GH")
    temperature_c : float
        Design temperature in °C.
    
    Returns
    -------
    float
        Stress ratio σ_allowable(T) / σ_allowable(20°C), in [0, 1].
    """

    if material_key not in STANDARD_MATERIALS:
        raise KeyError(f"Unknown material: {material_key}")

    derating_key = STANDARD_MATERIALS[material_key]["derating_key"]
    curve = DERATING_TABLES[derating_key]["curve"]

    # Clamp to the curve's temperature range.
    t_min = curve[0][0]
    t_max = curve[-1][0]
    t = max(t_min, min(t_max, temperature_c))

    # Linear interpolation
    for i in range(len(curve) - 1):
        t0, f0 = curve[i]
        t1, f1 = curve[i + 1]
        if t0 <= t <= t1:
            alpha = (t - t0) / (t1 - t0)
            return f0 + alpha * (f1 - f0)
    return curve[-1][1]

def get_allowable_stress(material_key: str, temperature_c: float) -> float:
    """
    Return the allowable stress (MPa) at a given design temperature.
    """
    material = STANDARD_MATERIALS[material_key]
    factor = get_derating_factor(material_key, temperature_c)
    return material["allowable_rt"] * factor

# ============================================================================
# 7. SELF-TEST
# ============================================================================

if __name__ == "__main__":
    print("EN 1092-1 Flange Dimension Database")
    print("=" * 60)
    print(f"Available DN sizes:             {len(EN1092_DIMENSIONS)}")
    print(f"Standard materials:             {len(STANDARD_MATERIALS)}")
    print(f"CSV-derived materials:          {len(CSV_MATERIALS)}")
    print()

    # Example: DN 50 PN 16
    dn, pn = "DN50", "PN16"
    spec = EN1092_DIMENSIONS[dn][pn]
    print(f"Example: {dn}{pn}")
    for k,v in spec.items():
        print(f" {k:12s}: {v}")
    print()

    # Example: derating for P250GH
    mat = "P250GH"
    print(f"Derating for {mat}:")
    for t in [20, 100, 200, 300, 400]:
        f = get_derating_factor(mat, t)
        s = get_allowable_stress(mat, t)
        print(f" T = {t:>3d} °C     factor = {f:.3f}    allowable = {s:.1f} MPa")