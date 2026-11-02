"""Authentification par clé API, transmise dans l'en-tête X-API-Key."""
import secrets

from fastapi import Header, HTTPException, status

from maintai.config import get_settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    """Vérifie la clé X-API-Key envoyée par le client.
    Raises:
        HTTPException 500 : aucune clé API n'est configurée sur le serveur.
        HTTPException 401 : la clé du client est absente ou incorrecte.
    """
    api_key_attendue = get_settings().api_key

    if api_key_attendue is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé API non configurée",
        )

    if x_api_key is None or not secrets.compare_digest(
        x_api_key, api_key_attendue
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
