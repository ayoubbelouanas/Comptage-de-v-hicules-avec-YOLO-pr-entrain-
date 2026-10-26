# Compte rendu · TP1 : une API de prédiction pour MaintAI

 ·  *Date :* 26 octobre 2026  oussama banani



---

## 1. Mise en place

Dernière ligne de python -m pytest, juste après la mise en place (rien n'est encore écrit) :


Résultat historique à relever au moment de cette étape. Il ne peut pas être reconstitué
fidèlement à partir du projet actuel, où les fichiers ont été complétés.


Le résultat attendu était *10 passed, 3 failed* sur l'ensemble de la suite.
Les trois tests de prédiction recevaient un 422 parce qu'aucun champ n'était encore
déclaré dans SensorReading.

Les quatre tests qui passent sont test_health, test_out_of_range_value_is_rejected,
test_missing_field_is_rejected et test_openapi_documents_predict.
Les deux tests 422 passent pour une mauvaise raison : le schéma SensorReading ne
déclare encore aucun champ, et extra="forbid" rejette donc tous les champs envoyés,
y compris les champs normalement valides. Il faut déclarer les champs et leurs bornes
pour que le 422 soit bien causé par une valeur réellement hors limites.

Les trois tests de prédiction ne passent donc pas encore à cette étape : les relevés
valides sont traités à tort comme des relevés contenant uniquement des champs interdits.

## 2. Le schéma d'entrée (maintai/api/schemas.py)

| Variable | Type | Minimum (ge) | Maximum (le) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| temperature_c | float | -40 °C | 150 °C | Plage étendue pour mesurer la température d'une machine, du froid industriel à une surchauffe importante. |
| vibration_mm_s | float | 0 mm/s | 50 mm/s | Une vitesse vibratoire ne peut pas être négative ; 50 mm/s couvre des vibrations anormalement fortes. |
| load_pct | float | 0 % | 100 % | Pourcentage de charge : de la charge nulle à la capacité nominale. |
| runtime_hours | float | 0 h | 20 000 h | Un compteur de fonctionnement ne peut pas être négatif ; 20 000 h représente la limite couverte par ce modèle. |

Après avoir écrit schemas.py seul, que donne python -m pytest, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?


Étape intermédiaire historique non exécutée dans cette session. Avec le `main.py`
initial qui contient encore `raise NotImplementedError`, le résultat attendu est
**10 passed, 3 failed** : les trois tests de prédiction échouent avec `NotImplementedError`,
car les validations du schéma laissent désormais passer les entrées valides jusqu'à
la fonction inachevée.


C'est bon signe : les relevés invalides sont rejetés par Pydantic, tandis que les
relevés valides arrivent jusqu'à la fonction predict(). Les erreurs restantes
indiquent que l'implémentation métier de cette fonction est la prochaine étape.

## 3. La fonction predict() (maintai/api/main.py)

Votre code :

python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(status_code=503, detail="Le modèle de prédiction n'est pas chargé.")

return predictor.predict(reading.model_dump())


Pourquoi répondre *503* et pas 500 quand le modèle manque ?

503 signifie que le service est temporairement indisponible : l'API fonctionne, mais
elle ne peut pas faire de prédiction tant que le modèle n'est pas disponible. 500
indiquerait plutôt une erreur interne inattendue.

Pourquoi le modèle est-il chargé *une seule fois*, au démarrage, et pas à chaque requête ?

Le chargement au démarrage évite de relire le fichier du modèle et de reconstruire le
prédicteur à chaque requête. Cela réduit le temps de réponse et centralise la gestion
de l'état du modèle. Le gestionnaire lifespan le charge une fois et le conserve
dans state pendant la durée de vie de l'application.

## 4. Les tests

Dernière ligne de python -m pytest à la fin du TP :


13 passed in 4.74s


## 5. L'API en marche

Après python -m maintai.dataset et python -m maintai.train, lancez uvicorn maintai.api.main:app --reload, puis envoyez ces requêtes depuis /docs (ou avec curl.exe).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| GET /health | 200 | {"status":"ok","model_loaded":true} |
| POST /v1/predict avec {"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000} | 200 | {"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-26T12:27:12Z"} |
| POST /v1/predict avec une température de 500 | 422 | {"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]} |
| POST /v1/predicte (faute de frappe dans l'adresse) | 404 | {"detail":"Not Found"} |

Ces résultats de prédiction ont été obtenus après un entraînement avec les données
synthétiques du projet. La probabilité et la version peuvent changer si le modèle ou
les données sont différents.

Dans /docs, ouvrir POST /v1/predict puis consulter le schéma du corps de requête
(SensorReading) : les bornes apparaissent dans les contraintes des propriétés.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un style architectural pour concevoir des API HTTP (ressources, méthodes
   et codes de réponse). FastAPI est un framework Python qui permet d'implémenter une
   API, notamment en suivant les principes REST.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   Il valide et convertit les données reçues, documente le format attendu dans OpenAPI
   (donc dans /docs) et fournit une structure typée exploitable par le code.
3. Dans http://localhost:8000/v1/predict, que désignent localhost, 8000 et /v1/predict ?
   localhost désigne la machine locale, 8000 le port du serveur, et /v1/predict
   le chemin de la route de prédiction.
4. Pourquoi /v1 dans l'adresse ?
   Il indique la version 1 de l'API. Une nouvelle version avec un contrat incompatible
   peut être publiée sous un autre chemin sans casser immédiatement les clients existants.
5. Dans la commande uvicorn maintai.api.main:app, que désignent maintai.api.main et app ?
   maintai.api.main est le chemin Python du module à importer ; app est l'objet
   FastAPI exposé par ce module et servi par Uvicorn.

## 7. Le rendu Git

- Lien de la pull request : aucune ; le compte rendu a été poussé directement sur main.
- Le tag tp1 existe sur GitHub : non (aucun tag tp1 n'est présent dans le dépôt).
- Commits du compte rendu :
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  Sans objet : aucune pull request n'a été créée, donc aucune relecture de PR ni aucun commentaire de review n'est enregistré.

## 8. Ce qui reste flou


Aucune question pour le moment. Le TP m’a permis de comprendre la validation des données avec Pydantic, le fonctionnement d’une API FastAPI et les tests automatisés avec pytest.