# Compte rendu – TP4 : Transformation de MaintAI en package Python

**Groupe :** …  
**Membre :** BANANI OUSSAMA
**Date :** 09/11/2026

> Chaque partie de ce compte rendu présente les manipulations réalisées, les résultats obtenus et les notions techniques abordées au cours du TP4.

---

## 1. Mise en place de l'environnement

Le travail a été réalisé dans le dossier `TP/TP4`, avec un environnement virtuel `.venv` dédié afin d'isoler les dépendances du projet.

Après l'installation des bibliothèques à l'aide de la commande `pip install -r requirements.txt`, la première exécution des tests a donné le résultat suivant :

```text
2 failed, 25 passed
```

**Quels sont les deux tests en échec et pourquoi ?**

Les deux tests en échec concernaient l'installation et l'importation du package `maintai`.

Le problème venait du fait que l'installation des dépendances avec `pip install -r requirements.txt` installe uniquement les bibliothèques nécessaires, mais ne rend pas automatiquement le projet lui-même accessible comme un package Python.

Pour résoudre ce problème, il a fallu installer le projet en mode éditable à l'aide de la commande :

```powershell
pip install -e .
```

Cette installation permet à Python de reconnaître le package `maintai` et d'accéder directement à son code source.

## 2. Sprint 1 : Configuration de `pyproject.toml` et installation éditable

### Déclaration des dépendances et du point d'entrée

Le fichier `pyproject.toml` contient notamment les déclarations suivantes :

