import streamlit as st
import requests
from predict_core import predict_flu_probability

st.title("Flu Prediction Model by XGBoost Algorithm")

# =========================================
# 1️⃣ 讀 FHIR Observation
# =========================================
def load_patient_data_from_fhir(token, obs_url):
    patient_data = {}
    try:
        r = requests.get(obs_url, headers={"Authorization": f"Bearer {token}"}, verify=False, timeout=10)
        o = r.json()
    except Exception:
        return None

    for c in o.get("component", []):
        text = c.get("code", {}).get("text", "").strip()
        # Numeric
        if text == "Temperature (°C)":
            patient_data["temp"] = c["valueQuantity"]["value"]
        elif text == "Height (CM)":
            patient_data["height"] = c["valueQuantity"]["value"]
        elif text == "Weight (KG)":
            patient_data["weight"] = c["valueQuantity"]["value"]
        elif text == "Pulse":
            patient_data["pulse"] = c["valueQuantity"]["value"]
        elif text == "Respiratory rate":
            patient_data["rr"] = c["valueQuantity"]["value"]
        elif text == "Systolic BP":
            patient_data["sbp"] = c["valueQuantity"]["value"]
        elif text == "Oxygen saturation (%)":
            patient_data["o2s"] = c["valueQuantity"]["value"]
        elif text == "Season (1–4)":
            patient_data["season"] = c.get("valueInteger")
        elif text == "Week of Year":
            patient_data["WOS"] = c.get("valueInteger")
        elif text == "Days of illness":
            patient_data["DOI"] = c.get("valueInteger")
        # Binary
        elif text == "Influenza vaccine this year?":
            patient_data["fluvaccine"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Exposure to confirmed influenza?":
            patient_data["exposehuman"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Recent travel?":
            patient_data["travel"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "New or increased cough?":
            patient_data["cough"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Cough with sputum?":
            patient_data["coughsputum"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Sore throat?":
            patient_data["sorethroat"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Rhinorrhea / nasal congestion?":
            patient_data["rhinorrhea"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Sinus pain?":
            patient_data["sinuspain"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Influenza antivirals in past 30 days?":
            patient_data["medhistav"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Chronic lung disease?":
            patient_data["pastmedchronlundis"] = "Yes" if c.get("valueInteger") == 1 else "No"
    return patient_data

# =========================================
# 2️⃣ 接收 token / obs_url 等（你可從 URL 或手動填）
# =========================================
token = st.text_input("Token", value="")
obs_url = st.text_input("Observation URL", value="")

patient_data = {}
if token and obs_url:
    patient_data = load_patient_data_from_fhir(token, obs_url)

    # =========================================
    # 2a️⃣ 顯示 FHIR 原始資料 / patient_data (可收折)
    # =========================================
    with st.expander("查看抓到的病患資料（收折）", expanded=False):
        st.json(patient_data)

    # =========================================
    # 2b️⃣ 將抓到的值放入 session_state，強制更新 widget 預設值
    # =========================================
    for k, v in patient_data.items():
        if k not in st.session_state:
            st.session_state[k] = v

# =========================================
# 3️⃣ helper（改成讀 session_state）
# =========================================
def num_input(label, minv, maxv, default, step=1.0, key=None):
    value = st.session_state.get(key, default)
    if isinstance(minv, float):
        value = float(value)
    else:
        value = int(value)
    return st.number_input(label, minv, maxv, value, step=step, key=key)

def yn(label, key):
    options = ["No", "Yes"]
    idx = 0
    v = st.session_state.get(key, "No")
    if isinstance(v, int):
        idx = 1 if v == 1 else 0
    elif isinstance(v, str):
        idx = options.index(v)
    return st.selectbox(label, options, index=idx, key=key)

# =========================================
# 4️⃣ Streamlit UI
# =========================================
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

# =========================================
# 5️⃣ Prediction
# =========================================
if st.button("Predict"):
    prob = predict_flu_probability(
        temp, height, weight, DOI, WOS, season,
        rr, sbp, o2s, pulse,
        fluvaccine, cough, coughsputum, sorethroat,
        rhinorrhea, sinuspain, exposehuman, travel,
        medhistav, pastmedchronlundis
    )
    st.metric("Predicted probability (%)", f"{prob:.2f}")
