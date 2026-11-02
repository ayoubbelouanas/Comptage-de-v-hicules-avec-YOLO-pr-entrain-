# Compte rendu — TP2 : tester, sécuriser et appeler l’API MaintAI

Étudiant : BANANI Oussama  
Date : 02/11/2026

## 1. Activité 1 : casser l’API

Dans le dossier `tp/tp1`, j’ai testé cinq requêtes destinées à vérifier la robustesse de l’API.

| Requête | Problème | Code attendu | Code obtenu |
|---|---|---:|---:|
| 1 | Champ manquant | 422 | 422 |
| 2 | Valeur absurde | 422 | 422 |
| 3 | Texte au lieu d’un nombre | 422 | 422 |
| 4 | Champ supplémentaire | 422 | 422 |
| 5 | Mauvaise route | 404 | 404 |

Aucune prévision n’était fausse. Les cinq requêtes ont bien donné les codes attendus : 422 pour les données invalides et 404 pour la route inexistante. Cela confirme que l’API valide correctement les entrées et détecte correctement les routes inexistantes.

La commande `python -m pytest` a donné :

```text
==================== 19 passed, 1 warning in 4.60s ====================
```

J’ai obtenu 19 tests au lieu de 18, car le projet contient un test supplémentaire : `test_500_degres_est_refuse`. Ce test vérifie qu’une température de 500 °C est refusée. Les 18 tests prévus sont donc complétés par ce test additionnel.

### Utilité de `@pytest.mark.parametrize`

Le décorateur `@pytest.mark.parametrize` permet d’exécuter la même fonction de test avec plusieurs jeux de paramètres, sans avoir à écrire une fonction distincte pour chaque cas.

Dans ce TP, Pytest compte 5 tests pour `test_requete_refusee`, car la liste `CAS_REFUSES` contient 5 cas différents. Chaque paramètre génère une exécution indépendante, ce qui permet de tester plusieurs entrées invalides avec une seule fonction.

---

## 2. Ruff

La commande `ruff check .` a donné :

```text
All checks passed!
```

La commande `ruff check . --fix` a donné :

```text
Found 4 errors (4 fixed, 0 remaining).
```

La commande `ruff format .` a donné :

```text
19 files left unchanged
```

La commande `python -m pytest` a donné :

```text
================ 19 passed, 1 warning in 4.64s =================
```

### Différence entre Ruff et Pytest

- `ruff check .` effectue une analyse statique du code Python. Il détecte notamment les problèmes de style, les imports inutilisés et certaines mauvaises pratiques, sans exécuter le programme.
- `python -m pytest` exécute les tests automatiques afin de vérifier le comportement du programme et s’assurer que les résultats obtenus correspondent aux attentes.

Autrement dit, Ruff vérifie la qualité du code, tandis que Pytest vérifie son fonctionnement.

---

## 3. Mise en place du TP2

Le projet a ensuite été préparé dans le dossier `tp/tp2`. La sortie vérifiable correspond à l’état après la sécurisation de l’API :

```text
======================== 18 passed, 1 warning in 3.76s ========================
```

Je n’ai pas conservé de sortie fiable du premier lancement juste après la mise en place initiale. Je ne peux donc pas confirmer précisément quels tests échouaient à cette étape ni les codes HTTP obtenus. Toutefois, si les tests sur l’absence ou l’invalidité de la clé échouaient en renvoyant 200 au lieu de 401, cela pouvait s’expliquer par l’absence de dépendance d’authentification sur le routeur.

---

## 4. La clé API (sprint 1)

J’ai ajouté une fonction `require_api_key()` dans `maintai/api/security.py` :

```python
def require_api_key(
    x_api_key: str | None = Header(default=None),
) -> None:
    """Vérifie la présence et la validité de la clé API du client."""
    expected_key = get_settings().api_key

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé API non configurée sur le serveur",
        )

    if x_api_key is None or not secrets.compare_digest(
        x_api_key, expected_key
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
```

J’ai ensuite ajouté le routeur dans `maintai/api/main.py` :

```python
router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_api_key)],
)
```

### Si la fonction est écrite sans toucher au routeur

Si les deux tests concernés sont ceux qui vérifient l’absence et l’invalidité de la clé, ils échouent parce que `require_api_key()` n’est pas encore associée au routeur. Il faut en effet ajouter la dépendance avec `Depends(require_api_key)` pour que la vérification soit exécutée à chaque requête.

