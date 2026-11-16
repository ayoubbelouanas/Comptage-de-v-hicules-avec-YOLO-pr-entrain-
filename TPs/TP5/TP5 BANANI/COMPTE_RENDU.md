# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** G2 ·  **Membres :** Oussama Banani ·  **Date :** 16/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP5.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
32 passed, 2 warnings in 82.85s (0:01:22)
```

Quels tests échouent, et pourquoi ?

Au départ, le point bloquant était `maintai/tracking.py` : la fonction `log_run` était vide (`return ""`), donc aucun test de MLflow ne pouvait enregistrer de run. `tests/test_tracking.py` échouait parce que `mlflow.search_runs()` ne trouvait rien. Un second problème venait de la compatibilité de dépendances sur Python 3.13 : `mlflow` utilisait une version de SQLAlchemy/Alembic trop récente pour l’environnement, ce qui a été corrigé par `SQLAlchemy<2` et `alembic<1.14`.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Avant l'installation editable, Python importait le code du dépôt local parce que le dossier du projet était dans le `PYTHONPATH` courant. Après `pip install -e .`, le package `maintai` pointait vers la version installée en mode editable dans l'environnement virtuel, reliée directement au code du dépôt. Cela permettait aussi d’utiliser la commande `maintai-predict` déclarée dans `pyproject.toml`.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

```python
"""Suivi des entraînements avec MLflow : chaque entraînement devient un « run » qu'on peut comparer.

Les runs sont enregistrés dans mlflow.db (dossier courant) ; on les regarde avec : mlflow ui
"""
import hashlib
import os
from pathlib import Path

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

import mlflow
import mlflow.sklearn

EXPERIMENT = "maintai"
TRUSTED_TYPES = ["sklearn.tree._tree.Tree"]


def file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES,
        )
        return run.info.run_id
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
5 passed, 2 warnings in 183.39s (0:03:03)
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.741 | 0.650 | 0.916 |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train` sur v1 | 0.750 | 0.622 | 0.904 |

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

Pour le modèle opérationnel sur la version courante, le run le plus pertinent est le run par défaut `python -m maintai.train` : il atteint un bon compromis avec `recall = 0.741`, `precision = 0.650` et `accuracy = 0.916`. Si l’on privilégie strictement le rappel pour réduire les pannes manquées, le run `python -m maintai.train --threshold 0.2` reste meilleur sur la version v1 avec `recall = 0.838`, mais il sacrifie la précision. En pratique, pour la version finale utilisée dans le projet, le choix se fait selon le compromis souhaité entre sensibilité et précision.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

La version indiquée est `scikit-learn==1.8.0`. Cela règle le problème du TP4 concernant les dépendances du package et la reproductibilité du modèle : le modèle est bien packagé avec sa version exacte de scikit-learn, ce qui évite les incompatibilités ou les comportements différents si l’environnement de production ne correspond pas exactement à celui de l’entraînement.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

MLflow enregistre les runs dans le dossier local du projet : `mlruns/` pour les artefacts et `mlflow.db` pour la base SQLite de métadonnées. Ces fichiers ne sont pas destinés à être versionnés dans Git, car ils sont produits par l’expérimentation et sont volumineux / non reproductibles selon l’environnement. C’est aussi pour cela que `.gitignore` contient `mlflow.db`.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` (version actuelle du jeu de données utilisé pour l’entraînement final) :

