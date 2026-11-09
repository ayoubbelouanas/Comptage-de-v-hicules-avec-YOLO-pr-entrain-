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
        """
        Envoyer un relevé de capteurs à l'API MaintAI.

        reading : dictionnaire contenant les valeurs des capteurs.
        Retour : réponse JSON avec la probabilité de panne.

        Une APIError est levée si l'API refuse la requête.
        """

        # 1. Préparer les en-têtes HTTP.
        # On ajoute la clé API uniquement si elle est renseignée.
        headers = {}

        if self.api_key:
            headers["X-API-Key"] = self.api_key

        # 2. Envoyer les valeurs des capteurs à l'API.
        # self.http permet aussi d'utiliser un client simulé
        # dans les tests sans démarrer de serveur.
        response = self.http.post(
            "/v1/predict",
            json=reading,
            headers=headers
        )

        # 3. Vérifier si le serveur a accepté la requête.
        if response.status_code != 200:

            # Récupérer le message d'erreur renvoyé par l'API.
            detail = response.json().get("detail")

            # Lever une exception avec le code et le détail.
            raise APIError(response.status_code, detail)

        # 4. Si la requête réussit, retourner la réponse JSON.
        return response.json()

   
