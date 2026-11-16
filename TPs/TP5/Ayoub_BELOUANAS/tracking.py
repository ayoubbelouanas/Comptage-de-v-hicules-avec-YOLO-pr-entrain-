"""Suivi des entraînements avec MLflow : chaque entraînement devient un « run » qu'on peut comparer.

Les runs sont enregistrés dans mlflow.db (dossier courant) ; on les regarde avec : mlflow ui
"""
import hashlib
import os
from pathlib import Path

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")  # coupe un message d'information de MLflow

import mlflow
import mlflow.sklearn

EXPERIMENT = "maintai"
TRUSTED_TYPES = ["sklearn.tree._tree.Tree"]  # nécessaire pour --model forest


def file_md5(path: Path) -> str:
    """Empreinte du fichier de données : la même que celle que DVC écrit dans le fichier .dvc."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    # TODO TP5 sprint 1 : enregistrer le run dans MLflow
    # Choisit l’expérience commune à tous les entraînements MaintAI.
    mlflow.set_experiment(EXPERIMENT)

    # Regroupe paramètres, version des données, métriques et modèle dans un run.
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        # Enregistre l’empreinte pour retrouver les données utilisées.
        mlflow.log_param("data_md5", file_md5(data_path))

        mlflow.log_metrics(metrics)

        # Stocke le pipeline complet, avec un exemple d'entrée pour l'interface MLflow.
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES,
        )

        run_id = run.info.run_id
    return run_id
