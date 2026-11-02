# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** …  ·  **Membres :** Ayoub BELOUANAS  ·  **Date :** 02-11-2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| POST /v1/predict — sans runtime_hours | champ manquant | 422 | 422 |
| POST /v1/predict — temperature_c: 999 | valeur absurde | 422 | 422 |
| POST /v1/predict — temperature_c: "chaud" | texte au lieu d'un nombre | 422 | 422 |
| POST /v1/predict — champ supplémentaire couleur: "rouge"| champ en trop | 422 | 422 |
| POST /v1/prediction | mauvaise route | 404 | 404 |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

-> Non, les cinq prévisions étaient correctes.

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
19 passed, 1 warning in 3.44s 
```

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

-> @pytest.mark.parametrize permet d’exécuter la même fonction de test plusieurs fois avec des valeurs différentes. Ici, Pytest compte 5 tests pour test_requete_refusee, car CAS_REFUSES contient cinq cas. La fonction est écrite une seule fois, mais elle est appelée une fois par tuple, avec sa description, son URL, son corps et le code attendu. Chaque cas apparaît séparément dans le résultat de Pytest.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
(.venv) (base) sm@AYOUBs-MacBook-Pro maintai-starter-tp1 % ruff check
UP017 [*] Use `datetime.UTC` alias
  --> maintai/train.py:58:36
   |
56 |         "target": TARGET,
57 |         "threshold": settings.threshold,
58 |         "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
   |                                    ^^^^^^^^^^^^
59 |         "sklearn_version": sklearn.__version__,
60 |     }
   |
help: Convert to `datetime.UTC` alias
   |
5  | import json
   - from datetime import datetime, timezone
6  + from datetime import datetime, timezone, UTC
7  |
--------------------------------------------------------------------------------
57 |         "threshold": settings.threshold,
   -         "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
58 +         "trained_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
59 |         "sklearn_version": sklearn.__version__,
   |

Found 1 error.
[*] 1 fixable with `--fix`.
```

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

-> `ruff check .` analyse le code pour trouver des problèmes de style et certaines erreurs potentielles, comme des imports inutilisés. Il ne lance pas l’application ni les tests.
 
-> `python -m pytest` exécute les fonctions de test du projet et vérifie que leur comportement correspond aux résultats attendus.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
2 failed, 16 passed, 1 warning in 3.87s 
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

-> test_missing_key_is_rejected et test_wrong_key_is_rejected échouent. Les deux reçoivent 200 au lieu de 401, car la vérification de la clé n’est pas encore attachée au router /v1.

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
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
```

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_api_key)],
)
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

-> Deux tests échouent encore, car require_api_key() existe mais n’est pas encore appelée par le router. Les requêtes sans clé ou avec une fausse clé reçoivent donc encore 200.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
18 passed, 1 warning in 3.58s
```

Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl.exe`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | 200 | {"status":"ok","model_loaded":true}|
| `POST /v1/predict`, relevé normal, sans clé | 401 | {"detail":"Clé API absente ou invalide"} |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | {"detail":"Clé API absente ou invalide"} |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | {"failure_probability": 0.8843,"alert": true,"threshold": 0.3,"model_version":"2026-11-02T12:02:21Z"} |
| `POST /v1/predict`, 500 °C, sans clé | 401 | {"detail":"Clé API absente ou invalide"} |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | "Input should be less than or equal to 150" |

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

-> La clé est vérifiée avant la validation des données. Sans clé, l’API renvoie 401. Avec une clé valide, elle examine le relevé et renvoie 422 parce que 500 °C dépasse la limite autorisée.

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

-> J’obtiens 500, avec {"detail":"Clé API non configurée"}. Sans --env-file .env, le serveur ne charge pas la clé attendue. C’est une erreur de configuration du serveur, pas une clé client absente ou incorrecte, qui donnerait 401.

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
/**
 * Envoie le relevé saisi à l’API et affiche l’erreur reçue
 * ou la probabilité de panne et l’état de l’alerte.
 */
document.getElementById("go").addEventListener("click", async () => {
  const reading = Object.fromEntries(
    FEATURES.map(f => [f, Number(document.getElementById(f).value)])
  );
  const apiUrl = document.getElementById("url").value.trim().replace(/\/+$/, "");
  const apiKey = document.getElementById("key").value.trim();

  try {
    // Envoie les données JSON et la clé API dans l’en-tête prévu.
    const resp = await fetch(`${apiUrl}/v1/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify(reading),
    });

    const data = await resp.json();

    // Affiche le code et le détail si l’API refuse la requête.
    if (!resp.ok) {
      show("err", `Erreur HTTP ${resp.status} : ${data.detail ?? "requête refusée"}`);
      return;
    }

    // Affiche la probabilité et choisit le style selon l’alerte.
    const probabilite = (data.failure_probability * 100).toFixed(1);
    const message = `Probabilité de panne : ${probabilite} % — ${
      data.alert ? "Alerte" : "Pas d’alerte"
    }`;
    show(data.alert ? "alert" : "ok", message);
  } catch (error) {
    // Une API arrêtée ou un blocage CORS empêche la réponse d’arriver.
    show("err", `API injoignable ou blocage CORS : ${error.message}`);
  }
});
```

Ce qu'affiche la page (servie sur le port 5500) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | Probabilité de panne : 87.4 % — Alerte |
| 500 °C, bonne clé | Erreur HTTP 422 : [object Object] |
| relevé normal, fausse clé | Erreur HTTP 401 : Clé API absente ou invalide |

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

-> 

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

-> Sur le port 5501, la page affiche « API injoignable ou blocage CORS : Failed to fetch ». Dans la console (F12), le navigateur signale que la requête vers http://localhost:8000 est bloquée par CORS : l’origine http://localhost:5501 n’est pas autorisée par l’API. 

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

-> Sans headers=HEADERS, 4 tests échouent et reçoivent 401 au lieu de 422 : l’authentification est vérifiée avant la validation du corps. Le cas « mauvaise route » passe quand même : /v1/prediction n’existe pas, donc il renvoie 404 sans déclencher la dépendance du router /v1.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
4 failed, 19 passed, 1 warning in 3.24s
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   -> 401 signifie que le client n’est pas authentifié : sa clé est absente ou incorrecte. 422 signifie que la requête est comprise, mais que ses données ne respectent pas les règles de validation. 403 signifie que le client est authentifié, mais qu’il n’a pas le droit d’effectuer l’action.

2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   -> La clé ne doit pas être dans le code ni dans Git, car elle pourrait être publiée et rester dans l’historique du dépôt. .env contient les vraies valeurs locales et est ignoré par Git. .env.example contient des valeurs fictives pour montrer la configuration attendue ; lui est commité.

3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   -> La clé est envoyée dans l’en-tête X-API-Key pour éviter qu’elle apparaisse dans l’URL, qui peut être enregistrée dans l’historique du navigateur et les journaux du serveur.

4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   -> secrets.compare_digest compare les clés de manière conçue pour limiter les fuites d’information par le temps de comparaison. Avec un simple ==, la comparaison peut s’arrêter dès le premier caractère différent.

5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   ->

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp2` existe sur GitHub : oui / non
- `git status` avant le commit : le fichier `.env` apparaissait-il ? oui / non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  …

## 9. Ce qui reste flou

…
