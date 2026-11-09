# ADR 000 : Choix du modèle de classification pour la prédiction des pannes

**Date :** 09/11/2026
**Auteur :** BANANI OUSSAMA

## 1. Contexte

Le projet MaintAI a pour objectif de prédire les risques de panne à partir des données collectées par différents capteurs, notamment la température, les vibrations, la charge et les heures de fonctionnement.

Les données sont traitées par un modèle de classification dont les résultats sont ensuite mis à disposition à travers une API FastAPI. Cette API permet d'exploiter les prédictions depuis différentes interfaces, notamment une application Streamlit et un client web.

Le choix du modèle constitue donc une étape importante du projet. Il doit permettre d'obtenir des prédictions pertinentes tout en restant suffisamment simple à entraîner, à intégrer dans l'architecture existante et à maintenir.

## 2. Options étudiées

Deux grandes approches ont été envisagées :

### Option 1 : Régression logistique avec normalisation des données

Cette approche repose sur un pipeline Scikit-learn associant `StandardScaler` et `LogisticRegression`.

**Avantages :**

- Entraînement rapide et faible consommation de ressources.
- Bonne interprétabilité des résultats.
- Adaptation aux données numériques structurées.
- Possibilité d'obtenir directement des probabilités de panne.
- Intégration et sauvegarde simples dans l'application.

**Inconvénients :**

- Capacité limitée à représenter des relations complexes et non linéaires.
- Peut être moins performante lorsque les interactions entre les variables sont importantes.

### Option 2 : Modèles de classification plus complexes

Cette catégorie comprend notamment les arbres de décision et les forêts aléatoires.

**Avantages :**

- Capacité à identifier des relations non linéaires entre les variables.
- Meilleure prise en compte de certaines interactions entre les mesures des capteurs.
- Possibilité d'obtenir de bonnes performances sur des données complexes.

**Inconvénients :**

- Paramétrage et optimisation potentiellement plus importants.
- Complexité supplémentaire lors de l'entraînement et de la maintenance.
- Interprétation des résultats parfois moins directe.
- Solution plus élaborée que nécessaire pour une première version du projet.

## 3. Décision retenue

Après comparaison des différentes possibilités, le choix s'est porté sur un pipeline de classification utilisant **Scikit-learn, avec `StandardScaler` et `LogisticRegression`**.

Ce choix répond aux besoins de MaintAI, qui consiste à réaliser une classification binaire afin de distinguer les situations présentant un risque de panne de celles considérées comme normales.

L'utilisation de `StandardScaler` permet de normaliser les variables numériques avant leur traitement par le classificateur. La régression logistique permet ensuite d'estimer une probabilité de panne, qui peut être exploitée par l'application pour déterminer si une alerte doit être déclenchée.

Par ailleurs, le pipeline complet peut être sauvegardé avec `joblib`, puis rechargé lors du démarrage de l'API FastAPI.

Cette solution représente un compromis intéressant entre simplicité, interprétabilité, performances et facilité d'intégration dans l'architecture existante.

## 4. Conséquences de la décision

Le choix de cette approche présente plusieurs avantages pour le projet :

- Réduire la complexité de la phase d'entraînement.
- Faciliter la reproductibilité des expérimentations.
- Simplifier la sauvegarde et le rechargement du modèle avec `joblib`.
- Permettre une intégration directe dans l'API FastAPI et l'interface Streamlit.
- Faciliter l'analyse de l'influence des variables sur les prédictions.
- Fournir des probabilités exploitables pour la mise en place d'un système d'alerte.

Toutefois, certaines limites doivent également être prises en compte :

- Le modèle peut avoir des difficultés à représenter certaines relations non linéaires.
- Ses performances peuvent être limitées lorsque les données présentent des comportements plus complexes.
- Les résultats obtenus sur des données synthétiques ne garantissent pas les mêmes performances sur des données réelles.

Pour améliorer la fiabilité du système, il sera donc important de contrôler la qualité des données, d'évaluer régulièrement les performances du modèle et d'adapter le seuil de classification (`threshold`) aux besoins de la maintenance prédictive.

Si les performances deviennent insuffisantes, d'autres algorithmes, notamment les arbres de décision ou les forêts aléatoires, pourront être étudiés et comparés au modèle initial.

La décision pourra ainsi être réévaluée en fonction de l'évolution du projet et de la disponibilité de nouvelles données.
