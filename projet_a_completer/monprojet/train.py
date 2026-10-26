
"""Entraîne, évalue et compare les modèles candidats.

Usage, depuis la racine du projet :
    python -m monprojet.train
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from monprojet import config
from monprojet.data import load_data, split
from monprojet.models import candidates


HIGHER_IS_BETTER = {
    "accuracy": True,
    "recall": True,
    "precision": True,
    "f1": True,
    "mae": False,
    "rmse": False,
    "r2": True,
}


def build_preprocessing(X: pd.DataFrame) -> ColumnTransformer:
    """Prépare les colonnes numériques, catégorielles et textuelles."""

    text = [config.TEXT_COLUMN] if config.TEXT_COLUMN else []

    numeric = [
        c for c in X.columns
        if c not in text and pd.api.types.is_numeric_dtype(X[c])
    ]

    categorical = [
        c for c in X.columns
        if c not in text and c not in numeric
    ]

    steps = []

    if numeric:
        steps.append(
            (
                "nombres",
                make_pipeline(
                    SimpleImputer(strategy="median"),
                    StandardScaler(),
                ),
                numeric,
            )
        )

    if categorical:
        steps.append(
            (
                "categories",
                make_pipeline(
                    SimpleImputer(strategy="most_frequent"),
                    OneHotEncoder(handle_unknown="ignore"),
                ),
                categorical,
            )
        )

    if text:
        steps.append(
            (
                "texte",
                TfidfVectorizer(),
                config.TEXT_COLUMN,
            )
        )

    return ColumnTransformer(steps, sparse_threshold=0)


def evaluate(model, X_test, y_test) -> dict:
    """Évalue le modèle et renvoie les métriques arrondies à 3 décimales."""

    y_pred = model.predict(X_test)

    if config.TASK == "classification":
        average = "binary" if pd.Series(y_test).nunique() == 2 else "macro"

        scores = {
            "accuracy": accuracy_score(y_test, y_pred),
            "recall": recall_score(
                y_test,
                y_pred,
                average=average,
                zero_division=0,
            ),
            "precision": precision_score(
                y_test,
                y_pred,
                average=average,
                zero_division=0,
            ),
            "f1": f1_score(
                y_test,
                y_pred,
                average=average,
                zero_division=0,
            ),
        }

    elif config.TASK == "regression":
        scores = {
            "mae": mean_absolute_error(y_test, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "r2": r2_score(y_test, y_pred),
        }

    else:
        raise ValueError(
            f"Tâche inconnue : '{config.TASK}'. "
            "Valeurs acceptées : 'classification' ou 'regression'."
        )

    return {
        name: round(float(value), 3)
        for name, value in scores.items()
    }


def main() -> None:
    """Entraîne, compare et sauvegarde le meilleur modèle."""

    # 1. Charger et découper les données.
    df = load_data()
    X_train, X_test, y_train, y_test = split(df)

    # Vérifier que la métrique principale est valide.
    if config.MAIN_METRIC not in HIGHER_IS_BETTER:
        raise ValueError(
            f"Métrique inconnue : '{config.MAIN_METRIC}'."
        )

    expected_metrics = (
        {"accuracy", "recall", "precision", "f1"}
        if config.TASK == "classification"
        else {"mae", "rmse", "r2"}
        if config.TASK == "regression"
        else set()
    )

    if config.MAIN_METRIC not in expected_metrics:
        raise ValueError(
            f"La métrique '{config.MAIN_METRIC}' ne correspond pas "
            f"à la tâche '{config.TASK}'."
        )

    # 2. Entraîner et évaluer chaque candidat.
    resultats = {}
    modeles_entraines = {}

    for nom, estimateur in candidates().items():
        modele = Pipeline(
            [
                ("preparation", build_preprocessing(X_train)),
                ("modele", estimateur),
            ]
        )

        modele.fit(X_train, y_train)
        scores = evaluate(modele, X_test, y_test)

        resultats[nom] = scores
        modeles_entraines[nom] = modele

    if not resultats:
        raise ValueError("Aucun modèle candidat n'a été fourni.")

    # 3. Afficher le tableau comparatif.
    tableau = pd.DataFrame(resultats).T

    metric = config.MAIN_METRIC
    ascending = not HIGHER_IS_BETTER[metric]

    tableau = tableau.sort_values(
        by=metric,
        ascending=ascending,
    )

    print("\n=== Comparaison des modèles ===")
    print(tableau.to_string())

    # 4. Identifier le meilleur modèle.
    meilleur_nom = tableau.index[0]
    meilleur_modele = modeles_entraines[meilleur_nom]

    print(f"\nMétrique principale : {metric}")
    print(f"Meilleur modèle : {meilleur_nom}")
    print(f"Score : {resultats[meilleur_nom][metric]}")

    # 5. Créer le dossier et sauvegarder les résultats.
    dossier = Path(config.MODELS_DIR)
    dossier.mkdir(parents=True, exist_ok=True)

    joblib.dump(meilleur_modele, dossier / "model.joblib")

    rapport = {
        "main_metric": metric,
        "best": meilleur_nom,
        "results": resultats,
    }

    with open(
        dossier / "metrics.json",
        "w",
        encoding="utf-8",
    ) as fichier:
        json.dump(
            rapport,
            fichier,
            indent=4,
            ensure_ascii=False,
        )

    print(f"\nModèle sauvegardé : {dossier / 'model.joblib'}")
    print(f"Métriques sauvegardées : {dossier / 'metrics.json'}")


if __name__ == "__main__":
    main()
