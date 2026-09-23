# Technical Brief — Smart Pressure Flange Generator

**Author:** Altug Remzi Akay

**Version:** 1.0

**Date:** September 2026

This document explains the engineering calculations behind the Smart
Pressure Flange Generator, including the standard references, formulas, assumptions, and implementation notes.

---

## 1. Introduction

A bolted flange connection is a critical safety-relevant component in any pressurised piping system. It must:

1. **Contain the internal pressure** without yielding.
2. **Compress the gasket** enough to seal at both ambient and operating conditions.
3. **Remain rigid** under bolt preload and pressure-induced moments.
4. **Not leak** under thermal cycling or external loads.

The European standard **EN 1092-1** specifies the geometry and pressure rating of standard flanges. **EN 13445** gives the wall-thickness formula for the pressure envelope. **ASME VIII Div. 1 Appendix 2** gives the bolted-joint bolt-load analysis. This tool implements all three.

---

## 2. Geometry from EN 1092-1

### 2.1 Flange Types

EN 1092-1 defines several flange types. This tool covers **Type 11 —
welding-neck flange, raised face**, the most common industrial type.

A Type 11 flange has:

- A circular **flange disc** with bolt holes on a bolt circle
- A **tapered hub** rising from the disc, ending in a weld-preparation bevel
- A **raised face** on the mating side (bottom), 2 mm above the flange face
- A **fillet** at the hub-to-disc junction to reduce stress concentration

### 2.2 Dimension Table

For every combination of DN (nominal size) and PN (pressure rating), EN 1092-1 specifies:

| Symbol | Meaning |
|--------|---------|
| **D** | Flange outer diameter |
| **K** | Bolt circle diameter |
| **L** | Bolt hole diameter |
| **n** | Number of bolts |
| **b** | Bolt thread size (e.g. M16) |
| **C** | Flange thickness at the hub |
| **H1** | Hub diameter at weld end |
| **H2** | Hub diameter at flange junction |
| **H3** | Hub height |

These values are stored in `config.EN1092_DIMENSIONS` and are the source of truth for all geometry generation.

---

## 3. Pressure Rating and Temperature Derating

### 3.1 Nominal Rating

A flange rated **PN16** is designed for a maximum working pressure of
**16 bar = 1.6 MPa** at **20 °C**.

### 3.2 Temperature Derating

As the operating temperature rises, the allowable stress of the steel falls. EN 1092-1 publishes derating curves that give the fraction of the room-temperature rating that remains available at elevated temperature.

The tool interpolates linearly between published data points. For carbon steel (P250GH):

| T (°C) | Factor |
|--------|--------|
| −20 | 1.00 |
| 20 | 1.00 |
| 100 | 0.93 |
| 200 | 0.83 |
| 300 | 0.73 |
| 400 | 0.62 |
| 450 | 0.55 |

The derated rating is:

$$
P_{\text{derated}}(T) = \text{PN} \times f(T)
$$

**Verification check:** the design passes only if

$$
P_{\text{operating}} \leq P_{\text{derated}}(T)
$$

---

## 4. Wall Thickness (EN 13445)

The minimum wall thickness for a cylindrical shell under internal pressure is:

$$
e = \frac{P \cdot D_i}{2 \cdot f \cdot E - P} + c
$$

where:

| Symbol | Meaning | Units |
|--------|---------|-------|
| e | Required wall thickness | mm |
| P | Design pressure | MPa |
| ${D_i}$ | Internal diameter | mm |
| f | Nominal design stress = allowable stress | MPa |
| E | Weld efficiency factor | – |
| c | Corrosion allowance | mm |

The **weld efficiency** `E` depends on the inspection regime:

| Regime | E |
|--------|---|
| Fully radiographed | 1.00 |
| Spot-radiographed | 0.85 |
| Non-radiographed | 0.70 |

The tool uses `E = 0.85` by default.

**Verdict:** the design passes if the actual flange thickness is greater than the required thickness.

---

## 5. Hoop Stress Verification

For a thin-walled cylinder under internal pressure, the hoop stress is:

$$
\sigma_h = \frac{P \cdot D_i}{2 \cdot t}
$$

where `t` is the actual flange thickness. The design passes if:

$$
\sigma_h \leq f \cdot E
$$

This is a quick sanity check on top of the thickness formula. The two
checks are redundant by construction, but the second one gives engineers an immediately comparable number.

---

## 6. Bolt Load Analysis (ASME VIII Div. 1, Appendix 2)

The bolted-joint analysis ensures that the bolts are strong enough to:

1. **Seat the gasket** during assembly, at ambient conditions.
2. **Maintain the seal** during operation, at design pressure.

### 6.1 Gasket Reaction Diameter

The gasket reaction diameter `G` is taken conservatively as:

$$
G = d_1 + N
$$

where `d_1` is the gasket inner diameter and `N` is the gasket width. Gasket dimensions are taken from EN 1514-1 (flat) or EN 1514-2 (spiral-wound).

### 6.2 Effective Gasket Width

The effective gasket width `b` is:

$$
b = \begin{cases}
b_0 & \text{if } b_0 \leq 6.4 \text{ mm} \\
2.5 \sqrt{b_0} & \text{if } b_0 > 6.4 \text{ mm}
\end{cases}
$$

where `b_0 = N / 2`.

