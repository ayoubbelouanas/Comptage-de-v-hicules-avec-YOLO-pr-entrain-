
import pandas as pd
from sklearn.model_selection import train_test_split

from monprojet import config


def load_data(path=None) -> pd.DataFrame:
    """Lit le CSV, vérifie la cible et supprime les cibles manquantes."""
    csv_path = config.DATA_PATH if path is None else path
    df = pd.read_csv(csv_path)

    if config.TARGET not in df.columns:
        raise ValueError(
            f"La colonne cible '{config.TARGET}' est absente du fichier CSV."
        )

    df = df.dropna(subset=[config.TARGET]).copy()
    return df


def feature_columns(df: pd.DataFrame) -> list:
    """Retourne les colonnes utilisées comme variables d'entrée."""
    if config.FEATURES is not None:
        return list(config.FEATURES)

    excluded = {config.TARGET, config.TIME_COLUMN}
    return [c for c in df.columns if c not in excluded]


def split(df: pd.DataFrame):
    """Sépare les données en ensembles d'entraînement et de test."""
    features = feature_columns(df)
    X = df[features]
    y = df[config.TARGET]

    if config.SPLIT == "random":
        # Stratification pour une classification, si possible.
        stratify = None

        if y.nunique() > 1 and y.value_counts().min() >= 2:
            stratify = y

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=config.TEST_SIZE,
            random_state=config.SEED,
            stratify=stratify,
        )

    elif config.SPLIT == "chronologique":
        if config.TIME_COLUMN not in df.columns:
            raise ValueError(
                f"La colonne temporelle '{config.TIME_COLUMN}' est absente."
            )

        dates = pd.to_datetime(df[config.TIME_COLUMN], errors="raise")
        indices = dates.sort_values(kind="stable").index

        X_sorted = X.loc[indices]
        y_sorted = y.loc[indices]

        n_test = int(len(df) * config.TEST_SIZE)
        if n_test == 0 or n_test >= len(df):
            raise ValueError(
                "TEST_SIZE doit permettre d'avoir des données "
                "dans les ensembles d'entraînement et de test."
            )

        X_train = X_sorted.iloc[:-n_test]
        X_test = X_sorted.iloc[-n_test:]
        y_train = y_sorted.iloc[:-n_test]
        y_test = y_sorted.iloc[-n_test:]

    else:
        raise ValueError(
            f"Mode de découpage inconnu : '{config.SPLIT}'. "
            "Valeurs acceptées : 'random' ou 'chronologique'."
        )

    return X_train, X_test, y_train, y_test
