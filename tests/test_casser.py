"""Cas de requêtes invalides pour l'API de prédiction."""

import pytest


VALID = {
    "temperature_c": 60.0,
    "vibration_mm_s": 2.0,
    "load_pct": 50.0,
    "runtime_hours": 5000,
}
HEADERS = {}


@pytest.mark.parametrize(
    ("url", "body", "expected_status"),
    [
        pytest.param(
            "/v1/predict",
            {key: value for key, value in VALID.items() if key != "runtime_hours"},
            422,
            id="champ-manquant",
        ),
        pytest.param(
            "/v1/predict",
            {**VALID, "temperature_c": 999},
            422,
            id="valeur-absurde",
        ),
        pytest.param(
            "/v1/predict",
            {**VALID, "temperature_c": "chaud"},
            422,
            id="texte-au-lieu-d-un-nombre",
        ),
        pytest.param(
            "/v1/predict",
            {**VALID, "couleur": "rouge"},
            422,
            id="champ-en-trop",
        ),
        pytest.param(
            "/v1/prediction",
            VALID,
            404,
            id="mauvaise-route",
        ),
    ],
)
def test_invalid_requests_are_rejected(client, url, body, expected_status):
    r = client.post(url, json=body, headers=HEADERS)

    assert r.status_code == expected_status
