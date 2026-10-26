
from monprojet import config

from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor


def candidates() -> dict:
    """Renvoie les modèles scikit-learn non entraînés à comparer."""

    if config.TASK == "classification":
        return {
            # Baseline : prédit toujours la classe majoritaire.
            "baseline": DummyClassifier(strategy="most_frequent"),

            # Modèles de classification.
            "logistic_regression": LogisticRegression(
                max_iter=1000,
                random_state=config.SEED,
            ),
            "random_forest": RandomForestClassifier(
                n_estimators=100,
                random_state=config.SEED,
            ),
            "hist_gradient_boosting": HistGradientBoostingClassifier(
                random_state=config.SEED,
            ),
            "knn": KNeighborsClassifier(
                n_neighbors=5,
            ),
        }

    elif config.TASK == "regression":
        return {
            # Baseline : prédit la moyenne de la cible.
            "baseline": DummyRegressor(strategy="mean"),

            # Modèles de régression.
            "ridge": Ridge(),
            "random_forest": RandomForestRegressor(
                n_estimators=100,
                random_state=config.SEED,
            ),
            "hist_gradient_boosting": HistGradientBoostingRegressor(
                random_state=config.SEED,
            ),
            "knn": KNeighborsRegressor(
                n_neighbors=5,
            ),
        }

    else:
        raise ValueError(
            f"Tâche inconnue : '{config.TASK}'. "
            "Valeurs acceptées : 'classification' ou 'regression'."
        )
