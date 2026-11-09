# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** …  ·  **Membres :** Ayoub BELOUANAS ·  **Date :** 09/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP4.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
2 failed, 25 passed, 1 warning in 6.96s
```

Quels sont les deux tests qui échouent, et pourquoi ?

Les deux tests qui échouent sont `test_installed_version_matches_the_code` et `test_command_is_declared`, dans `tests/test_package.py`. Le premier échoue parce que `maintai` n’est pas encore installé et que ses métadonnées de version sont donc absentes. Le second échoue parce que la commande `maintai-predict` n’est pas encore déclarée comme point d’entrée du package.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

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

Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?

`pytest` sert aux tests et `fastapi` sert à lancer l’API ; ils ne sont pas nécessaires au cœur du package. Ils sont donc dans des groupes optionnels, tandis que `dependencies` contient les bibliothèques nécessaires au package.

Sortie de `pip show maintai` (les quatre premières lignes) :

```
maintai-predict 72 6 85 15000
Name: maintai
Version: 0.2.0
Summary: Prédiction de panne à partir de relevés de capteurs
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
27 passed, 1 warning in 7.61s 
```

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?

maintai-predict 72 6 85 15000 : Probabilité de panne : 95 % (ALERTE)

python -c "import maintai; print(maintai.__file__)" : /Users/sm/Desktop/Emsi_5/Dev App AI/TP4/maintai-starter-tp4/maintai/__init__.py

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?

Oui, le changement est visible sans réinstallation. `pip install -e .` installe le package en mode éditable : la commande utilise le code source du projet, donc elle voit les modifications enregistrées.

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```
maintai-0.2.0-py3-none-any.whl  maintai-0.2.0.tar.gz
```

Contenu du wheel (`tar -tf dist\maintai-0.2.0-py3-none-any.whl`). Le modèle, les tests et `ui/` y sont-ils ? Pourquoi ?

```
Archive:  dist/maintai-0.2.0-py3-none-any.whl
  Length      Date    Time    Name
---------  ---------- -----   ----
       95  11-02-2026 16:56   maintai/__init__.py
     1338  11-02-2026 16:56   maintai/cli.py
     1498  11-02-2026 16:50   maintai/client.py
     1505  10-20-2026 12:54   maintai/config.py
      787  10-20-2026 12:54   maintai/data.py
     1327  10-20-2026 12:54   maintai/dataset.py
     1188  10-20-2026 12:54   maintai/predict.py
     3058  10-20-2026 12:54   maintai/train.py
        0  10-20-2026 12:54   maintai/api/__init__.py
     1915  10-20-2026 12:54   maintai/api/main.py
     1186  10-20-2026 12:54   maintai/api/schemas.py
      747  10-20-2026 12:54   maintai/api/security.py
     3423  11-09-2026 11:07   maintai-0.2.0.dist-info/METADATA
       91  11-09-2026 11:07   maintai-0.2.0.dist-info/WHEEL
       53  11-09-2026 11:07   maintai-0.2.0.dist-info/entry_points.txt
        8  11-09-2026 11:07   maintai-0.2.0.dist-info/top_level.txt
     1290  11-09-2026 11:07   maintai-0.2.0.dist-info/RECORD
---------                     -------
    19509                     17 files

Le wheel contient le code Python du package `maintai` et ses métadonnées. Le modèle, les tests et le dossier `ui/` n’y sont pas, car la configuration du package n’inclut que `maintai*`.
```

Dans un environnement neuf (`%TEMP%\essai`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | Modèle introuvable : /private/tmp/essai/.venv/lib/python3.13/site-packages/models/model.joblib Entraînez-le (python -m maintai.train) ou indiquez son dossier dans MAINTAI_MODELS_DIR.|
| avec `MAINTAI_MODELS_DIR` vers vos `models` | Probabilité de panne : 95 % (ALERTE) |
| après `pip install scikit-learn==1.8.0` | Probabilité de panne : 95 % (ALERTE) |

D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?

L’avertissement apparaît lorsqu’on charge un modèle entraîné avec une version de scikit-learn différente de celle installée dans l’environnement. Ici, le modèle a été entraîné avec scikit-learn 1.8.0, tandis que le nouvel environnement avait scikit-learn 1.9.1. L’installation de la version 1.8.0 supprime ce décalage.

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?
   `requirements.txt` fixe des versions précises avec `==` pour recréer le même environnement de travail. Dans `pyproject.toml`, `dependencies` déclare les bibliothèques nécessaires au package et leurs versions minimales avec `>=`. Les dépendances optionnelles, comme FastAPI ou pytest, sont indiquées séparément.

2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?
   `pip install -e .` installe le projet en mode éditable : la commande utilise le code source du dossier du projet, donc les modifications sont visibles sans réinstallation. Installer le wheel installe une version construite du package ; pour intégrer une modification du code source, il faut reconstruire puis réinstaller le wheel.

3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?
   Un point d’entrée associe une commande terminal à une fonction Python. Ici, `maintai-predict` appelle `maintai.cli:main`. Pip crée le lanceur dans l’environnement actif : sous Windows dans `.venv\Scripts\maintai-predict.exe`, et sur macOS/Linux dans `.venv/bin/maintai-predict`.

## 5. Le rendu Git

- Lien de la pull request : …
- Le tag `tp4` existe sur GitHub : oui / non
- `git status` avant le commit : `dist/`, `build/` ou `maintai.egg-info/` apparaissaient-ils ? oui / non

## 6. Ce qui reste flou

…
