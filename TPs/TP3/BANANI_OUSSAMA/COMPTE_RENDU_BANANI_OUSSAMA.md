# Compte rendu – TP3 : Développement d’une interface Streamlit pour MaintAI

**Étudiante :** BANANI OUSSAMA<br>
**Date :** 09/11/2026

## 1. Mise en place de l’environnement

Lors de la première exécution de la commande `python -m pytest` dans le dossier `TP/TP3`, le résultat obtenu était le suivant :

```text
1 failed, 22 passed, 1 warning in 9.30s
```

**Fichier de test concerné :**

Le problème provenait du fichier `tests/test_ui.py`, plus précisément du test :

```text
tests/test_ui.py::test_ui_shows_the_prediction
```

Deux erreurs ont été identifiées au cours des corrections :

1. La fonction de prédiction récupérait une clé incorrecte dans la réponse de l'API. Le code utilisait `probability` au lieu de `failure_probability`, ce qui provoquait une `KeyError`. De plus, l'indicateur affiché ne correspondait pas au résultat attendu : le test attendait une probabilité de 95 %, alors que la dernière valeur récupérée était la température (59,7 °C).

2. Après la première correction, une nouvelle erreur est apparue dans `ui/app.py` :

```text
NameError: name 'pct' is not defined
```

Cette erreur était liée à l'utilisation de la variable `pct` dans `st.metric()` avant sa définition.

Après correction de ces deux problèmes, l'ensemble des tests a été validé à la fin du sprint 2, avec **23 tests réussis**.

## 2. Démarrage de l'application Streamlit

La commande initialement prévue pour lancer l'application était :

```powershell
streamlit run ui/app.py
```

Cependant, la commande effectivement utilisée et documentée est :

```powershell
python -m streamlit run ui/app.py
```

Lors du premier lancement, Streamlit a affiché son message de bienvenue et proposé de renseigner une adresse e-mail. Une erreur `FileNotFoundError` est ensuite apparue, indiquant que le fichier `data/sensors.csv` était introuvable dans le dossier TP3.

Pour résoudre ce problème, le fichier a été récupéré depuis le projet TP2 et copié dans le répertoire approprié à l'aide de la commande suivante :

```powershell
Copy-Item "C:\Users\pc\Downloads\S5_maintai-starter-tp2\maintai-starter-tp2\data\sensors.csv" ".\data\sensors.csv"
```

Une fois le fichier ajouté, l'application a démarré correctement et est devenue accessible à l'adresse :

```text
http://localhost:8501
```

**Pourquoi utiliser `python -m streamlit` ?**

Cette commande permet d'exécuter directement le module Streamlit à partir de l'interpréteur Python sélectionné. Elle est particulièrement utile lorsque la commande `streamlit` n'est pas reconnue par Windows, notamment lorsque son exécutable n'est pas présent dans la variable d'environnement `PATH` ou lorsqu'il existe plusieurs environnements Python.

## 3. Sprint 1 : Exploration des données

Le premier sprint consistait à développer l'onglet « Données » afin de présenter les principales caractéristiques du jeu de données et de proposer des visualisations interactives.

Le code suivant a été utilisé :

```python
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
```

### Résultats de l'exploration

À partir du fichier `data/sensors.csv`, les trois indicateurs suivants ont été obtenus :

| Indicateur | Résultat |
|---|---:|
| Nombre total de relevés | 5 000 |
| Taux de panne | 13,6 % |
| Température moyenne | 59,8 °C |

**Analyse du taux de panne en fonction de la vibration**

Après avoir sélectionné la variable `vibration_mm_s`, on constate une tendance générale à l'augmentation du taux de panne lorsque le niveau de vibration devient plus élevé.

Cette relation n'est toutefois pas parfaitement régulière d'une tranche à l'autre, en raison de la variabilité présente dans les données synthétiques.

On peut donc conclure que, dans ce jeu de données, une augmentation des vibrations est globalement associée à une augmentation du risque de panne.

**Observation du fonctionnement de Streamlit**

Pour comprendre le mécanisme de fonctionnement de Streamlit, l'instruction suivante a été ajoutée au début de `ui/app.py` :

```python
print("relance")
```

Lorsqu'une interaction déclenche une mise à jour de l'application, le message `relance` apparaît dans le terminal.

Cela s'explique par le fonctionnement de Streamlit, qui réexécute automatiquement le script Python lorsqu'une interaction utilisateur nécessite une actualisation de l'interface.

