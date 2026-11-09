# ADR 001 : Transformation de MaintAI en package Python installable

**Date :** 09/11/2026  
**Auteur :** BANANI OUSSAMA

## 1. Contexte

Le projet MaintAI doit évoluer d'une application composée de scripts Python exécutés directement depuis le répertoire source vers un package Python installable et réutilisable.

Cette évolution nécessite une organisation plus structurée du code, une déclaration centralisée des dépendances et la mise en place d'un point d'entrée permettant d'utiliser les fonctionnalités du projet directement depuis la ligne de commande.

Il est également nécessaire de garantir l'accès aux ressources indispensables au fonctionnement de l'application, notamment au modèle de prédiction, quel que soit le mode d'installation utilisé.

## 2. Options étudiées

Deux solutions ont été envisagées :

### Option 1 : Conserver le projet sous forme de scripts Python

Cette approche consiste à maintenir l'organisation actuelle et à exécuter les différents fichiers directement depuis le dossier du projet.

**Avantages :**
- Mise en place simple et rapide.
- Peu de modifications nécessaires dans la structure existante.
- Utilisation directe des scripts pendant le développement.

**Inconvénients :**
- Dépendance au répertoire depuis lequel les scripts sont exécutés.
- Réutilisation du code moins pratique dans d'autres environnements.
- Gestion des dépendances et des commandes moins centralisée.
- Absence d'une véritable interface d'installation standardisée.

### Option 2 : Transformer le projet en package Python

Cette solution consiste à organiser MaintAI sous forme de package Python et à utiliser un fichier `pyproject.toml` pour définir sa configuration.

**Avantages :**
- Centralisation des métadonnées et des dépendances du projet.
- Installation simplifiée dans différents environnements Python.
- Possibilité de définir des commandes accessibles depuis le terminal.
- Meilleure organisation du code et facilité de réutilisation.
- Compatibilité avec les mécanismes standards de distribution Python.

**Inconvénients :**
- Nécessité d'adapter la structure et la configuration du projet.
- Gestion supplémentaire des ressources externes, notamment du modèle entraîné.
- Attention particulière à apporter aux chemins d'accès et à la compatibilité des dépendances.

## 3. Décision retenue

Nous avons choisi de transformer MaintAI en un package Python installable, en utilisant le fichier `pyproject.toml` pour déclarer les métadonnées, les dépendances et le point d'entrée de l'application.

L'installation en mode éditable est réalisée avec la commande :

```bash
pip install -e .
```

Ce mode d'installation permet de travailler directement sur le code source sans devoir réinstaller le package après chaque modification.

La configuration prévoit également l'accès aux fonctionnalités du projet depuis la ligne de commande, notamment à travers la commande `maintai-predict`.

Cette décision répond aux objectifs du TP4 et permet de rendre le projet plus modulaire, plus facile à utiliser et mieux organisé.

## 4. Conséquences de la décision

La transformation en package Python apporte plusieurs améliorations :

- Faciliter l'installation et l'utilisation de MaintAI dans différents environnements.
- Centraliser la configuration et la gestion des dépendances dans `pyproject.toml`.
- Simplifier l'exécution des fonctionnalités grâce à un point d'entrée CLI.
- Améliorer la réutilisation et la maintenance du code.
- Faciliter les tests et les évolutions futures du projet.

Cependant, cette évolution implique également certaines contraintes techniques.

Le modèle de prédiction doit notamment être accessible indépendamment de l'emplacement du package installé, en particulier lors d'une installation à partir d'un fichier Wheel.

Pour répondre à cette contrainte, le chemin d'accès aux modèles doit être configurable à l'aide de la variable d'environnement `MAINTAI_MODELS_DIR`.

Enfin, il est important de contrôler la compatibilité des versions des bibliothèques utilisées, notamment celle de `scikit-learn`, afin de garantir le bon fonctionnement du modèle lors de son chargement et de son utilisation.

Cette décision constitue ainsi une étape importante dans la structuration de MaintAI et prépare le projet à une distribution et une utilisation dans différents environnements Python.