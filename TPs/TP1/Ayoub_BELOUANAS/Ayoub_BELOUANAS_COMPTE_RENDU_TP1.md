# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :**  · **Membres :** Ayoub BELOUANAS · **Date :** 26-10-2026

> Le rapport est rendu avec le code dans la pull request du TP1. Les informations de groupe, de pull request et de relecture restent à compléter par l'équipe.

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
3 failed, 10 passed
```

Cette sortie initiale n'a pas été conservée ; c'est le résultat attendu indiqué dans le polycopié.

Les quatre tests qui passent déjà dans `tests/test_api.py` sont `test_health`, `test_out_of_range_value_is_rejected`, `test_missing_field_is_rejected` et `test_openapi_documents_predict`.

Les deux tests qui attendent 422 passent pour une mauvaise raison : avec le schéma vide et `extra="forbid"`, Pydantic refuse tous les champs envoyés, y compris les champs valides. Le 422 ne prouve donc pas encore que les limites sont correctes ni que le champ manquant est détecté.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---:|---:|---:|---|
| `temperature_c` | `float` | -40 | 150 | Couvre des conditions très froides et les températures élevées qu'un moteur peut atteindre. |
| `vibration_mm_s` | `float` | 0 | 50 | Une vibration ne peut pas être négative ; 50 mm/s couvre un état fortement dégradé. |
| `load_pct` | `float` | 0 | 100 | La charge est exprimée en pourcentage de la capacité nominale. |
| `runtime_hours` | `float` | 0 | 100000 | Le compteur d'heures ne peut pas être négatif ; 100000 h représente plus de onze ans de fonctionnement continu. |

Après avoir écrit `schemas.py` seul, le polycopié prévoit encore trois échecs : les relevés valides atteignent `predict()`, qui n'est pas encore implémentée à cette étape et lève `NotImplementedError`. C'est un bon signe : le schéma laisse désormais passer les entrées valides et la requête atteint l'étape suivante.

Les tests concernés sont `test_predict_returns_probability`, `test_high_risk_reading_raises_alert` et `test_503_when_model_missing`. La sortie intermédiaire exacte n'a pas été conservée ; le polycopié indique trois échecs à cette étape.

```
3 failed — NotImplementedError dans predict()
```

## 3. La fonction `predict()` (`maintai/api/main.py`)

```python
def predict(reading: SensorReading) -> PredictionOut:
    """Prédit le risque de panne à partir d'un relevé déjà validé.

    Args:
        reading: Mesures de capteurs validées par le schéma SensorReading.

    Raises:
        HTTPException: Si le modèle n'est pas chargé, avec le statut 503.

    Returns:
        PredictionOut: Probabilité de panne, état d'alerte et version du modèle.
    """
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Le modèle de prédiction est indisponible.",
        )
    return PredictionOut(**predictor.predict(reading.model_dump()))
```

On répond **503** parce que le service est temporairement indisponible faute de modèle. Le code 500 signalerait plutôt une erreur interne inattendue.

Le modèle est chargé une seule fois au démarrage pour éviter de relire et recharger ses fichiers à chaque requête, ce qui réduirait les performances.

## 4. Les tests

Dernière ligne de la suite complète actuelle de `python -m pytest` :

```
19 passed, 1 warning in 3.31s
```

La suite complète comprend les cinq cas paramétrés ajoutés dans `tests/test_casser.py`. Sans ce fichier, les tests TP1 présents dans ce dépôt donnent `14 passed, 1 warning`. La fiche annonce 13 tests pour son starter ; cette copie en contient un de plus.

## 5. L'API en marche

Requêtes envoyées à l'application locale avec le modèle chargé :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---:|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec le relevé normal de l'exemple | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-11-02T09:34:54Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, les bornes apparaissent dans le schéma `SensorReading` du corps de la requête `POST /v1/predict`, avec le type et la description de chaque champ.

## 6. Questions de compréhension

1. **REST et FastAPI : quelle est la différence ?**

   REST est un ensemble de règles de conception pour les API web. FastAPI est une bibliothèque Python qui permet de créer une API en suivant ces règles.

2. **Le schéma Pydantic sert à trois choses. Lesquelles ?**

   Il valide les données reçues, génère la documentation OpenAPI affichée dans `/docs`, et fournit à la fonction un objet Python typé.

3. **Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?**

   `localhost` désigne la machine locale, `8000` le port sur lequel le serveur écoute, et `/v1/predict` le chemin de la route de prédiction.

4. **Pourquoi `/v1` dans l'adresse ?**

   `/v1` indique la version du contrat de l'API. Une future version pourra évoluer sous `/v2` sans casser immédiatement les clients qui utilisent `/v1`.

5. **Dans `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?**

   `maintai.api.main` est le chemin Python vers le module `maintai/api/main.py`. `app` est la variable de ce module qui contient l'application FastAPI.

## 7. Le rendu Git

- **Lien de la pull request :** 
- **Le tag `tp1` existe sur GitHub :** 
- **`.env` apparaissait-il dans `git status` avant le commit ?** le projet n'utilise pas de fichier `.env`.
- **Relecture :** 

## 8. Ce qui reste flou