Dans notre application, les curseurs de prédiction étant intégrés dans un formulaire `st.form`, leurs modifications sont prises en compte lors de la validation du formulaire, notamment après le clic sur le bouton « Prédire ».

**Rôle de `@st.cache_data`**

Le décorateur `@st.cache_data` permet de conserver en mémoire le résultat du chargement des données.

Ainsi, lorsque Streamlit réexécute le script avec les mêmes paramètres, le DataFrame déjà chargé peut être réutilisé sans effectuer une nouvelle lecture du fichier CSV.

Cette fonctionnalité permet de réduire les opérations répétitives et d'améliorer les performances de l'application.

## 4. Sprint 2 : Mise en place de la prédiction

Le deuxième sprint avait pour objectif d'intégrer l'API FastAPI à l'interface Streamlit afin de permettre à l'utilisateur de soumettre des mesures de capteurs et d'obtenir une estimation du risque de panne.

### Méthode `predict` dans `maintai/client.py`

La méthode suivante a été utilisée pour communiquer avec l'API :

```python
def predict(self, reading: dict) -> dict:
    """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
    headers = {}
    if self.api_key:
        headers["X-API-Key"] = self.api_key

    r = self.http.post(
        "/v1/predict",
        json=reading,
        headers=headers
    )

    if r.status_code != 200:
        raise APIError(r.status_code, r.json().get("detail"))

    return r.json()
```

Cette méthode transmet les données à l'endpoint `/v1/predict`, ajoute la clé API lorsqu'elle est disponible et retourne le résultat fourni par le serveur. Elle permet également de gérer les erreurs HTTP lorsque la requête échoue.

### Validation des tests

À la fin du sprint 2, la commande `python -m pytest` a produit le résultat suivant :

```text
=============================== 23 passed, 1 warning in 7.05s ================================
```

Les 23 tests ont donc été exécutés avec succès.

Le seul avertissement restant est un `StarletteDeprecationWarning`, concernant l'utilisation de `httpx` avec `starlette.testclient`. Il s'agit d'un avertissement de dépréciation et non d'un échec de test.

### Vérification des différents scénarios

Avec l'API démarrée, plusieurs situations ont été prises en compte :

| Scénario | Résultat attendu dans Streamlit |
|---|---|
| Valeurs par défaut avec une clé API valide | Affichage d'une probabilité de panne de 95 % et du message « ALERTE : risque de panne détecté ! » |
| Utilisation d'une clé API incorrecte | Affichage d'un avertissement signalant une erreur 401 et une clé absente ou invalide |
| API arrêtée avec Ctrl+C dans le terminal Uvicorn | Affichage d'un message indiquant que l'API est injoignable, accompagné du détail de l'erreur de connexion |

### Entraînement et vérification du modèle

Lors du premier test de communication avec l'API, un message indiquait que le modèle n'était pas encore chargé.

Pour résoudre ce problème, j'ai lancé la commande suivante :

```powershell
python -m maintai.train
```

Cette opération a permis d'entraîner le modèle et de sauvegarder le résultat dans `models/model.joblib`.

Les métriques obtenues sont présentées ci-dessous :

| Métrique | Modèle | Baseline |
|---|---:|---:|
| Accuracy | 0,904 | 0,864 |
| Recall | 0,75 | 0,0 |
| Precision | 0,622 | Non indiquée |
| Seuil | 0,3 | Non indiqué |

Après le redémarrage de l'API et la configuration de la clé d'authentification, une requête POST a retourné les résultats suivants :

```text
failure_probability : 0.9553
alert               : True
threshold           : 0.3
```

La probabilité de panne calculée est donc de **95,53 %**. Comme cette valeur dépasse le seuil de décision fixé à 0,3, une alerte est déclenchée.

Dans l'interface Streamlit, cette probabilité est affichée sous la forme arrondie de **95 %**.

### Pourquoi la prédiction fonctionne-t-elle lorsque le port 8501 n'est pas présent dans `MAINTAI_CORS_ORIGINS` ?

Le port 8501 correspond au serveur Streamlit, tandis que l'API FastAPI fonctionne sur un autre port.

Dans cette architecture, le navigateur communique avec Streamlit, puis le code Python de l'application envoie lui-même les requêtes à l'API à l'aide de `httpx`.

La communication avec l'API est donc effectuée côté serveur et non directement depuis le navigateur. Par conséquent, la politique CORS du navigateur ne s'applique pas à cet appel serveur-à-serveur.

C'est pour cette raison que la prédiction fonctionne même si le port 8501 ne figure pas dans `MAINTAI_CORS_ORIGINS`.

