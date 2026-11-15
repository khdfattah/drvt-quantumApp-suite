import math
import pandas as pd
import streamlit as st

# =========================
# DRVT DESIGN ENGINE
# =========================

st.set_page_config(
    page_title="DRVT Design Engine",
    page_icon="⚛️",
    layout="wide"
)

# -------------------------
# Constants
# -------------------------

V_EQ = 286.398      # nm³
A0 = 0.529          # Å

# -------------------------
# Material Database
# -------------------------

MATERIALS = {
    "Diamond": {"C11": 1076, "rho": 3515},
    "Silicon": {"C11": 165.6, "rho": 2329},
    "GaAs": {"C11": 119, "rho": 5317},
    "AlN": {"C11": 410, "rho": 3260},
    "SiC": {"C11": 390, "rho": 3210},
    "LiNbO3": {"C11": 203, "rho": 4640},
}

# -------------------------
# Functions
# -------------------------

def photonic_state(lambda_nm):
    r_nm = math.sqrt(V_EQ / (math.pi * lambda_nm))
    aeff = math.pi * r_nm**2
    energy = 13.606 * r_nm**2
    xi = (r_nm * 10) / A0
    return r_nm, aeff, energy, xi

def material_state(c11, rho, lambda_ph=1.0):
    r_ang = 10 * (
        ((5.5133e-4 * c11 * 1e9) /
         (rho * lambda_ph**2)) ** 0.25
    )

    xi = r_ang / A0

    if xi > 1.05:
        state = "Extended Photo‑Phononic"
        score = 90 + min(10, (xi - 1))
    elif xi < 0.95:
        state = "Localized Phononic"
        score = max(50, 100 - (1 - xi) * 100)
    else:
        state = "Transition Boundary"
        score = 100

    return r_ang, xi, state, round(score, 1)

# -------------------------
# Header
# -------------------------

st.title("⚛️ DRVT Design Engine")

st.markdown("""
Material screening and resonance-state classification platform
based on Dynamic Resonant Volume Theory (DRVT).
""")

# =========================
# Photonic Module
# =========================

st.header("Photonic Resonance")

lambda_nm = st.number_input(
    "Wavelength λ (nm)",
    value=1550.0
)

r_nm, aeff, energy, xi = photonic_state(lambda_nm)

c1, c2, c3, c4 = st.columns(4)

c1.metric("r_res (nm)", f"{r_nm:.4f}")
c2.metric("A_eff (nm²)", f"{aeff:.4f}")
c3.metric("Energy (eV)", f"{energy:.4f}")
c4.metric("ξ", f"{xi:.2f}")

# =========================
# Material Module
# =========================

st.header("Material Selection")

selected = st.selectbox(
    "Material",
    list(MATERIALS.keys())
)

lambda_ph = st.slider(
    "Target Phonon Wavelength (nm)",
    500.0,
    500000.0,
    1.0
)

mat = MATERIALS[selected]

rA, xiA, stateA, scoreA = material_state(
    mat["C11"],
    mat["rho"],
    lambda_ph
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("C11 (GPa)", mat["C11"])
c2.metric("ρ (kg/m³)", mat["rho"])
c3.metric("r_res (Å)", f"{rA:.3f}")
c4.metric("Suitability", f"{scoreA}/100")

st.success(f"DRVT Regime: {stateA}")

# =========================
# Ranking Table
# =========================

rows = []

for name, props in MATERIALS.items():

    rA, xiA, stateA, scoreA = material_state(
        props["C11"],
        props["rho"],
        lambda_ph
    )

    rows.append([
        name,
        round(rA, 3),
        round(xiA, 2),
        stateA,
        scoreA
    ])

atlas = pd.DataFrame(
    rows,
    columns=[
        "Material",
        "r_res (Å)",
        "ξ",
        "State",
        "Score"
    ]
)

atlas = atlas.sort_values(
    "Score",
    ascending=False
)

st.header("DRVT Material Ranking")

st.dataframe(
    atlas,
    use_container_width=True
)
