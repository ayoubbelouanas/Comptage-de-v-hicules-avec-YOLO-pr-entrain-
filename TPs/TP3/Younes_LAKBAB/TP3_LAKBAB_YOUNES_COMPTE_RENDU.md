# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** …  ·  **Membres :** …  ·  **Date :** …

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
5 failed, 18 passed, 1 warning in 16.26s
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

tests/test_client.py : 3 échecs. Les tests test_client_returns_prediction, test_client_wrong_key_raises_401 et test_client_bad_reading_raises_422 lèvent NotImplementedError: TP3 sprint 2 : MaintaiClient.predict. La méthode predict n'est pas encore implémentée dans le starter. Elle sera développée au sprint 2.
tests/test_ui.py : 2 échecs. Les tests test_ui_shows_the_data et test_ui_shows_the_prediction lèvent IndexError: list index out of range parce que at.metric est vide : les indicateurs de l'onglet « Données » et l'affichage de la prédiction ne sont pas encore programmés.

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
(ModuleNotFoundError: No module named 'maintai'

File "C:\Users\youne\OneDrive\Bureau\maintai-starter-tp3\ui\app.py", line 9, in <module>
    from maintai.client import APIError, MaintaiClient
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

La deuxième commande fonctionne correctement et l'application devient accessible à l'adresse http://localhost:8501.

En utilisant python -m, Streamlit est lancé avec l'interpréteur Python actif, depuis la racine du projet. Python peut ainsi trouver et importer le package local maintai.

Contrairement à la première commande, cette méthode évite l'erreur ModuleNotFoundError.

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

```python
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
```

| Indicateur | Valeur affichée |
|---|---|
| Relevés |5000 |
| Taux de panne |13.6% |
| Température moyenne |59.8 °C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

Dans le jeu de données synthétique de MaintAI, le risque de panne augmente avec la vibration. Nous nous attendons donc à observer une tendance générale à la hausse du taux de panne lorsque la vibration augmente. Cette tendance doit être vérifiée sur le graphique obtenu.

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

Streamlit réexécute le script lorsque l'utilisateur modifie un widget situé en dehors d'un formulaire, comme la liste déroulante des variables. Le message « relance » apparaît alors dans le terminal.

En revanche, les curseurs de l'onglet « Prédiction » sont placés dans un formulaire st.form. Leur modification ne provoque pas immédiatement une réexécution : il faut cliquer sur le bouton « Prédire ».

À quoi sert `@st.cache_data` sur la fonction `charger` ?

Le décorateur @st.cache_data permet de conserver en mémoire le résultat du chargement du fichier CSV. Ainsi, Streamlit n'a pas besoin de relire les données à chaque interaction avec l'interface. Cela améliore les performances de l'application et réduit les traitements inutiles.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
        """
        Envoyer un relevé de capteurs à l'API MaintAI.

        reading : dictionnaire contenant les valeurs des capteurs.
        Retour : réponse JSON avec la probabilité de panne.

        Une APIError est levée si l'API refuse la requête.
        """

        # 1. Préparer les en-têtes HTTP.
        # On ajoute la clé API uniquement si elle est renseignée.
        headers = {}

        if self.api_key:
            headers["X-API-Key"] = self.api_key

        # 2. Envoyer les valeurs des capteurs à l'API.
        # self.http permet aussi d'utiliser un client simulé
        # dans les tests sans démarrer de serveur.
        response = self.http.post(
            "/v1/predict",
            json=reading,
            headers=headers
        )

        # 3. Vérifier si le serveur a accepté la requête.
        if response.status_code != 200:

            # Récupérer le message d'erreur renvoyé par l'API.
            detail = response.json().get("detail")

            # Lever une exception avec le code et le détail.
            raise APIError(response.status_code, detail)

        # 4. Si la requête réussit, retourner la réponse JSON.
        return response.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
23 passed, 1 warning in 11.92s
```

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé |Une probabilité de panne et un message indiquant si une alerte est déclenchée. |
| valeurs par défaut, fausse clé |Un avertissement avec le code HTTP 401 indiquant que la clé API est invalide. |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) |Un message d'erreur « API injoignable : vérifiez le serveur. » |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

CORS est un mécanisme de sécurité appliqué par les navigateurs aux requêtes HTTP entre différentes origines.

Dans le TP2, la page HTML utilisait JavaScript pour envoyer directement les requêtes à l'API depuis le navigateur. Le navigateur appliquait donc les règles CORS.

Dans le TP3, la requête HTTP est envoyée par le serveur Python Streamlit grâce à la bibliothèque httpx, et non directement par le navigateur.

Par conséquent, les restrictions CORS du navigateur ne s'appliquent pas à cette communication entre le serveur Streamlit et l'API FastAPI.

C'est pourquoi la prédiction fonctionne même si le port 8501 n'est pas présent dans MAINTAI_CORS_ORIGINS.

## 5. Questions de compréhension

**1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?**

Dans le TP2, la requête HTTP est envoyée directement par le navigateur grâce à JavaScript et à la fonction `fetch()`.

Dans le TP3, la requête est envoyée par le serveur Python Streamlit à l'aide de la bibliothèque `httpx`, à travers la méthode `MaintaiClient.predict()`.

Cette différence explique pourquoi les restrictions CORS du navigateur ne s'appliquent pas aux requêtes envoyées par Streamlit.

**2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?**

Les tests utilisent `TestClient` de FastAPI pour communiquer directement avec l'application, sans démarrer de serveur HTTP.

Ce client est transmis à `MaintaiClient` grâce au paramètre `http=client`.

Cela permet de tester les prédictions et les erreurs HTTP (401, 422) de manière rapide et automatisée, sans lancer uvicorn.

**3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?**

Pour une démonstration à un client, je choisirais Streamlit, car il permet de créer rapidement une interface interactive en Python avec des indicateurs et des graphiques.

Pour une application de maintenance utilisée en production, je privilégierais HTML + JavaScript, car cette solution offre davantage de possibilités pour personnaliser l'interface et améliorer l'expérience utilisateur.

Cependant, Streamlit reste un bon choix pour une première version interne destinée aux techniciens de maintenance.

## 6. Le rendu Git

- Lien de la pull request : …
- Le tag `tp3` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? oui / non

## 7. Ce qui reste flou

…
