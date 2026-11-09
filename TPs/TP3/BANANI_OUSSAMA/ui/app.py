
"""Interface Streamlit de MaintAI : explorer les données, puis demander une prédiction à l'API.

Lancement (depuis la racine du projet) : python -m streamlit run ui/app.py
"""
import httpx
import pandas as pd
import streamlit as st

from maintai.client import APIError, MaintaiClient
from maintai.config import FEATURES, get_settings

st.set_page_config(page_title="MaintAI", page_icon="🔧")
st.title("MaintAI · prédiction de panne")


@st.cache_data
def charger(path) -> pd.DataFrame:
    # Lu une seule fois : Streamlit relance tout le script à chaque clic
    return pd.read_csv(path)


with st.sidebar:
    url = st.text_input("URL de l'API", "http://localhost:8000")
    cle = st.text_input("Clé API", type="password")

onglet_donnees, onglet_prediction = st.tabs(["Données", "Prédiction"])

# Sprint 1 : explorer les données
with onglet_donnees:
    df = charger(get_settings().data_path)

    # 1. Trois indicateurs
    c1, c2, c3 = st.columns(3)
    c1.metric("Nombre de relevés", len(df))
    c2.metric("Taux de panne", f"{df.failure.mean():.1%}")
    c3.metric("Température moyenne", f"{df.temperature_c.mean():.1f} °C")

    # 2. Choisir une variable
    variable = st.selectbox("Choisir une variable", FEATURES)

    # 3. Taux de panne par tranche
    tranches = pd.cut(df[variable], bins=10)
    taux = df.groupby(tranches, observed=True).failure.mean()
    taux.index = [round(i.mid, 2) for i in taux.index]
    st.subheader(f"Taux de panne par {variable}")
    st.bar_chart(taux)

    # 4. Nuage de points température / vibration
    df_nuage = df.copy()
    df_nuage["Panne"] = df_nuage["failure"].map({0: "Non", 1: "Oui"})
    st.subheader("Température et vibration")
    st.scatter_chart(
        df_nuage,
        x="temperature_c",
        y="vibration_mm_s",
        color="Panne"
    )


# Sprint 2 : demander une prédiction à l'API
with onglet_prediction:
    with st.form("releve"):
        releve = {
            "temperature_c": st.slider("Température (°C)", -40.0, 150.0, 72.0),
            "vibration_mm_s": st.slider("Vibration (mm/s)", 0.0, 50.0, 6.0),
            "load_pct": st.slider("Charge (%)", 0.0, 100.0, 85.0),
            "runtime_hours": st.number_input(
                "Heures de fonctionnement", 0, 100_000, 15000
            ),
        }
        envoye = st.form_submit_button("Prédire")

    if envoye:
        try:
            api = MaintaiClient(url, api_key=cle)
            resultat = api.predict(releve)

        except APIError as e:
            st.warning(f"Erreur {e.status_code} : {e.detail}")

        except httpx.HTTPError as e:
            st.error(f"API injoignable : {e}")

        else:
            pct = round(resultat["failure_probability"] * 100)
            st.metric("Probabilité de panne", f"{pct} %")

            if resultat["alert"]:
                st.error("ALERTE : risque de panne détecté !")
            else:
                st.success("Situation normale : aucun risque de panne détecté.")