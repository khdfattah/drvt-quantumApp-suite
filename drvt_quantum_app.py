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
    10000.0,
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

# =========================
# Cryogenic Vacuum & Coherence Module
# =========================
st.divider()
st.header("Cryogenic Vacuum & Coherence Optimizer")
st.markdown(
    "Calculate the critical background gas pressure ($P_{\\text{crit}}$) to"
    " prevent decoherence ($\\Gamma < \\Gamma_q$)."
)

preset_exp = st.selectbox(
    "Experimental Benchmark",
    [
        "QphoX / Rigetti Qubit Readout (31 μW)",
        "Harvard TFLN High-Efficiency Target (100 μW)",
        "Harvard TFLN Low-Power Baseline (1 μW)",
        "Custom Operating Point",
    ],
)

if preset_exp == "QphoX / Rigetti Qubit Readout (31 μW)":
  def_p, def_q, def_v, def_t, def_lam = 31.0, 5.0e5, 5.0e-13, 10.0, 1564.89
elif preset_exp == "Harvard TFLN High-Efficiency Target (100 μW)":
  def_p, def_q, def_v, def_t, def_lam = 100.0, 2.0e6, 1.2e-12, 10.0, 1550.0
elif preset_exp == "Harvard TFLN Low-Power Baseline (1 μW)":
  def_p, def_q, def_v, def_t, def_lam = 1.0, 2.0e6, 1.2e-12, 10.0, 1550.0
else:
  def_p, def_q, def_v, def_t, def_lam = 1.0, 1.0e6, 5.0e-13, 10.0, 1550.0

col1, col2 = st.columns(2)
with col1:
  pump_uw = st.number_input("Optical Pump Power (μW)", value=def_p, min_value=1e-6)
  p_gas = st.number_input(
      "Ambient Gas Pressure P_gas (Pa)", value=1.0e-9, format="%.2e"
  )
  temp_mk = st.number_input("Cryogenic Temperature (mK)", value=def_t, min_value=1.0)

with col2:
  q_val = st.number_input("Cavity Quality Factor (Q)", value=def_q, format="%.1e")
  v_cav = st.number_input(
      "Cavity Volume V_cav (cm³)", value=def_v, format="%.1e"
  )
  lam_opt = st.number_input("Pump Wavelength (nm)", value=def_lam)

GAMMA_Q = 3.81e-7
n_res_cav = (v_cav * 1e21) / V_EQ
n_photons = 6455.7 * (pump_uw / 1.0) * (q_val / 1e6) * (lam_opt / 1550.0)
rod = n_photons / n_res_cav

p_crit = (
    1.48e-9
    * (1.0 / pump_uw)
    * (temp_mk / 10.0)
    * (1e6 / q_val)
    * (1550.0 / lam_opt)
    * (v_cav / 5e-13)
)
gamma = GAMMA_Q * (p_gas / p_crit)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Stored Photons", f"{n_photons:,.0f}")
m2.metric("Occupancy (ROD)", f"{rod:.2e}")
m3.metric("Max P_crit (Pa)", f"{p_crit:.2e}")
m4.metric("Coupling Γ", f"{gamma:.2e}")

if gamma < GAMMA_Q:
  st.success(
      f"✅ QUANTUM COHERENCE PRESERVED (Γ = {gamma:.2e} < Γ_q = 3.81e-7) | Spec:"
      f" {'UHV' if p_crit < 1e-7 else 'HV'}"
  )
else:
  st.error(
      f"⚠️ DECOHERENCE DOMINATED (Γ = {gamma:.2e} ≥ Γ_q = 3.81e-7) | Reduce"
      f" P_gas below {p_crit:.2e} Pa"
  )

# =========================
# 4. Pulsed Duty-Cycle & Anisotropic Crystal Cut Module
# =========================
st.divider()
st.header("Advanced Hardware Design: Pulsed Mode & Crystal Cut")
st.markdown(
    "Optimize optical pulse duty-cycles to bypass CW decoherence limits and"
    " evaluate anisotropic crystal orientations."
)

col_adv1, col_adv2 = st.columns(2)

with col_adv1:
  st.subheader("1. Pulsed-Mode Duty-Cycle Optimizer")
  st.caption(
      "Determine the safe laser duty cycle when continuous-wave (CW) pumping"
      " exceeds Γ_q."
  )
  peak_power_uw = st.number_input(
      "Peak Pulse Pump Power (μW)", value=31.0, min_value=0.001
  )
  target_p_gas = st.number_input(
      "Chamber Base Pressure (Pa)", value=1.0e-9, format="%.2e"
  )

  # Calculate CW Gamma at peak power using current Q, V_cav, T, lambda
  p_crit_peak = (
      1.48e-9
      * (1.0 / peak_power_uw)
      * (temp_mk / 10.0)
      * (1e6 / q_val)
      * (1550.0 / lam_opt)
      * (v_cav / 5e-13)
  )
  gamma_peak = GAMMA_Q * (target_p_gas / p_crit_peak)

  if gamma_peak < GAMMA_Q:
    max_duty = 100.0
    st.success(
        f"✅ **100% Duty Cycle (CW Safe):** Peak power is below the decoherence"
        f" threshold (Γ = {gamma_peak:.2e})."
    )
  else:
    # Safe duty cycle scales inversely with excess coupling above Gamma_q (with 20% safety margin)
    max_duty = min(99.0, (GAMMA_Q / gamma_peak) * 80.0)
    st.warning(
        f"⚡ **Pulsed Operation Required:** Limit laser duty cycle to **≤"
        f" {max_duty:.2f}%** (e.g., {max_duty*10:.1f} ns pulse per 1 μs period)"
        " to prevent gas-induced phase noise."
    )

with col_adv2:
  st.subheader("2. Anisotropic TFLN Crystal Orientation")
  st.caption(
      "Evaluate acoustic-photonic coupling across different Lithium Niobate"
      " wafer cuts."
  )
  crystal_cut = st.selectbox(
      "Select TFLN Wafer Orientation",
      [
          "X-Cut LiNbO₃ (Standard Electro-Optic, C11 = 203 GPa)",
          "Z-Cut LiNbO₃ (Vertical Acoustic Mode, C33 = 242 GPa)",
          "Y-Cut LiNbO₃ (SAW / Shear Mode, C22 = 203 GPa)",
          "128° Y-X Cut LiNbO₃ (High Piezo-Coupling, C_eff = 215 GPa)",
      ],
  )

  if "Z-Cut" in crystal_cut:
    c_eff = 242.0
  elif "128°" in crystal_cut:
    c_eff = 215.0
  else:
    c_eff = 203.0

  r_cut, xi_cut, state_cut, score_cut = material_state(c_eff, 4640.0, lambda_ph)
  vs_cut = math.sqrt((c_eff * 1e9) / 4640.0)

  c_a, c_b = st.columns(2)
  c_a.metric("Acoustic Velocity", f"{vs_cut:,.0f} m/s")
  c_b.metric("Cut Suitability", f"{score_cut}/100")
  st.info(
      f"**Orientation Analysis:** r_res = {r_cut:.3f} Å (ξ = {xi_cut:.2f}) —"
      f" {state_cut}"
  )
