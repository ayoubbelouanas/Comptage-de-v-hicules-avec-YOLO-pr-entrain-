# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** …  ·  **Membres :** Ayoub BELOUANAS  ·  **Date :** 09/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
5 failed, 18 passed in 13.16s
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

test_client.py.  test_client_returns_prediction - NotImplementedError
test_client.py.  test_client_wrong_key_raises_401 - NotImplementedError
test_client.py.  test_client_bad_reading_raises_422 - NotImplementedError
test_ui.py.   test_ui_shows_the_data - IndexError
test_ui.py.   test_ui_shows_the_prediction - IndexError

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
ModuleNotFoundError: No module named 'maintai'
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

Avec `python -m streamlit`, Python ajoute le dossier courant au chemin de recherche des modules. Comme je lance la commande depuis la racine du projet, Python y trouve le dossier `maintai`.

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

```python
 c1, c2, c3 = st.columns(3)
    c1.metric("Relevés", len(df))
    c2.metric("Taux de panne", f"{df['failure'].mean():.1%}")
    c3.metric("Température moyenne", f"{df['temperature_c'].mean():.1f} °C")

    # Laisse choisir une variable pour comparer son évolution avec le taux de panne.
    variable = st.selectbox("Variable à explorer", FEATURES)
    tranches = pd.cut(df[variable], bins=10)
    taux_par_tranche = df.groupby(tranches, observed=True)["failure"].mean()

    # Utilise le milieu numérique de chaque tranche comme étiquette des barres.
    taux_par_tranche.index = [
        round(tranche.mid, 2) for tranche in taux_par_tranche.index
    ]
    st.subheader(f"Taux de panne selon {variable}")
    st.bar_chart(taux_par_tranche)

    # Affiche la panne sous forme de texte pour distinguer plus facilement les points.
    donnees_nuage = df.assign(
        panne=df["failure"].map({0: "Non", 1: "Oui"})
    )
    st.subheader("Température et vibration")
    st.scatter_chart(
        donnees_nuage,
        x="temperature_c",
        y="vibration_mm_s",
        color="panne",
    )
```

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000 |
| Taux de panne | 13.6% |
| Température moyenne | 59.8°C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

Quand la vibration augmente , le taux de panne augmente aussi. Il approche 100 % dans les tranches de vibration les plus élevées.

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

Les curseurs sont dans un formulaire : les déplacer seuls ne relance pas le script. Le message relance apparaît quand on clique sur « Prédire ». Cela montre que Streamlit réexécute le script après l’envoi du formulaire. Le formulaire retarde la réexécution jusqu’à ce clic.

À quoi sert `@st.cache_data` sur la fonction `charger` ?

Ce décorateur met en cache le résultat de charger. Lors des réexécutions suivantes, Streamlit peut réutiliser le jeu de données déjà chargé au lieu de relire le fichier CSV.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
        """Envoie un relevé à l’API et renvoie sa prédiction.

        Args:
            reading: Dictionnaire contenant les valeurs des capteurs.

        Returns:
            La réponse JSON de l’API en cas de succès.

        Raises:
            APIError: Si l’API répond avec un code différent de 200.
            httpx.HTTPError: Si la requête ne peut pas atteindre l’API.
        """
        # TODO TP3 sprint 2 :
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        response = self.http.post(
            "/v1/predict",
            json=reading,
            headers=headers,
        )

        if response.status_code != 200:
            detail = response.json().get("detail")
            raise APIError(response.status_code, detail)

        return response.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
1 failed, 22 passed, 1 warning in 6.51s
```

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | ALERTE : risque de panne (95 %) |
| valeurs par défaut, fausse clé | Erreur 401 : Clé API absente ou invalide |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | API injoignable : [Errno 61] Connection refused |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

CORS est une restriction appliquée par les navigateurs. Dans le TP3, le navigateur communique avec Streamlit sur le port 8501, puis c’est le code Python de Streamlit qui envoie la requête à l’API. Cette requête est faite côté serveur avec httpx, donc elle n’est pas bloquée par CORS.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   Dans la page web du TP2, le JavaScript du navigateur envoie la requête à l’API avec fetch. Dans Streamlit, c’est le code Python côté serveur qui l’envoie avec MaintaiClient et httpx.

2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   Les tests fournissent à MaintaiClient un client de test qui appelle directement l’application FastAPI. La requête ne passe donc pas par un serveur uvicorn.

3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   Pour une démonstration rapide à un client, je choisirais la page HTML et JavaScript : elle est légère et s’ouvre dans un navigateur. Pour le travail quotidien d’un technicien, je choisirais Streamlit : ses onglets, ses graphiques et ses contrôles facilitent l’exploration des relevés et la demande de prédictions.

## 6. Le rendu Git

- Lien de la pull request : …
- Le tag `tp3` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? oui / non

## 7. Ce qui reste flou

…
