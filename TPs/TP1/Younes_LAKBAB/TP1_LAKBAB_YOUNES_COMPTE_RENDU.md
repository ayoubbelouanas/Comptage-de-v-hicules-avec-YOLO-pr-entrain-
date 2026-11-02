# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :**  ·  **Membres :** Younes LAKBAB  ·  **Date :** 02-11-2026

> Ce compte rendu suit les huit rubriques du fichier `COMPTE_RENDU.md` fourni par le professeur. Les explications et le code sont rédigés ; les sorties personnelles du terminal, les réponses de l'API et les informations Git doivent être vérifiées avant le rendu. Les résultats « attendus » ne sont pas présentés comme des mesures réalisées sur mon ordinateur.

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```text
3 failed, 10 passed
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

Les quatre tests sont `test_health`, `test_out_of_range_value_is_rejected`, `test_missing_field_is_rejected` et `test_openapi_documents_predict`.

Les deux tests de rejet (`test_out_of_range_value_is_rejected` et `test_missing_field_is_rejected`) passent initialement pour une mauvaise raison. En effet, `SensorReading` ne possède encore aucun champ et la configuration `extra="forbid"` interdit tous les champs supplémentaires. Même un relevé valide est donc rejeté avec un code **422**. Cela ne prouve pas que la température hors limites ou le champ manquant sont réellement contrôlés.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | -40 | 150 | Permet de couvrir des températures basses et un échauffement important d'un moteur ; au-delà, le relevé sort de la plage retenue. |
| `vibration_mm_s` | `float` | 0 | 50 | Une vitesse de vibration ne peut pas être négative ; 50 mm/s laisse une marge pour des vibrations très élevées. |
| `load_pct` | `float` | 0 | 100 | Une charge en pourcentage de la capacité nominale varie ici de 0 % à 100 %. |
| `runtime_hours` | `float` | 0 | 100000 | Un compteur d'heures cumulées ne peut pas être négatif et peut dépasser plusieurs années d'utilisation. |

Les quatre champs sont déclarés avec `Field(ge=..., le=..., description=...)`. Le type `float` autorise aussi les valeurs décimales. `ConfigDict(extra="forbid")` est conservé afin de refuser les champs inconnus.

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```text
3 failed, 10 passed
Erreur caractéristique : NotImplementedError dans predict()
```


C'est un bon signe : le schéma reconnaît désormais les mesures valides et la requête atteint la fonction `predict()`. Les trois tests qui nécessitent une prédiction échouent encore parce que cette fonction n'est pas implémentée : `test_predict_returns_probability`, `test_high_risk_reading_raises_alert` et `test_503_when_model_missing`.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
def predict(reading: SensorReading) -> PredictionOut:
    """Renvoie la prédiction pour un relevé validé."""
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API",
        )
    return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

Le code **503 Service Unavailable** indique que l'API fonctionne, mais que le service de prédiction est indisponible parce que le modèle n'est pas chargé. Un code **500** évoquerait plutôt une erreur interne inattendue. Le message d'erreur peut indiquer comment résoudre le problème : entraîner le modèle, puis redémarrer l'API.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Le chargement du modèle peut prendre du temps et consommer des ressources. Le charger une seule fois pendant le démarrage de FastAPI évite de relire `model.joblib` à chaque prédiction. Les demandes suivantes réutilisent donc le même objet en mémoire, ce qui réduit le temps de réponse.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```text
13 passed
```


## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | **200 attendu** — à vérifier | `{"status":"ok","model_loaded":true}` si le modèle est chargé ; sinon `model_loaded` vaut `false`. |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | **200 attendu** — à vérifier | Objet avec `failure_probability`, `alert`, `threshold` (0.3) et `model_version`. Les valeurs exactes dépendent du modèle entraîné. |
| `POST /v1/predict` avec une température de 500 | **422 attendu** — à vérifier | Objet `detail` précisant que `temperature_c` dépasse la borne maximale autorisée de 150 °C. |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | **404 attendu** — à vérifier | `{"detail":"Not Found"}`. |


Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans la documentation Swagger, j'ouvre la route **POST `/v1/predict`**, puis la description du corps de requête et le schéma **`SensorReading`**. On y trouve chaque champ, son type, sa description et les contraintes `minimum` et `maximum` produites par Pydantic.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?

   **Réponse :** REST est un style de conception des services web qui recommande des routes, des méthodes HTTP et des représentations cohérentes. FastAPI est un framework Python qui permet de programmer une API selon ces principes.

2. Le schéma Pydantic sert à trois choses. Lesquelles ?

   **Réponse :** Il **valide** les types et les bornes des données reçues, **documente** automatiquement l'API avec OpenAPI/Swagger et **fournit** à la fonction de prédiction un objet Python typé.

3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?

   **Réponse :** `localhost` est l'ordinateur qui exécute l'API, `8000` est le port d'écoute du serveur et `/v1/predict` est la route utilisée pour demander une prédiction.

4. Pourquoi `/v1` dans l'adresse ?

   **Réponse :** `/v1` indique la première version de l'API. Plus tard, une version `/v2` pourrait évoluer sans interrompre immédiatement les clients de `/v1`.

5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?

   **Réponse :** `maintai.api.main` désigne le module Python situé dans `maintai/api/main.py`. `app` désigne l'objet `FastAPI` créé dans ce module et exécuté par Uvicorn.

## 7. Le rendu Git

- Lien de la pull request : **[à renseigner avec le lien réel]**.
- Le tag `tp1` existe sur GitHub : **[oui / non — à vérifier]**.
- Qui a relu la pull request, et quel commentaire a-t-il laissé ? **[nom du relecteur et commentaire réel à ajouter]**.

Le dépôt ne doit pas contenir `.venv`, les données CSV générées ni les fichiers du modèle dans `models/`. Le compte rendu et l'ADR 002 doivent accompagner les fichiers source.

## 8. Ce qui reste flou

La principale difficulté rencontrée concerne la distinction entre une erreur de validation **422** et un service de prédiction indisponible **503**. Une valeur impossible doit être rejetée par Pydantic avant l'appel du modèle, tandis qu'une entrée valide peut malgré tout renvoyer 503 si le modèle n'a pas été chargé. Ce point se vérifie avec les tests et avec la route `/health`.