## 5. Questions de compréhension

### 1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?

Dans le TP2, les requêtes sont envoyées directement par le navigateur à l'aide du JavaScript et de la fonction `fetch()`.

En revanche, dans le TP3, c'est le code Python de Streamlit qui communique avec l'API à travers le client `MaintaiClient`, en utilisant la bibliothèque `httpx`.

La principale différence réside donc dans le lieu d'exécution de la requête HTTP : côté navigateur pour le TP2 et côté serveur Python pour le TP3.

### 2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'Uvicorn ?

Les tests utilisent le `TestClient` de FastAPI, qui permet d'envoyer des requêtes directement à l'application ASGI en mémoire.

Le client de test est ensuite utilisé par `MaintaiClient` pour vérifier le comportement des requêtes et les réponses de l'API.

Il n'est donc pas nécessaire de démarrer un véritable serveur Uvicorn. Cette méthode simplifie les tests, réduit leur temps d'exécution et permet de vérifier le fonctionnement de l'API sans dépendre d'un serveur réseau actif.

### 3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?

Pour une démonstration rapide à un client, je privilégierais **Streamlit**. Cette solution permet de développer rapidement une interface interactive, de présenter les données sous forme de graphiques et de tester directement les prédictions du modèle.

En revanche, pour une application destinée à être utilisée quotidiennement par des techniciens de maintenance, je choisirais plutôt **une interface HTML + JavaScript personnalisée**. Elle offre davantage de flexibilité pour concevoir une expérience utilisateur adaptée aux besoins professionnels, aux différents appareils et aux fonctionnalités spécifiques du métier.

## 6. Rendu et gestion du dépôt Git

**Dépôt GitHub :**

(https://github.com/ayoubbelouanas/Comptage-de-v-hicules-avec-YOLO-pr-entrain-/edit/main/TPs/TP3)

**Pull Request :**

Aucune Pull Request n'a été ouverte pour le moment. Les Pull Requests existantes sont actuellement fermées.

**Vérification du tag `tp3` :**

Le tag `tp3` a bien été créé sur GitHub. Il pointe vers le commit suivant :

```text
6c06bb7
```

Ce commit appartient à la branche `main`.

**État du dépôt avant le commit :**

La commande `git status` affichait :

```text
On branch main
Your branch is up to date with 'origin/main'
nothing to commit, working tree clean
```

Le dépôt local était donc synchronisé avec le dépôt distant et ne contenait aucune modification en attente de commit.

**Gestion des fichiers sensibles et des ressources :**

Le fichier `.env` contient des paramètres de configuration sensibles, notamment la clé API. Il doit rester exclu du dépôt Git afin d'éviter toute divulgation d'informations confidentielles.

Les fichiers `data/sensors.csv` et `models/model.joblib` doivent également être gérés conformément aux consignes du TP et aux règles définies dans le fichier `.gitignore`.

## 7. Points restant à approfondir

Le principal point qui nécessite encore des recherches concerne l'avertissement `StarletteDeprecationWarning` rencontré pendant l'exécution des tests.

Cet avertissement signale une évolution concernant l'utilisation de `httpx` avec `starlette.testclient` et recommande de se renseigner sur la compatibilité avec `httpx2`.

Il serait intéressant d'étudier les conséquences de cette dépréciation sur le projet et d'identifier la meilleure manière de mettre à jour les dépendances tout en conservant la compatibilité avec les tests existants.

## Conclusion

Ce troisième TP m'a permis de mettre en pratique le développement d'une interface interactive avec Streamlit et son intégration à une API FastAPI dans le cadre d'un projet de maintenance prédictive.

J'ai pu réaliser plusieurs fonctionnalités, notamment l'exploration statistique des données, la visualisation des mesures des capteurs, la soumission de relevés et l'affichage des probabilités de panne.

Les différentes corrections apportées au cours des deux sprints ont permis de résoudre les problèmes rencontrés lors du chargement des données, de l'initialisation du modèle et de l'affichage des résultats.

Enfin, l'exécution des tests automatisés a confirmé le bon fonctionnement des fonctionnalités développées, avec **23 tests réussis**.

Ce travail m'a également permis de mieux comprendre la communication entre une interface utilisateur et une API, la gestion des erreurs HTTP, le fonctionnement de Streamlit ainsi que l'importance des tests dans le développement d'une application.

Le TP3 aboutit ainsi à une interface fonctionnelle permettant d'exploiter les résultats du modèle de maintenance prédictive de MaintAI.
