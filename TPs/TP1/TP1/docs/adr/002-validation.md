# ADR 002 : Validation des relevés et disponibilité du modèle

Date : 02/11/2026 · Auteurs : Ayoub BELOUANAS et l'équipe MaintAI

## Contexte

L'API reçoit des mesures de capteurs qui doivent être plausibles avant d'être
transmises au modèle. Elle doit également distinguer une indisponibilité
temporaire du modèle d'une erreur interne.

## Options étudiées

1. **Bornes physiques larges** : accepter les valeurs plausibles pour un moteur
   réel, même si elles dépassent les valeurs observées dans le jeu de données.
   Cela évite de rejeter inutilement de nouvelles machines, au prix d'un
   contrôle moins strict des valeurs extrêmes.
2. **Bornes copiées sur `sensors.csv`** : contrôler strictement les valeurs
   observées. Cette option rejette toutefois des relevés réels valides qui
   sortent de l'échantillon d'entraînement.

Pour le modèle absent :

1. **Répondre 503** : l'API reste disponible pour la supervision et indique
   qu'elle est temporairement incapable de servir les prédictions.
2. **Refuser de démarrer** : aucun trafic ne peut atteindre une API sans modèle,
   mais la supervision et les endpoints de santé deviennent indisponibles.

## Décision

Nous retenons des bornes physiques larges :

- température : `-40` à `150 °C` ;
- vibration : `0` à `50 mm/s` ;
- charge : `0` à `100 %` ;
- durée de fonctionnement : `0` à `100000 heures`.

Ces limites correspondent respectivement à une plage de température moteur
réaliste, à une vibration non négative pouvant couvrir un état fortement
dégradé, à la charge nominale exprimée en pourcentage et à une durée positive
permettant de représenter des équipements anciens.

Si le modèle manque, l'application démarre et `/health` reste consultable,
tandis que `/v1/predict` répond `503`. Ce code signale une indisponibilité
temporaire au client, contrairement à `500` qui indiquerait une erreur
inattendue du serveur.

## Conséquences

Pydantic rejette les valeurs impossibles avec `422` avant l'appel au modèle et
documente les bornes dans OpenAPI. Une borne large laisse passer certaines
valeurs extrêmes ; les limites devront donc être réévaluées avec des données
industrielles. Le démarrage sans modèle facilite la supervision, mais les
clients doivent traiter explicitement la réponse `503`.
