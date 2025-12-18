import streamlit as st
import requests
import json
from predict_core import predict_flu_probability

# =================================================
# 0️⃣ 前端 JS：把 #hash 轉成 ?query（關鍵）
# =================================================
st.components.v1.html(
    """
    <script>
    (function () {
        if (window.location.hash && !window.location.search) {
            const q = window.location.hash.substring(1);
            const newUrl = window.location.pathname + "?" + q;
            window.location.replace(newUrl);
        }
    })();
    </script>
    """,
    height=0,
)

st.title("Flu Prediction Model by XGBoost Algorithm")

# =================================================
# 1️⃣ 從 URL 讀取 SMART on FHIR 參數
# =================================================
qp = st.query_params

token = qp.get("token")
pid   = qp.get("pid")
fhir  = qp.get("fhir")
obs   = qp.get("obs")

# =================================================
# 2️⃣ FHIR → patient_data（最小必要欄位）
# =================================================
def load_patient_data_from_fhir(token, pid, fhir, obs):
    if not (token and pid and fhir):
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/fhir+json"
    }

    patient_data = {}

    # -----------------------------
    # Observation
    # -----------------------------
    if obs:
        r = requests.get(obs, headers=headers, verify=False)
        o = r.json()

        for c in o.get("component", []):
            code = c.get("code", {}).get("coding", [{}])[0].get("code")

            # -------- Numeric --------
            if code == "8310-5":       # Body temperature
                patient_data["temp"] = c["valueQuantity"]["value"]

            elif code == "9279-1":     # Respiratory rate
                patient_data["rr"] = c["valueQuantity"]["value"]

            elif code == "8480-6":     # Systolic BP
                patient_data["sbp"] = c["valueQuantity"]["value"]

            elif code == "59408-5":    # O2 saturation
                patient_data["o2s"] = c["valueQuantity"]["value"]

            elif code == "8867-4":     # Pulse
                patient_data["pulse"] = c["valueQuantity"]["value"]

            # -------- Binary (範例) --------
            elif code == "cough" and c.get("valueInteger", 0) == 1:
                patient_data["cough"] = "Yes"

            elif code == "rhinorrhea" and c.get("valueInteger", 0) == 1:
                patient_data["rhinorrhea"] = "Yes"

    return patient_data if patient_data else None


patient_data = load_patient_data_from_fhir(token, pid, fhir, obs)

# =================================================
# 3️⃣ Helper（你原本的，完全不動）
# =================================================
def num_input(label, minv, maxv, default, step=1.0, key=None):
    value = default
    if patient_data and key in patient_data:
        value = patient_data[key]

    if isinstance(minv, float):
        value = float(value)
    else:
        value = int(value)

    return st.number_input(label, minv, maxv, value, step=step)


def yn(label, key):
    options = ["No", "Yes"]
    idx = 0

    if patient_data and key in patient_data:
        v = patient_data[key]
        if isinstance(v, int):
            idx = 1 if v == 1 else 0
        elif isinstance(v, str):
            idx = options.index(v)

    return st.selectbox(label, options, index=idx)

# =================================================
# 4️⃣ Numeric inputs
# =================================================
temp = num_input("Temperature (°C)", 30.0, 42.0, 37.3, 1.0, "temp")
height = num_input("Height (CM)", 1.0, 400.0, 160.0, 0.5, "height")
weight = num_input("Weight (KG)", 1.0, 400.0, 60.0, 0.5, "weight")
DOI = num_input("Days of illness", 1, 14, 1, 1, "DOI")
WOS = num_input("Week of year", 1, 53, 1, 1, "WOS")
season = num_input("Season (1–4)", 1, 4, 1, 1, "season")
rr = num_input("Respiratory rate", 10, 30, 12, 1, "rr")
sbp = num_input("Systolic BP", 50, 250, 90, 1, "sbp")
o2s = num_input("Oxygen saturation (%)", 1, 100, 100, 1, "o2s")
pulse = num_input("Pulse", 50, 180, 100, 1, "pulse")

# =================================================
# 5️⃣ Binary inputs
# =================================================
fluvaccine = yn("Influenza vaccine this year?", "fluvaccine")
cough = yn("New or increased cough?", "cough")
coughsputum = yn("Cough with sputum?", "coughsputum")
sorethroat = yn("Sore throat?", "sorethroat")
rhinorrhea = yn("Rhinorrhea / nasal congestion?", "rhinorrhea")
sinuspain = yn("Sinus pain?", "sinuspain")
exposehuman = yn("Exposure to confirmed influenza?", "exposehuman")
travel = yn("Recent travel?", "travel")
medhistav = yn("Influenza antivirals in past 30 days?", "medhistav")
pastmedchronlundis = yn("Chronic lung disease?", "pastmedchronlundis")

# =================================================
# 6️⃣ Prediction（完全不動）
# =================================================
if st.button("Predict"):
    prob = predict_flu_probability(
        temp, height, weight, DOI, WOS, season,
        rr, sbp, o2s, pulse,
        fluvaccine, cough, coughsputum, sorethroat,
        rhinorrhea, sinuspain, exposehuman, travel,
        medhistav, pastmedchronlundis
    )

    st.metric("Predicted probability (%)", f"{prob:.2f}")
