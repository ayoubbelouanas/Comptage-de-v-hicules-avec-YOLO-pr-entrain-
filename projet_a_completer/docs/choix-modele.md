# Choix du modèle
Oussama BANANI & Ayoub BELOUANAS & Mohamed NEJJARI & Younes LAKBAB

Date : 26/10/2026 · Groupe : S3

## Contexte
Le but du projet est de prévoir le nombre de repas servis à la cantine en fonction des variables observées (date, météo, jours de semaine, inscriptions, etc.). La métrique principale retenue est la MAE (Mean Absolute Error), car elle représente l’écart moyen absolu entre les valeurs prédites et les valeurs réelles, ce qui est directement interprétable pour une cible quantitative.

## Données et découpage
Le jeu utilisé est le fichier `data/cantine_repas.csv`.
Il contient 340 lignes et 11 colonnes. La variable cible est `repas_servis`.
Le découpage est chronologique, avec une fraction de test de 20 % (`TEST_SIZE = 0.2`) pour respecter l’ordre temporel et évaluer la capacité de généralisation sur le futur.

## Résultats sur le jeu de test

| Modèle | MAE | RMSE | R2 |
|---|---:|---:|---:|
| Baseline | 70.271 | 88.416 | -0.151 |
| Ridge | 22.623 | 28.545 | 0.880 |
| Random Forest | 31.845 | 41.540 | 0.746 |
| KNN | 36.212 | 46.037 | 0.688 |
| HistGradientBoosting | 39.015 | 51.049 | 0.616 |

## Décision
Le modèle retenu est `ridge`, car il obtient la meilleure MAE sur le jeu de test : 22.623 contre 70.271 pour la baseline. Cela correspond à une amélioration de 47.648 points, soit environ 67.8 % d’écart moyen réduit par rapport à la ligne de base.
Le score R2 de 0.880 démontre aussi que le modèle explique correctement la variabilité des données. Le critère d’acceptation est donc atteint, car le modèle sélectionné surpasse clairement la baseline et garde une erreur absolue faible pour une prediction de quantité de repas.

## Limites
Ces résultats sont robustes pour le jeu disponible, mais ils ne couvrent pas tous les cas possibles : la série est courte, la saisonnalité peut être sous-estimée, et le comportement du service peut évoluer si des changements structurels apparaissent (nouveaux menus, événements exceptionnels, vacances, etc.). Le jeu de test étant limité à 20 % des données chronologiques, il reste important de surveiller les performances sur de nouvelles périodes.

## Annexe — Résultats avec `exemple_pannes.csv`

Cette annexe présente les résultats obtenus avec le jeu de pannes fourni dans `data/exemple_pannes.csv`. Elle correspond à une autre configuration du projet : la cible est `failure`, la tâche est une classification et la métrique principale est le rappel (`recall`). La configuration active dans `monprojet/config.py` reste celle de la cantine.

Le fichier contient 5 000 lignes et 5 colonnes : `temperature_c`, `vibration_mm_s`, `load_pct`, `runtime_hours` et `failure`. Il n'y a pas de valeurs manquantes. La cible est déséquilibrée : 4 122 observations sans panne (82,44 %) et 878 avec panne (17,56 %). Le découpage aléatoire stratifié utilise 4 000 lignes pour l'entraînement et 1 000 pour le test ; celui-ci contient 176 pannes.

| Modèle | Accuracy | Recall | Precision | F1 |
|---|---:|---:|---:|---:|
| Baseline (classe majoritaire) | 0.824 | 0.000 | 0.000 | 0.000 |
| Régression logistique | 0.889 | 0.574 | 0.737 | 0.645 |
| Random Forest | 0.873 | 0.545 | 0.671 | 0.602 |
| HistGradientBoosting | 0.881 | 0.574 | 0.697 | 0.629 |
| KNN | 0.878 | 0.540 | 0.699 | 0.609 |

La régression logistique est retenue parmi les modèles testés : son rappel de 0.574 est à égalité avec HistGradientBoosting, et sa précision et son F1 sont meilleurs. Elle détecte environ 57,4 % des pannes du jeu de test, contre 0 % pour la baseline. Ce rappel reste insuffisant pour considérer le modèle comme prêt à être utilisé seul : environ 42,6 % des pannes du test ne sont pas détectées. Un seuil d'acceptation métier doit être défini avant tout déploiement, en tenant compte du coût des fausses alertes et des pannes manquées.

Ces scores dépendent d'un seul découpage aléatoire et ne garantissent pas les mêmes performances sur de nouvelles machines ou dans le temps. Il faut notamment valider le modèle sur des données indépendantes et récentes avant tout usage opérationnel.
