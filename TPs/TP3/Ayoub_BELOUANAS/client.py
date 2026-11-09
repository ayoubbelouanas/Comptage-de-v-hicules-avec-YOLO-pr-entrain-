"""Client Python de l'API MaintAI : ce que fetch faisait dans la page web (TP2), en Python.

Usage :
    from maintai.client import MaintaiClient
    api = MaintaiClient("http://localhost:8000", api_key="demo123")
    api.predict({"temperature_c": 72, "vibration_mm_s": 6, "load_pct": 85, "runtime_hours": 15000})
"""
import httpx


class APIError(Exception):
    """L'API a répondu, mais pas 200 : on garde le code et le message."""

    def __init__(self, status_code: int, detail):
        super().__init__(f"Erreur {status_code} : {detail}")
        self.status_code = status_code
        self.detail = detail


class MaintaiClient:
    def __init__(self, url: str = "http://localhost:8000", api_key: str | None = None,
                 http: httpx.Client | None = None):
        # Les tests passent leur TestClient dans http : même code, sans serveur
        self.http = http or httpx.Client(base_url=url, timeout=5.0)
        self.api_key = api_key

    def health(self) -> dict:
        r = self.http.get("/health")
        r.raise_for_status()
        return r.json()

    def predict(self, reading: dict) -> dict:
        """Envoie un relevé à l’API et renvoie sa prédiction.

        Args:
            reading: Dictionnaire contenant les valeurs des capteurs.

        Returns:
            La réponse JSON de l’API en cas de succès.

        Raises:
            APIError: Si l’API répond avec un code différent de 200.
            httpx.HTTPError: Si la requête ne peut pas atteindre l’API.
        """
        # TODO TP3 sprint 2 :
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        response = self.http.post(
            "/v1/predict",
            json=reading,
            headers=headers,
        )

        if response.status_code != 200:
            # Lit le détail JSON quand l’API en fournit un.
            try:
                contenu = response.json()
                detail = (
                    contenu.get("detail", contenu)
                    if isinstance(contenu, dict)
                    else contenu
                )
            # Certains serveurs renvoient du texte ou un corps vide en cas d’erreur.
            except ValueError:
                detail = response.text.strip() or "Réponse vide ou non JSON"

            raise APIError(response.status_code, detail)

        return response.json()