```toml
dependencies = [
    "numpy>=2.4",
    "pandas>=3.0",
    "scikit-learn>=1.8",
    "joblib>=1.5",
    "httpx>=0.28",
]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

**Pourquoi `pytest` et `fastapi` ne figurent-ils pas dans `dependencies` ?**

`pytest` est une bibliothèque destinée à l'exécution des tests automatisés. Elle intervient principalement pendant le développement et la validation du projet. Elle n'est donc pas indispensable à l'utilisation normale du package.

De son côté, `fastapi` est utilisé pour mettre en place le service API, mais il n'est pas nécessaire à l'exécution de la fonctionnalité principale de prédiction accessible depuis la commande `maintai-predict`.

Ces deux bibliothèques peuvent ainsi être considérées comme des dépendances spécifiques au développement ou à certains composants du projet, plutôt que comme des dépendances obligatoires du package principal.

### Vérification de l'installation

Après l'installation éditable, la commande `pip show maintai` a retourné les informations suivantes :

```text
Name: maintai
Version: 0.2.0
Summary: Prédiction de pannes à partir de relevés de capteurs
Home-page:
```

Ces informations confirment que le package `maintai`, en version `0.2.0`, est bien installé dans l'environnement Python.

### Validation des tests à la fin du sprint 1

Après les modifications apportées à la configuration du projet, l'exécution de `python -m pytest` a donné le résultat suivant :

```text
================= 27 passed, 1 warning in 6.63s =================
```

Les 27 tests ont donc été validés avec succès.

### Utilisation du package depuis un autre répertoire

Pour vérifier que le package était correctement installé, je me suis placée dans un autre répertoire à l'aide de la commande :

```powershell
cd $env:TEMP
```

J'ai ensuite exécuté :

```powershell
maintai-predict 72 6 85 15000
```

Le résultat obtenu était :

```text
Probabilité de panne : 95 % (ALERTE)
```

La commande suivante a également été utilisée pour identifier l'emplacement du package :

```powershell
python -c "import maintai; print(maintai.__file__)"
```

Elle affiche le chemin du fichier `__init__.py` du package.

Grâce à l'installation éditable (`pip install -e .`), Python retrouve directement les fichiers du package dans le répertoire source du projet, même lorsque la commande est exécutée depuis un autre dossier.

### Vérification de la prise en compte des modifications

Après avoir modifié le message affiché dans `maintai/cli.py`, j'ai relancé la commande `maintai-predict` sans procéder à une nouvelle installation.

Le changement est immédiatement visible, car l'installation éditable maintient un lien entre le package installé et son emplacement dans le dossier source.

Ainsi, les modifications apportées au code sont directement prises en compte lors de la prochaine exécution de la commande.

## 3. Sprint 2 : Construction et installation du fichier Wheel

### Génération des distributions

La commande suivante a permis de construire les distributions du package :

```powershell
python -m build
```

Après cette opération, le dossier `dist/` contenait les deux fichiers suivants :

```text
maintai-0.2.0.tar.gz
maintai-0.2.0-py3-none-any.whl
```

Le projet dispose donc de deux formats de distribution : une archive source (`.tar.gz`) et un fichier Wheel (`.whl`).

### Vérification du contenu du Wheel

Pour examiner le contenu du fichier Wheel, la commande suivante a été utilisée :

```powershell
tar -tf dist\maintai-0.2.0-py3-none-any.whl
```

Le résultat obtenu était :

```text
maintai/
maintai-0.2.0.dist-info/
```

Le fichier Wheel contient le package Python `maintai` ainsi que les métadonnées nécessaires à son installation.

En revanche, le modèle entraîné, les fichiers de tests et le dossier `ui/` ne sont pas inclus dans cette distribution actuelle, car ils ne font pas partie des éléments déclarés pour être intégrés au package.

Le modèle doit donc être fourni séparément. Son emplacement est ensuite indiqué à l'application à travers la variable d'environnement `MAINTAI_MODELS_DIR`.

### Installation dans un nouvel environnement virtuel

Afin de vérifier que le package pouvait fonctionner indépendamment de son dossier source, une installation a été réalisée dans un environnement virtuel neuf situé dans `%TEMP%\essai`.

Les différents essais ont donné les résultats suivants :

| Situation testée | Résultat obtenu |
|---|---|
| Sans `MAINTAI_MODELS_DIR` | Message indiquant que le modèle est introuvable dans `site-packages\models\model.joblib` |
| Avec `MAINTAI_MODELS_DIR` configuré vers le dossier `models` | `Probabilité de panne : 95 % (ALERTE)` |
| Après installation de `scikit-learn==1.8.0` | `Probabilité de panne : 95 % (ALERTE)` |

Ces essais montrent que le package peut être installé dans un environnement indépendant du projet source, à condition de lui fournir le chemin d'accès au modèle entraîné.

### Origine de l'avertissement `InconsistentVersionWarning`

L'avertissement `InconsistentVersionWarning` apparaît lorsqu'un modèle Scikit-learn sauvegardé avec une version donnée de la bibliothèque est chargé avec une autre version.

Dans notre cas, le fichier `models/model_info.json` contient l'information suivante :

```json
"sklearn_version": "1.8.0"
```

Cette indication permet d'identifier la version de Scikit-learn utilisée lors de l'entraînement du modèle.

L'installation de la version correspondante dans le nouvel environnement a été effectuée avec :

```powershell
pip install scikit-learn==1.8.0
```

Cette opération permet d'assurer la compatibilité entre l'environnement d'exécution et la version utilisée pour entraîner et sauvegarder le modèle.

## 4. Questions de compréhension

### 1. Quelle différence existe-t-il entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?

Le fichier `requirements.txt` sert à définir les bibliothèques à installer pour préparer un environnement de travail. Il peut regrouper les dépendances nécessaires à l'exécution, aux tests et aux différentes opérations de développement.

En revanche, la section `dependencies` de `pyproject.toml` déclare les bibliothèques indispensables au fonctionnement du package lorsqu'il est installé.

Ces dépendances sont automatiquement prises en compte par `pip` lors de l'installation du package, ce qui facilite sa distribution et son utilisation dans d'autres environnements.

### 2. Quelle différence existe-t-il entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?

La commande `pip install -e .` réalise une installation éditable du projet. Le package reste lié à son répertoire source, ce qui permet de prendre en compte les modifications du code sans devoir procéder à une nouvelle installation.

À l'inverse, la commande :

```powershell
pip install dist\maintai-0.2.0-py3-none-any.whl
```

installe le package à partir du fichier Wheel généré lors de la phase de construction.

Il s'agit d'une installation classique qui utilise les fichiers contenus dans la distribution, indépendamment du dossier source original.

La principale différence concerne donc le lien avec le code source : il est conservé lors d'une installation éditable, contrairement à une installation à partir d'un Wheel.

### 3. Qu'est-ce qu'un point d'entrée (`[project.scripts]`) ? Où `pip` crée-t-il le fichier `maintai-predict.exe` ?

Un point d'entrée permet de définir une commande exécutable depuis le terminal et de l'associer à une fonction Python précise du package.

Dans notre projet, la déclaration :

```toml
[project.scripts]
maintai-predict = "maintai.cli:main"
```

indique que l'exécution de la commande `maintai-predict` déclenche la fonction `main()` du module `maintai.cli`.

Sous Windows, lors de l'installation du package, `pip` crée le lanceur `maintai-predict.exe` dans le répertoire `Scripts` de l'environnement Python actif.

Par exemple, pour un environnement virtuel local, son emplacement est :

```text
.venv\Scripts\maintai-predict.exe
```

Ce mécanisme permet d'utiliser les fonctionnalités du package directement depuis la ligne de commande, sans avoir à exécuter manuellement un fichier Python.

## 5. Rendu et gestion du dépôt Git

**Lien du dépôt GitHub – dossier TP4 :**

https://github.com/ayoubbelouanas/Comptage-de-v-hicules-avec-YOLO-pr-entrain-/tree/main/TPs/TP4

**Pull Request :**

Aucune Pull Request n'a été ouverte à ce stade. Le travail est prévu pour être intégré directement dans la branche `main`.



**Vérification de l'état du dépôt :**

L'état de `git status` avant le commit reste également à vérifier, notamment pour contrôler la présence éventuelle des répertoires générés pendant la construction du package :

- `dist/`
- `build/`
- `maintai.egg-info/`

Ces éléments doivent être gérés conformément aux règles du `.gitignore`, afin d'éviter d'ajouter au dépôt des fichiers générés automatiquement qui ne sont pas nécessaires au suivi du code source.

## 6. Points restant à approfondir

Les principales difficultés rencontrées pendant ce TP concernent la distinction entre une installation éditable et une installation classique à partir d'un fichier Wheel.

La gestion du modèle entraîné dans un environnement différent du répertoire source constitue également un point important. Il est nécessaire de prévoir une configuration adaptée des chemins d'accès aux ressources, notamment à travers `MAINTAI_MODELS_DIR`.

Ce travail a aussi permis de mieux comprendre l'importance de la compatibilité des versions des bibliothèques Python, en particulier Scikit-learn, lors de la sauvegarde et du rechargement d'un modèle.

Enfin, la distinction entre les dépendances indispensables au fonctionnement du package et celles utilisées uniquement pour les tests et le développement représente une notion essentielle pour assurer une distribution propre et maîtrisée.

## Conclusion

Ce TP4 m'a permis de comprendre les différentes étapes nécessaires pour transformer un projet Python classique en un package installable et réutilisable.

La mise en place de `pyproject.toml`, l'installation éditable, la création d'un point d'entrée en ligne de commande et la génération d'un fichier Wheel ont permis de faire évoluer l'organisation de MaintAI vers une structure plus standardisée.

Les différents essais réalisés ont également mis en évidence l'importance de la gestion des ressources externes et de la compatibilité des dépendances, notamment lors de l'installation du package dans un nouvel environnement virtuel.

Enfin, ce TP m'a permis de mieux comprendre les mécanismes de distribution des packages Python et leur intérêt pour faciliter le déploiement, la réutilisation et la maintenance d'une application.