### 6.3 Gasket Seating Load (Wm1)

The minimum bolt load required to seat the gasket is:

$$
W_{m1} = \pi \cdot b \cdot G \cdot y
$$

where `y` is the minimum design seating stress (MPa), from the ASME
table for the gasket type.

### 6.4 Operating Load (Wm2)

The minimum bolt load required to maintain the seal under operating
pressure is:

$$
W_{m2} = \frac{\pi G^2}{4} P + 2 \pi b G m P
$$

where `m` is the gasket factor (dimensionless), from the ASME table.

### 6.5 Required Bolt Area

The required total bolt cross-sectional area is:

$$
A_m = \frac{\max(W_{m1}, W_{m2})}{S_b}
$$

where `S_b` is the allowable bolt stress at the design temperature.

The available bolt area is:

$$
A_b = n \times A_{\text{bolt}}
$$

with `A_bolt` the tensile stress area of a single bolt, from ISO 898-1.

**Verdict:**

- Under `EN_1092` philosophy: a shortfall is a **warning only** (design-by-rule).
- Under `ASME_VIII_App2`: a shortfall is a **hard error**.

---

## 7. Flange Rigidity (Kellogg Index)

The simplified Kellogg rigidity index is:

$$
J = \frac{D_{\text{out}} / t_{\text{flange}}}{K / L}
$$

where `D_out` is the flange outer diameter, `t` is the flange thickness, `K` is the bolt circle diameter, and `L` is the bolt hole diameter.

**Interpretation:**

| J | Meaning |
|---|---------|
| J < 1.0 | Flange is rigid |
| 1.0 ≤ J < 2.0 | Flange may rotate slightly under bolt load |
| J ≥ 2.0 | Flange is flexible — consider a thicker design |

The Kellogg index is a screening check, not a substitute for FEA.

---

## 8. CAD Generation

The flange geometry is built in **CadQuery** as follows:

1. **Base disc** — a cylinder of outer diameter `D` and thickness `t`.
2. **Tapered hub** — a loft between `H2` (at the disc) and `H1` (at the weld
   end), extruded upward by `H3`.
3. **Raised face** — a cylinder of diameter `d_gasket + 2 mm`, extruded by
   2 mm downward from the disc face.
4. **Bore** — a through-cut cylinder of diameter `DN`.
5. **Bolt holes** — a polar array of `n` circles of diameter `L`, cut
   through the disc.
6. **Fillet** — at the hub-to-disc junction. The radius is:

   $$
   r_f = \min\left(0.15 \cdot H_2,\ 0.6 \cdot t,\ \text{gap to bolt holes}\right)
   $$

   The third term ensures the fillet doesn't collide with the bolt holes.
7. **Chamfer** — at the top of the hub, for the weld preparation (1.5 mm).

The solid is exported to **STEP** (for manufacturing and FEA) and **STL**
(for viewing and 3D printing).

---

## 9. Cost and Weight Estimation

The mass is computed from the volume:

$$
m = V \cdot \rho
$$

where `V` is the volume (mm³) and `ρ` the density (g/cm³).

The cost estimate uses three layers:

| Layer | Factor | Meaning |
|-------|--------|---------|
| Raw material | 1.0× | `m × cost_per_kg` |
| Waste factor | 1.15× | Chips, offcuts, scrap |
| Manufacturing | 2.5× | Machining, handling, QA |

The final estimate is therefore:

$$
C_{\text{total}} = m \times c_{\text{kg}} \times 1.15 \times 2.5
$$

This is a rough estimate. A real workshop quote would also include heat treatment, surface treatment, NDT, and material certification.

---

## 10. Assumptions and Limitations

1. **Linear elastic behaviour** is assumed throughout.
2. **No FEA.** All calculations are closed-form, per the referenced codes.
3. **No external nozzle loads** on the flange.
4. **No gasket creep or relaxation** over time.
5. **No consideration of fatigue** for cyclic service.
6. **No thermal gradient** through the flange.
7. **Standard geometry only.** Custom or non-standard flanges are out of scope.
8. **Preliminary design only.** Final verification by a qualified
   pressure-equipment engineer is required before production.

---

## 11. References

1. **EN 1092-1:2018+A1:2019** — Flanges and their joints — Circular flanges for pipes, valves, fittings and accessories, PN designated.
2. **EN 13445-3:2021** — Unfired pressure vessels — Part 3: Design.
3. **EN 10222-2:2017** — Steel forgings for pressure purposes — Part 2: Ferritic and martensitic steels with specified elevated temperature properties.
4. **EN 1514-1 / -2** — Flanges and their joints — Dimensions of gaskets for use with PN-designated flanges.
5. **ASME BPVC Section VIII Division 1** — Rules for Construction of Pressure Vessels, Appendix 2: Rules for Bolted Flange Connections with Ring Type Gaskets.
6. **ASME BPVC Section II Part D** — Materials — Properties.
7. **ISO 898-1:2013** — Mechanical properties of fasteners made of carbon steel and alloy steel.
8. **Kellogg, M.W.** — Design of Piping Systems, 2nd ed., Wiley, 1956.

---

## 12. Contact

For questions, corrections, or collaboration:

**Altug Remzi Akay**

Email: altug.akay@bergsskolan.se

GitHub: [@altugrakay-commits](https://github.com/altugrakay-commits)