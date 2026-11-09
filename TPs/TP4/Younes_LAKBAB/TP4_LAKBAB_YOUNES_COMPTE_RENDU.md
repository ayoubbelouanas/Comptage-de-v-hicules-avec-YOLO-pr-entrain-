# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** …  ·  **Membres :** …  ·  **Date :** …

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP4.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
2 failed, 25 passed, 1 warning in 17.75s
```

Quels sont les deux tests qui échouent, et pourquoi ?

Les deux tests qui doivent échouer sont :

1. `test_installed_version_matches_the_code` :
   le package maintai n'est pas encore installé dans
   l'environnement Python. Sa version ne peut donc pas
   être retrouvée dans les métadonnées des packages installés.

2. `test_command_is_declared` :
   la commande maintai-predict n'est pas encore déclarée
   dans pyproject.toml ni installée dans l'environnement.

Ces erreurs sont normales à cette étape. Elles seront
corrigées pendant le Sprint 1 en complétant pyproject.toml
et en exécutant pip install -e .

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

```toml
# Bibliothèques nécessaires au fonctionnement de MaintAI.
# >= indique la version minimale acceptée.

dependencies = [
    "numpy>=2.0",          # Calcul numérique et génération de données
    "pandas>=2.2",         # Manipulation des données
    "scikit-learn>=1.5",   # Entraînement et prédiction ML
    "joblib>=1.4",         # Sauvegarde et chargement du modèle
    "httpx>=0.27",         # Client HTTP pour communiquer avec l'API
]

# Déclarer une commande accessible depuis le terminal.
[project.scripts]

# Nom de la commande = "module Python:fonction à exécuter"
maintai-predict = "maintai.cli:main"

```

Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?

pytest est utilisé uniquement pour les tests, tandis que fastapi sert à exécuter l'API. Ces bibliothèques ne sont pas nécessaires pour effectuer une prédiction directement avec le package.

Elles sont donc placées dans les dépendances optionnelles : dev pour pytest et api pour FastAPI.

Sortie de `pip show maintai` (les quatre premières lignes) :

```
pip show maintai
Name: maintai
Version: 0.2.0
Summary: TODO : une phrase qui dit ce que fait le package
Home-page: 
Author: 
Author-email: 
License: 
Location: C:\Users\youne\OneDrive\Bureau\maintai-starter-tp4\.venv\Lib\site-packages
Editable project location: C:\Users\youne\OneDrive\Bureau\maintai-starter-tp4
Requires: httpx, joblib, numpy, pandas, scikit-learn
Required-by: 
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
27 passed, 1 warning in 12.20s 
```

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?

La commande maintai-predict fonctionne même lorsque nous sommes dans un dossier différent du projet.

La deuxième commande affiche le chemin du module maintai situé dans le dossier d'origine du TP4.

Cela est possible grâce à l'installation en mode éditable avec pip install -e ., qui permet à Python de retrouver directement les fichiers sources du projet.

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?

Le message modifié doit apparaître immédiatement sans nouvelle installation.

En effet, l'installation éditable ne copie pas définitivement le code du package. Elle conserve un lien vers les fichiers sources. Par conséquent, toute modification du code Python est directement prise en compte lors de la prochaine exécution de la commande.

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```
 Répertoire : C:\Users\youne\OneDrive\Bureau\maintai-starter-tp4\dist


Mode                 LastWriteTime         Length Name                                                                                                                                                    
----                 -------------         ------ ----                                                                                                                                                    
-a----         11/9/2026  12:07 PM          11636 maintai-0.2.0-py3-none-any.whl                                                                                                                          
-a----         11/9/2026  12:07 PM          12442 maintai-0.2.0.tar.gz                                                                                                                                    

```

Contenu du wheel (`tar -tf dist\maintai-0.2.0-py3-none-any.whl`). Le modèle, les tests et `ui/` y sont-ils ? Pourquoi ?

```
maintai/__init__.py
maintai/cli.py
maintai/client.py
maintai/config.py
maintai/data.py
maintai/dataset.py
maintai/predict.py
maintai/train.py
maintai/api/__init__.py
maintai/api/main.py
maintai/api/schemas.py
maintai/api/security.py
maintai-0.2.0.dist-info/METADATA
maintai-0.2.0.dist-info/WHEEL
maintai-0.2.0.dist-info/entry_points.txt
maintai-0.2.0.dist-info/top_level.txt
maintai-0.2.0.dist-info/RECORD
```

Dans un environnement neuf (`%TEMP%\essai`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | Message « Modèle introuvable », car le modèle n'est pas inclus dans le wheel.|
| avec `MAINTAI_MODELS_DIR` vers vos `models` | La prédiction peut fonctionner(Probabilité de panne : 95 % (ALERTE)), mais un avertissement de version peut apparaître si les versions de scikit-learn diffèrent.|
| après `pip install scikit-learn==1.8.0` | La prédiction fonctionne (Probabilité de panne : 95 % (ALERTE)) avec la version attendue par le modèle, sans avertissement d'incompatibilité de version si le modèle a été entraîné avec scikit-learn 1.8.0.|


D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?

L'avertissement InconsistentVersionWarning apparaît lorsqu'un modèle scikit-learn est chargé avec une version différente de celle utilisée lors de son entraînement.

Cette différence peut provoquer des problèmes de compatibilité ou des résultats inattendus.

Le fichier models/model_info.json contient la ligne sklearn_version, qui indique la version utilisée pour entraîner et sauvegarder le modèle.

Il faut donc utiliser une version compatible, idéalement la même version de scikit-learn, pour garantir la reproductibilité des prédictions.

Cette expérience montre qu'une livraison complète nécessite trois éléments : le code Python (wheel), le modèle entraîné et les versions exactes des dépendances.

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?

Le fichier requirements.txt contient les bibliothèques avec des versions exactes (==) afin de garantir un environnement reproductible.

En revanche, dependencies dans pyproject.toml définit les bibliothèques nécessaires au fonctionnement du package, généralement avec des versions minimales (>=).

Ainsi, requirements.txt sert principalement à reproduire l'environnement du projet, tandis que pyproject.toml permet d'installer et de distribuer le package avec ses dépendances.

2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?

La commande pip install -e . installe le package en mode éditable. Python utilise directement les fichiers sources du projet. Les modifications du code sont donc prises en compte sans réinstallation.

En revanche, pip install dist\maintai-0.2.0-py3-none-any.whl installe une copie du package construite dans le wheel. Les modifications ultérieures des fichiers sources ne sont pas automatiquement prises en compte.

Le mode éditable est adapté au développement, tandis que le wheel est utilisé pour la distribution.


3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?

Un point d'entrée permet d'associer une commande du terminal à une fonction Python.

Dans notre projet, la déclaration suivante :

[project.scripts]
maintai-predict = "maintai.cli:main"

permet d'exécuter la fonction main() du module maintai/cli.py en saisissant simplement maintai-predict dans le terminal.

Lors de l'installation, pip crée le fichier maintai-predict.exe dans le dossier Scripts de l'environnement virtuel :

.venv\Scripts\maintai-predict.exe

Cela permet d'utiliser MaintAI directement depuis le terminal sans lancer manuellement un script Python.

## 5. Le rendu Git

- Lien de la pull request : …
- Le tag `tp4` existe sur GitHub : oui / non
- `git status` avant le commit : `dist/`, `build/` ou `maintai.egg-info/` apparaissaient-ils ? oui / non

## 6. Ce qui reste flou

…
