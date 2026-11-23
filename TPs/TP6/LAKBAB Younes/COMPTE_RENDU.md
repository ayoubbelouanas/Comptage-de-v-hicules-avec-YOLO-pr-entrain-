# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

Date : 23/11/2026 · 11:50 · Auteurs : LAKBAB YOUNES

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
Hello from Docker!

Client:
 Version:           29.2.1
 API version:       1.53
 Go version:        go1.25.6
 Git commit:        a5c7197
 Built:             Mon Feb  2 17:20:16 2026
 OS/Arch:           windows/amd64
 Context:           desktop-linux

Server: Docker Desktop 4.63.0 (220185)
 Engine:
  Version:          29.2.1
  API version:      1.53 (minimum version 1.44)
  Go version:       go1.25.6
  Git commit:       6bc6209
  Built:            Mon Feb  2 17:17:24 2026
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          v2.2.1
  GitCommit:        dea7da592f5d1d2b7755e3a161be07f43fad8f75
 runc:
  Version:          1.3.4
  GitCommit:        v1.3.4-0-gd6d73eb8
 docker-init:
  Version:          0.19.0
  GitCommit:        de40ad0

```

Dernière ligne de `python -m pytest` après la mise en place :

```
5 failed, 33 passed, 4 warnings in 54.04s
```

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?

   Une image Docker est un modèle contenant le code de l'application, ses bibliothèques et son environnement d'exécution. Un conteneur est une instance de cette image en cours d'exécution, dans un environnement isolé.

2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   Cette organisation permet d'optimiser le cache Docker. Les dépendances sont installées avant la copie du code source. Ainsi, lorsqu'on modifie uniquement le code, Docker réutilise la couche contenant les bibliothèques déjà installées, ce qui accélère la construction de l'image.

3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?

   La version exacte de scikit-learn est fixée pour garantir la compatibilité avec le modèle entraîné et sauvegardé. L'utilisation de >=1.5 pourrait installer une version différente et provoquer des problèmes de compatibilité ou de reproductibilité.

4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   
   Ces bibliothèques sont principalement utilisées pendant le développement. MLflow permet de suivre les expériences, DVC sert au versionnement des données et pytest permet d'exécuter les tests. Elles ne sont pas nécessaires pour utiliser le modèle déjà entraîné dans l'API. Leur exclusion réduit la taille de l'image et le nombre de dépendances.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile

# Image de MaintAI : code et bibliothèques

# 1. Image Python
FROM python:3.11-slim

# 2. Répertoire de travail
WORKDIR /app

# 3. Installer les dépendances
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# 4. Copier le code
COPY maintai/ ./maintai/
COPY ui/ ./ui/

# 5. Variables d'environnement
ENV MAINTAI_MODELS_DIR=/app/models
ENV MAINTAI_DATA_PATH=/app/data/sensors.csv

# 6. Exposer le port et démarrer l'API
EXPOSE 8000

CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build | 193s | 1.13GB |
| après une modification de `maintai/predict.py` |1.54s |1.13GB |

Que signifie `CACHED` dans le journal du second build ?

Le terme `CACHED` indique que Docker réutilise une couche construite précédemment, car les fichiers et les instructions associés n'ont pas changé. Cela évite notamment de réinstaller toutes les bibliothèques Python après une simple modification du code source. Le second build est donc généralement plus rapide.

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```
$modelsPath = (Resolve-Path .\models).Path
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "${modelsPath}:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | { "status": "ok",  
                  "model_loaded": true}|
| `POST /v1/predict` sans clé |{
  "detail": "Clé API absente ou invalide"
} |
| `POST /v1/predict` avec la clé | {
  "failure_probability": 0.9553,
  "alert": true,
  "threshold": 0.3,
  "model_version": "2026-11-23T10:51:07Z"
}|

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

Sans l'option `-v`, l'API démarre normalement, mais le modèle n'est pas chargé. L'endpoint `/health` retourne `model_loaded: false`, tandis que `/v1/predict` retourne une erreur HTTP 503.

Cela s'explique par le fait que le modèle est exclu de l'image Docker et doit être fourni au conteneur à travers un volume. Sans ce volume, l'application ne peut pas effectuer de prédiction.


**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

Lorsque l'API est démarrée avec `--host 127.0.0.1`, les journaux Docker indiquent que le serveur Uvicorn écoute sur `127.0.0.1:8000`.

Cependant, l'API n'est pas accessible depuis le navigateur à l'adresse `http://localhost:8002/health`.

En effet, `127.0.0.1` limite l'accès au conteneur lui-même. Pour rendre l'application accessible depuis l'extérieur, il faut utiliser `--host 0.0.0.0`.

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml

services:
  api:
    build: .
    image: maintai:0.4.0
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models:ro

  ui:
    image: maintai:0.4.0
    command:
      - python
      - -m
      - streamlit
      - run
      - ui/app.py
      - --server.address=0.0.0.0
      - --server.port=8501
      - --server.headless=true
    environment:
      MAINTAI_API_URL: http://api:8000
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - api

```

Sortie de `docker compose ps` :

```
NAME        IMAGE           COMMAND                  SERVICE   CREATED          STATUS          PORTS
tp6-api-1   maintai:0.4.0   "uvicorn maintai.api…"   api       11 seconds ago   Up 10 seconds   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
tp6-ui-1    maintai:0.4.0   "python -m streamlit…"   ui        11 seconds ago   Up 9 seconds    0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

elle affichait http://localhost:8000 parce que ui/app.py utilise cette valeur fixe et ne lis pas encore MAINTAI_API_URL.

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
docker compose exec ui python -c "import httpx; print(httpx.get('http://api:8000/health').text)"
{"status":"ok","model_loaded":true}

(.venv) (base) sm@MacBookPro TP6 % docker compose exec ui python -c "import httpx; print(httpx.get('http://localhost:8000/health').text)"
Traceback (most recent call last):
  File "/usr/local/lib/python3.11/site-packages/httpx/_transports/default.py", line 101, in map_httpcore_exceptions
    yield
  File "/usr/local/lib/python3.11/site-packages/httpx/_transports/default.py", line 250, in handle_request
    resp = self._pool.handle_request(req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpcore/_sync/connection_pool.py", line 256, in handle_request
    raise exc from None
  File "/usr/local/lib/python3.11/site-packages/httpcore/_sync/connection_pool.py", line 236, in handle_request
    response = connection.handle_request(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpcore/_sync/connection.py", line 101, in handle_request
    raise exc
  File "/usr/local/lib/python3.11/site-packages/httpcore/_sync/connection.py", line 78, in handle_request
    stream = self._connect(request)
             ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpcore/_sync/connection.py", line 124, in _connect
    stream = self._network_backend.connect_tcp(**kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpcore/_backends/sync.py", line 207, in connect_tcp
    with map_exceptions(exc_map):
  File "/usr/local/lib/python3.11/contextlib.py", line 158, in __exit__
    self.gen.throw(typ, value, traceback)
  File "/usr/local/lib/python3.11/site-packages/httpcore/_exceptions.py", line 14, in map_exceptions
    raise to_exc(exc) from exc
httpcore.ConnectError: [Errno 111] Connection refused

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/usr/local/lib/python3.11/site-packages/httpx/_api.py", line 195, in get
    return request(
           ^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_api.py", line 109, in request
    return client.request(
           ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_client.py", line 825, in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_client.py", line 914, in send
    response = self._send_handling_auth(
               ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_client.py", line 942, in _send_handling_auth
    response = self._send_handling_redirects(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_client.py", line 979, in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_client.py", line 1014, in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/httpx/_transports/default.py", line 249, in handle_request
    with map_httpcore_exceptions():
  File "/usr/local/lib/python3.11/contextlib.py", line 158, in __exit__
    self.gen.throw(typ, value, traceback)
  File "/usr/local/lib/python3.11/site-packages/httpx/_transports/default.py", line 118, in map_httpcore_exceptions
    raise mapped_exc(message) from exc
httpx.ConnectError: [Errno 111] Connection refused

```

-> La 2eme echoue car localhost désigne le conteneur ui lui-même. Compose permet à ui de joindre l’API par le nom du service, api.

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
38 passed, 4 warnings in 40.66s
```

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumez ici votre décision en deux phrases :

-> Nous avons choisi de mettre le code et les dépendances dans l’image Docker, puis de fournir le modèle et les données au lancement par des volumes en lecture seule. La clé API est transmise par le fichier .env, sans être intégrée à l’image.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.

   -> Le code et les dépendances entrent dans l’image avec COPY et l’installation des bibliothèques depuis requirements-docker.txt. Au lancement, le modèle et les données sont montés comme volumes, et la clé API est transmise au conteneur par env_file: .env.

2. Pourquoi la clé API n'est-elle jamais dans l'image ?

   -> La clé API est un secret : si elle était incluse dans l’image, toute personne ayant accès à cette image pourrait la récupérer. La transmettre au lancement permet de la garder hors de l’image et de la changer sans reconstruire celle-ci.

3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?

   -> TP4 et TP5 apportent le code, le modèle entraîné et les dépendances nécessaires à son utilisation. Docker ajoute une image contenant l’environnement d’exécution et les dépendances, afin de lancer l’application de façon cohérente sur les machines équipées de Docker.

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp6` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? oui / non

## 9. Ce qui reste flou

…