La dernière ligne de `python -m pytest` à la fin du sprint 1 est :

```text
======================== 18 passed, 1 warning in 3.76s ========================
```

### Résultats des requêtes HTTP

Après avoir démarré le serveur avec :

```powershell
uvicorn maintai.api.main:app --reload --env-file .env
```

Les résultats obtenus sont les suivants :

| Requête | Code obtenu | Réponse |
|---|---:|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | `{"failure_probability":0.9475,"alert":true,"threshold":0.3,"model_version":"2026-11-02T12:08:40Z"}` |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | Erreur de validation : température > 150 °C |

La réponse pour le dernier cas est :

```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "temperature_c"],
      "msg": "Input should be less than or equal to 150",
      "input": 500,
      "ctx": {"le": 150}
    }
  ]
}
```

### Pourquoi 500 °C donne-t-il 401 sans clé mais 422 avec une clé valide ?

Sans clé, la dépendance d’authentification bloque immédiatement la requête avec un code 401, avant même la validation des données.

Avec une clé valide, l’API passe l’étape d’authentification, puis la validation Pydantic vérifie le corps de la requête. La température 500 °C est supérieure à la limite autorisée (150 °C), ce qui entraîne un code 422.

### Relancer Uvicorn sans `--env-file .env`

Si j’envoie un relevé avec la clé sans définir `MAINTAI_API_KEY` dans l’environnement du serveur, j’obtiens un code 500.

Cela est logique car le serveur n’a aucune clé de référence pour vérifier la clé fournie par le client. Le message retourné est alors :

```text
Clé API non configurée sur le serveur
```

Le code 401 est réservé au cas où le serveur a bien une clé configurée, mais que le client envoie une clé absente ou incorrecte.

---

## 5. La page web (sprint 2)

Le code JavaScript utilisé dans `web/index.html` est le suivant :

```javascript
document.getElementById("go").addEventListener("click", async () => {
  const button = document.getElementById("go");

  const reading = Object.fromEntries(
    FEATURES.map(f => [
      f,
      Number(document.getElementById(f).value)
    ])
  );

  const url = document.getElementById("url").value.trim().replace(/\/+$/, "");
  const key = document.getElementById("key").value.trim();

  if (!key) {
    show("err", "Veuillez saisir votre clé API.");
    return;
  }

  button.disabled = true;
  show("ok", "Prédiction en cours...");

  try {
    const response = await fetch(`${url}/v1/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": key
      },
      body: JSON.stringify(reading)
    });

    const data = await response.json();

    if (!response.ok) {
      show("err", `Erreur ${response.status} : ${JSON.stringify(data)}`);
      return;
    }

    show("ok", "Prédiction réussie :\n" +
      JSON.stringify(data, null, 2));

  } catch (error) {
    show("err", "Impossible de contacter l'API : " + error.message);
  } finally {
    button.disabled = false;
  }
});
```

### Résultats affichés par la page

La page est servie sur `http://127.0.0.1:5501`.

| Essai | Résultat affiché |
|---|---|
| Relevé normal avec une bonne clé | Prédiction réussie : probabilité de défaillance de 0,9475 et alerte activée |
| Température de 500 °C avec une bonne clé | Erreur 422 : température supérieure à la limite autorisée de 150 °C |
| Relevé normal avec une fausse clé | Erreur 401 : clé API absente ou invalide |

### Expérience CORS

Lorsque la page est servie depuis `http://127.0.0.1:5501`, elle fonctionne car cette origine est bien autorisée dans la configuration CORS.

En revanche, une origine non autorisée, comme `http://127.0.0.1:9999`, est rejetée par le serveur. Le navigateur bloque alors la requête et affiche une erreur CORS dans la console.

### Pourquoi `curl.exe` fonctionne alors que la page web est bloquée ?

`curl.exe` ne tient pas compte de la politique CORS. CORS est une protection imposée par les navigateurs pour les pages web, afin d’empêcher un script JavaScript d’une origine non autorisée d’accéder à une autre API. Le serveur peut donc répondre à une requête `curl`, même si le navigateur bloque une requête issue d’une page web provenant d’une origine non autorisée.

---

## 6. Les tests de l’activité 1 dans le TP2

J’ai copié `test_casser.py` dans `tp/tp2/tests`.

