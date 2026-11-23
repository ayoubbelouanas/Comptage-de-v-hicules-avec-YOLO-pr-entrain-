# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** 8  ·  **Membres :** Ayoub BELOUANAS ·  **Date :** 23/11/2026 · **Heure** : 11:25 

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
Hello from Docker!

Client:
 Version:           29.6.2
 API version:       1.55
 Go version:        go1.26.5
 Git commit:        dfc4efb
 Built:             Thu Jul 16 16:11:17 2026
 OS/Arch:           darwin/amd64
 Context:           desktop-linux

Server: Docker Desktop 4.84.0 (234817)
 Engine:
  Version:          29.6.2
  API version:      1.55 (minimum version 1.40)
  Go version:       go1.26.5
  Git commit:       3d80467
  Built:            Thu Jul 16 16:12:20 2026
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          v2.2.5
  GitCommit:        e53c7c1516c3b2bff98eb76f1f4117477e6f4e66
 runc:
  Version:          1.3.6
  GitCommit:        v1.3.6-0-g491b69ba
 docker-init:
  Version:          0.19.0
  GitCommit:        de40ad0
```

Dernière ligne de `python -m pytest` après la mise en place :

```
5 failed, 33 passed, 4 warnings in 33.56s
```

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   -> Une image est un paquet préparé à partir du Dockerfile, qui contient le code et les dépendances. Un conteneur est une instance de cette image en cours d’exécution.

2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   -> Docker peut mettre en cache l’installation des dépendances. Si le code change mais pas les dépendances, il réutilise cette étape et le build est plus rapide.

3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   -> Le modèle a été entraîné et sauvegardé avec cette version. Utiliser la même version limite les incompatibilités lors du chargement du modèle.

4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   -> MLflow et DVC servent au suivi et à la gestion des données pendant le développement ; pytest sert à lancer les tests. Ils ne sont pas nécessaires pour exécuter l’application dans le conteneur.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY maintai/ maintai/
COPY ui/ ui/

ENV MAINTAI_MODELS_DIR=/app/models
ENV MAINTAI_DATA_PATH=/app/data/sensors.csv

EXPOSE 8000

CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build | 193s | 1.13GB |
| après une modification de `maintai/predict.py` | 1.54s | 1.13GB |

Que signifie `CACHED` dans le journal du second build ?

-> CACHED signifie que Docker a réutilisé une couche déjà construite, car les fichiers dont elle dépend n’ont pas changé. Comme requirements-docker.txt n’a pas été modifié, Docker n’a pas réinstallé les dépendances ; il a seulement reconstruit les couches concernées par le changement de code.

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "$(pwd)/models:/app/models:ro" maintai:0.4.0
50ed3f8d1b89bab772d88a6895c09e9f5fce57018b4b368082e3ec10034f664f
```

| Essai | Réponse |
|---|---|
| `GET /health` | 200 |
| `POST /v1/predict` sans clé | 401 |
| `POST /v1/predict` avec la clé | 200 |

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

-> /health répond que l’API fonctionne, mais indique "model_loaded": false. Une requête à /v1/predict échoue avec le code 503, car le conteneur ne trouve pas le fichier du modèle.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

-> Les logs montrent qu’Uvicorn démarre sur http://127.0.0.1:8000, mais curl vers http://localhost:8002/health échoue avec Recv failure: Connection reset by peer. Le serveur n’écoute que sur l’interface locale du conteneur. Pour que le port publié soit accessible depuis le Mac, Uvicorn doit écouter sur 0.0.0.0.

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
# MaintAI en deux conteneurs : l'API et l'interface Streamlit.
# Lancer : docker compose up --build      Arrêter : docker compose down

services:
  api:
    build: .
    image: maintai:0.4.0
    env_file: .env                     # MAINTAI_API_KEY, comme au TP2
    ports:
      - "8000:8000"                    # PC:conteneur
    # TODO TP6 sprint 2 : monter le dossier models du PC dans /app/models, en lecture seule
    volumes:
      - ./models:/app/models:ro

  # TODO TP6 sprint 2 : le service ui
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
tp6-api-1   maintai:0.4.0   Up   0.0.0.0:8000->8000/tcp
tp6-ui-1    maintai:0.4.0   Up   0.0.0.0:8501->8501/tcp
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

-> elle affichait http://localhost:8000 parce que ui/app.py utilise cette valeur fixe et ne lis pas encore MAINTAI_API_URL.

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
