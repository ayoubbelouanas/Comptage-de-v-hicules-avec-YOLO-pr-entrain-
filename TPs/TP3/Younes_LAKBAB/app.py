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
    
# ============================================================
# SPRINT 1 : EXPLORATION DES DONNÉES
# ============================================================

with onglet_donnees:

    # Charger les données des capteurs depuis le fichier CSV.
    # La fonction charger() utilise @st.cache_data pour éviter
    # de relire le fichier à chaque interaction avec l'interface.
    df = charger(get_settings().data_path)

    # --------------------------------------------------------
    # 1. Affichage des trois indicateurs
    # --------------------------------------------------------

    # Créer trois colonnes côte à côte dans l'interface.
    c1, c2, c3 = st.columns(3)

    # Afficher le nombre total de relevés.
    c1.metric("Relevés", len(df))

    # Calculer le taux de panne.
    # failure = 1 signifie panne, failure = 0 signifie normal.
    # La moyenne représente donc la proportion de pannes.
    taux_panne = df["failure"].mean()

    # Afficher le taux de panne sous forme de pourcentage.
    c2.metric("Taux de panne", f"{taux_panne:.1%}")

    # Calculer la température moyenne des machines.
    temperature_moyenne = df["temperature_c"].mean()

    # Afficher la température moyenne avec une décimale.
    c3.metric(
        "Température moyenne",
        f"{temperature_moyenne:.1f} °C"
    )

    # --------------------------------------------------------
    # 2. Sélection d'une variable
    # --------------------------------------------------------

    st.subheader("Analyse du taux de panne")

    # Permettre à l'utilisateur de choisir une variable.
    # FEATURES contient les quatre variables du modèle.
    variable = st.selectbox(
        "Choisir une variable",
        FEATURES
    )

    # --------------------------------------------------------
    # 3. Calcul du taux de panne par tranche
    # --------------------------------------------------------

    # Découper les valeurs de la variable en 10 intervalles.
    tranches = pd.cut(df[variable], bins=10)

    # Calculer le taux moyen de panne dans chaque intervalle.
    # observed=True évite de conserver des catégories inutilisées.
    taux_par_tranche = (
        df.groupby(tranches, observed=True)["failure"]
        .mean()
    )

    # Remplacer chaque intervalle par son point central.
    # Cela permet de conserver des étiquettes numériques.
    taux_par_tranche.index = [
        round(intervalle.mid, 2)
        for intervalle in taux_par_tranche.index
    ]

    # Afficher le taux de panne sous forme de diagramme en barres.
    st.bar_chart(taux_par_tranche)

    # --------------------------------------------------------
    # 4. Nuage de points : température et vibration
    # --------------------------------------------------------

    st.subheader("Relation entre température et vibration")

    # Créer une copie du DataFrame pour le graphique.
    # Les données originales ne sont pas modifiées.
    df_nuage = df.copy()

    # Transformer les valeurs de panne en catégories lisibles.
    # 0 devient "Non" et 1 devient "Oui".
    df_nuage["panne"] = df_nuage["failure"].map({
        0: "Non",
        1: "Oui"
    })

    # Afficher un nuage de points.
    # Axe X : température.
    # Axe Y : vibration.
    # Couleur : présence ou absence de panne.
    st.scatter_chart(
        df_nuage,
        x="temperature_c",
        y="vibration_mm_s",
        color="panne"
    )

    st.info("Sprint 1 : les indicateurs et les graphiques viendront ici.")


# Sprint 2 : demander une prédiction à l'API
with onglet_prediction:
    with st.form("releve"):
        releve = {
            "temperature_c": st.slider("Température (°C)", -40.0, 150.0, 72.0),
            "vibration_mm_s": st.slider("Vibration (mm/s)", 0.0, 50.0, 6.0),
            "load_pct": st.slider("Charge (%)", 0.0, 100.0, 85.0),
            "runtime_hours": st.number_input("Heures de fonctionnement", 0, 100_000, 15000),
        }
        envoye = st.form_submit_button("Prédire")

    if envoye:
        # 1. Créer le client HTTP.
        # url : adresse du serveur FastAPI.
        # cle : clé API saisie dans la barre latérale.
        api = MaintaiClient(url, api_key=cle)

        try:
            # 2. Envoyer les relevés des capteurs à l'API.
            # La méthode predict retourne le résultat en JSON.
            resultat = api.predict(releve)

        except APIError as erreur:
            # 3. Gérer les erreurs renvoyées par l'API.
            # Exemples : 401 (clé invalide), 422 (données invalides).
            st.warning(
                f"Erreur {erreur.status_code} : {erreur.detail}"
            )

        except httpx.HTTPError:
            # 4. Gérer les erreurs de communication.
            # Ce message apparaît notamment si l'API est arrêtée.
            st.error("API injoignable : vérifiez le serveur.")

        else:
            # 5. Récupérer la probabilité de panne.
            # La valeur retournée est comprise entre 0 et 1.
            probabilite = resultat["failure_probability"]

            # Convertir la probabilité en pourcentage entier.
            pourcentage = round(probabilite * 100)

            # Afficher le résultat dans l'interface.
            st.metric(
                "Probabilité de panne",
                f"{pourcentage} %"
            )

            # 6. Afficher un message selon l'état de la machine.
            if resultat["alert"]:
                # Le modèle détecte un risque de panne.
                st.error("ALERTE : risque de panne détecté.")
            else:
                # Le risque de panne est jugé acceptable.
                st.success("État normal : aucune alerte de panne.")

        st.info("Sprint 2 : la prédiction s'affichera ici.")