```yaml
outs:
- md5: 93fdeef2cac1893c4f720c16457eea75
  size: 202834
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

L’empreinte `93fdeef2cac1893c4f720c16457eea75` du fichier `data/sensors.csv.dvc` est identique au paramètre `data_md5` enregistré dans le dernier run MLflow. Cela montre bien que la même version de données est tracée à la fois par DVC et par MLflow. La version précédente v1 utilisait `73e0b7cb3c6f795c70c3ddf970b99c15`, puis la version v2 du dataset a été générée avec la nouvelle graine ; la table de comparaison ci-dessous montre le passage d’une version à l’autre.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

Le fichier CSV est un artefact volumineux et potentiellement volatile ; Git ne le versionne pas directement. DVC le remplace par un petit fichier de métadonnées `.dvc` qui contient l’empreinte MD5 et l’emplacement de stockage. Ainsi, Git ne garde que la définition de version des données, et DVC garde le contenu réel dans son cache/remote.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
data\sensors.csv.dvc:
	changed outs:
		modified:           data\sensors.csv
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | N/A (pas de commit dédié dans ce sous-dossier) | 73e0b7cb | 5000 |
| v2 | N/A (pas de commit dédié dans ce sous-dossier) | 93fdeef2 | 8000 |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

Une restauration de la version v1 ramène le fichier à 5000 lignes. Une restauration de la version v2 le ramène à 8000 lignes. C’est exactement la différence attendue entre les deux jeux de données : la version v2 a plus d’observations et une nouvelle graine de génération.

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

`dvc pull` échoue si le cache DVC et le remote local ne disposent pas des fichiers. Dans notre vérification, on obtient :

```
WARNING: Some of the cache files do not exist neither locally nor on remote. Missing cache files:
md5: 93fdeef2cac1893c4f720c16457eea75
Everything is up to date.
ERROR: failed to pull data from the cloud - Checkout failed for following targets:
data\sensors.csv
Is your cache up to date?
```

Cela confirme qu’un stockage distant/local fiable est indispensable pour restaurer les données : sans cache/remote, DVC ne peut pas reconstruire le fichier.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 | 73e0b7cb | 4000 | 0.750 | 0.622 |
| v2 | 93fdeef2 | 6400 | 0.741 | 0.650 |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

Le modèle v2 n’est pas clairement “meilleur” au sens absolu : son recall est légèrement plus bas, mais sa précision est meilleure. La comparaison est donc délicate car les deux runs n’ont pas été entraînés sur le même jeu de données. Un meilleur `recall` ou une meilleure `precision` peut être simplement le reflet d’un changement de distribution des données. Il faut donc comparer les runs seulement en gardant le `data_md5` constant ou en interprétant les résultats avec prudence.

## 5. Décision : l'ADR 004

Dans `docs/adr/004-choix-du-modele.md` : on retient le modèle logistique avec un seuil de 0.2, car il maximise le rappel et donc réduit le risque de panne manquée. Le run retenu est `003a5cd109a048908c4ade9c4de6707a` et la version de données utilisée est `73e0b7cb3c6f795c70c3ddf970b99c15` (v1).

## 6. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?
   Git versionne le code source et les fichiers de configuration légers. DVC versionne les données lourdes en gardant un fichier `.dvc` avec leur empreinte et un stockage distant/local. MLflow versionne les expériences d’entraînement : paramètres, métriques, artefacts et modèles, avec l’empreinte des données (`data_md5`).
2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?
   Le stockage local est ajouté pour éviter de dépendre d’un remote partagé dans le cadre pédagogique et pour tester DVC en local. Pour que tout le groupe partage les mêmes données, il faut créer un remote partagé (S3, Azure Blob, MinIO, NAS ou dépôt distant) et le configurer pour tous : `dvc remote add --shared ...` puis `dvc push`.
3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
   Il faut livrer : le modèle entraîné (`models/model.joblib`), le contrat d’entrée / métadonnées (`models/model_info.json`) et les métriques d’évaluation (`models/metrics.json`). Ils sont maintenant dans le dossier `models/` du projet, et leur emplacement peut être changé via la variable d’environnement `MAINTAI_MODELS_DIR`.

## 7. Le rendu Git

- Lien de la pull request : N/A / non communiqué dans ce dépôt local
- Le tag `tp5` existe sur GitHub : non (non visible dans ce contexte local)
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? oui

## 8. Ce qui reste flou

Le seul point délicat est la gestion du remote DVC sur un environnement local sans infrastructure partagée : il faut un vrai remote externe pour que plusieurs équipes puissent récupérer exactement les mêmes données. En mode local, DVC ne remplace pas complètement un stockage partagé; il sert surtout à la reproductibilité et à la traçabilité des versions de données.

