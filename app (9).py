import streamlit as st
from predict_core import predict_flu_probability

st.title("Flu Prediction Model by XGBoost Algorithm")

# =================================================
# 0️⃣ 病人資料（之後可換成 FHIR / API；無資料就設 None）
# =================================================
# patient_data = None
patient_data = {
    "temp": 38.2,
    "height": 170,
    "weight": 68,
    "DOI": 2,
    "WOS": 5,
    "season": 1,
    "rr": 20,
    "sbp": 110,
    "o2s": 96,
    "pulse": 105,
    "fluvaccine": "No",
    "cough": "Yes",
    "coughsputum": "Yes",
    "sorethroat": "No",
    "rhinorrhea": "Yes",
    "sinuspain": "No",
    "exposehuman": "Yes",
    "travel": "No",
    "medhistav": "No",
    "pastmedchronlundis": "No",
}

# =================================================
# 1️⃣ Helper（最小新增）
# =================================================
def num_input(label, minv, maxv, default, step=1.0, key=None):
    value = default
    if patient_data and key in patient_data:
        value = patient_data[key]

    # 🔒 關鍵：型別對齊（Streamlit 要求）
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

        # 🔒 最小修正：支援 0/1 or "No"/"Yes"
        if isinstance(v, int):
            idx = 1 if v == 1 else 0
        elif isinstance(v, str):
            idx = options.index(v)

    return st.selectbox(label, options, index=idx)

# =================================================
# 2️⃣ Numeric inputs（原順序，僅加 key）
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
# 3️⃣ Binary inputs（原結構）
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
# 4️⃣ Prediction（完全不動）
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