### Sans `headers=HEADERS`

Sans l’en-tête `X-API-Key`, quatre tests échouent avec un code 401 Unauthorized. Ces quatre cas appellent une route protégée (`/v1/predict`) sans clé valide.

Le cinquième cas, qui utilise une mauvaise route (`/v1/inconnue`), retourne 404 Not Found. Ce cas passe quand même, car la route n’existe pas et la dépendance d’authentification n’est donc pas exécutée.

### Dernière ligne de `python -m pytest` avec `headers=HEADERS`

Après avoir ajouté l’en-tête `X-API-Key`, les tests passent bien :

```text
collected 23 items

tests\test_api.py .......          [ 30%]
tests\test_casser.py .....         [ 52%]
tests\test_data.py ...             [ 65%]
tests\test_security.py .....       [ 86%]
tests\test_train.py ...            [100%]

23 passed, 1 warning in 2.65s
```

Les cinq tests de résistance sont validés : les quatre cas invalides retournent 422, tandis que la route inexistante retourne 404. Au total, les 23 tests du TP2 passent.

---

## 7. Questions de compréhension

### 1. Différence entre 401 et 422 ; et entre 401 et 403

- 401 Unauthorized : l’authentification est absente ou invalide.
- 422 Unprocessable Entity : la requête est bien comprise, mais les données envoyées ne respectent pas les règles de validation.
- 403 Forbidden : le client est authentifié, mais il n’a pas les droits nécessaires pour accéder à la ressource.

### 2. Pourquoi la clé n’est-elle ni dans le code ni dans Git ?

La clé API est un secret. Elle ne doit pas être exposée dans le dépôt public.

- `.env` contient les variables locales réelles, y compris la vraie clé API. Il ne doit pas être ajouté au dépôt.
- `.env.example` contient un exemple de configuration sans valeur sensible. Il peut être versionné pour montrer aux autres développeurs comment configurer le projet.

### 3. Pourquoi la clé est-elle transmise dans un en-tête et pas dans l’URL ?

Une clé dans l’URL peut être enregistrée dans l’historique, les logs du serveur, ou les liens partagés. Un en-tête HTTP, comme `X-API-Key`, évite davantage ces risques. Cependant, il faut impérativement utiliser HTTPS pour sécuriser la transmission de la clé sur le réseau.

### 4. Que fait `secrets.compare_digest` de plus qu’un simple `==` ?

`secrets.compare_digest` compare les chaînes de manière sécurisée et réduit le risque d’attaque par analyse temporelle. Il limite les différences de durée d’exécution selon les caractères comparés, ce qui rend les attaques plus difficiles.

### 5. Qu’est-ce qu’une “origine” ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?

Une origine est définie par trois éléments : le schéma, l’hôte et le port.

Donc `http://localhost:5500` et `http://localhost:8000` ne sont pas la même origine, car le port est différent. CORS considère qu’une origine différente est une origine distincte, même si le site est local et le même serveur.

---

## 8. Rendu Git

Le dépôt GitHub utilisé est :

- [classification-des-reclamations-clients](https://github.com/wiam1237/classification-des-reclamations-clients)

Détails :
- Dossier de rendu : `tp/tp2`
- Branche principale : `main`
- Branche de travail : `tp2-maintai`
- La branche `tp2-maintai` a été fusionnée dans `main`, puis les modifications ont été poussées sur GitHub.
- Il n’y a pas eu de Pull Request ; l’intégration a été faite directement.
- Le tag `tp2` doit être vérifié.
- Les fichiers sensibles comme `.env` et l’environnement virtuel ne sont pas inclus dans le dépôt.
- Aucun reviewer n’était nécessaire, car il n’y a pas eu de Pull Request.

Le travail du TP2 est donc disponible dans le dépôt GitHub, dans le dossier `tp/tp2`, sur la branche principale `main`.

---

## 9. Ce qui reste flou

La différence entre `localhost` et `127.0.0.1` est importante pour CORS. Même sur le même ordinateur et avec le même port, ces deux hôtes ne sont pas identiques pour le navigateur. Il faut donc autoriser dans la configuration CORS l’origine exacte utilisée par la page web.

Par exemple, `http://localhost:5501` et `http://127.0.0.1:5501` sont deux origines distinctes, même si elles pointent vers la même machine.
