# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :**  ·  **Membres :** Younes LAKBAB  ·  **Date :** 02-11-2026

> Ce compte rendu conserve les neuf rubriques et les questions du modèle original du professeur. Les explications sont rédigées. Les sorties de terminal et les codes HTTP non observés sur mon ordinateur sont clairement distingués des résultats attendus.

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| `POST /v1/predict` sans `load_pct` | champ manquant | 422 | **[à vérifier : 422 attendu]** |
| `POST /v1/predict` avec `load_pct: 250` | valeur absurde | 422 | **[à vérifier : 422 attendu]** |
| `POST /v1/predict` avec `temperature_c: "chaud"` | texte au lieu d'un nombre | 422 | **[à vérifier : 422 attendu]** |
| `POST /v1/predict` avec `pression_bar: 5` en plus des quatre champs | champ en trop | 422 | **[à vérifier : 422 attendu]** |
| `POST /v1/prediction` | mauvaise route | 404 | **[à vérifier : 404 attendu]** |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

**Réponse :** Les cinq codes prévus sont cohérents avec le schéma et les routes définis dans MaintAI. Le champ manquant, la valeur hors bornes, le texte non numérique et le champ supplémentaire sont refusés par Pydantic avec **422** (`extra="forbid"` bloque les champs inconnus). Une route qui n'existe pas renvoie **404**. La concordance avec les codes réellement obtenus reste à confirmer à partir des essais.

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```text
18 passed
```

*Résultat attendu avec les 13 tests initiaux du TP1 et les cinq nouveaux cas. À remplacer par la sortie réelle de `python -m pytest -v`.*

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

**Réponse :** Le décorateur `@pytest.mark.parametrize` exécute une fonction avec plusieurs ensembles de paramètres. `CAS_REFUSES` comporte cinq tuples : pytest considère donc **cinq tests distincts**, bien qu'une seule fonction `test_requete_refusee()` soit écrite. Chaque tuple précise la description du cas, l'URL, le corps JSON et le code HTTP attendu.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```text
[À compléter : coller ici la sortie exacte de « ruff check . » lancée dans TP/TP1]
Résultat visé après correction : All checks passed!
```

*L'exemple du camarade indique une alerte `UP017` sur `datetime.now(timezone.utc)` ; ce résultat ne peut pas être présenté comme la sortie de ma machine sans avoir exécuté Ruff.*

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

**Réponse :** `ruff check .` analyse statiquement le code sans l'exécuter : qualité, conventions, imports inutiles et certaines erreurs possibles. `python -m pytest` **exécute les tests** et vérifie que les fonctions et les routes se comportent comme prévu. Les deux outils sont complémentaires : Ruff améliore la qualité du code, pytest contrôle son fonctionnement.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```text
2 failed, 16 passed
```


Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

**Réponse :** Les tests `test_missing_key_is_rejected` et `test_wrong_key_is_rejected` échouent. Au départ, la route de prédiction ne déclenche pas encore la fonction de contrôle de la clé : les deux requêtes reçoivent alors **200 au lieu de 401**, si le modèle est disponible.

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Vérifie la clé transmise dans l'en-tête X-API-Key."""
    api_key_attendue = get_settings().api_key

    if not api_key_attendue:
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

Cette fonction s'appuie sur les imports `secrets`, `Header`, `HTTPException`, `status` et `get_settings` déjà présents dans le starter.

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_api_key)],
)
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

**Réponse :** Deux tests échouent toujours, car définir `require_api_key()` ne suffit pas : la fonction n'est pas appelée automatiquement. L'ajout de `Depends(require_api_key)` au routeur `/v1` permet de vérifier la clé avant chaque prédiction.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```text
18 passed
```


Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl.exe`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | **[à confirmer : 200 attendu]** | `{"status":"ok","model_loaded":true}` si le modèle est chargé ; `false` sinon. |
| `POST /v1/predict`, relevé normal, sans clé | **[à confirmer : 401 attendu]** | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | **[à confirmer : 401 attendu]** | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | **503 observé sur la page web avant chargement du modèle** ; 200 attendu après correction | `{"detail":"Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API"}` au moment de l'erreur ; après correction, objet avec `failure_probability`, `alert`, `threshold`, `model_version`. |
| `POST /v1/predict`, 500 °C, sans clé | **[à confirmer : 401 attendu]** | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | **[à confirmer : 422 attendu]** | Validation Pydantic indiquant que `temperature_c` doit être inférieure ou égale à 150 °C. |

*Le 503 a été visible dans une capture de mon application ; les autres lignes décrivent les réponses prévues et doivent être complétées avec les observations réelles. Le chargement du modèle se corrige avec `python -m maintai.dataset`, puis `python -m maintai.train` et un redémarrage d'Uvicorn.*

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

**Réponse :** L'authentification est contrôlée avant la validation des données. Sans clé correcte, FastAPI répond **401** immédiatement. Avec la bonne clé, le corps JSON est examiné et 500 °C est rejeté avec **422**, puisque la borne maximale vaut 150 °C.

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

**Réponse attendue :** **500**, avec un message du type `{"detail":"Clé API non configurée"}`, si `MAINTAI_API_KEY` n'est définie dans aucune autre variable d'environnement. Le problème vient de la configuration du serveur et non d'une clé incorrecte transmise par le client, d'où le code 500 plutôt que 401. *Essai à confirmer sur la machine.*

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
document.getElementById("go").addEventListener("click", async () => {
  const reading = Object.fromEntries(
    FEATURES.map(f => [f, Number(document.getElementById(f).value)])
  );
  const apiUrl = document.getElementById("url").value.trim().replace(/\/+$/, "");
  const apiKey = document.getElementById("key").value.trim();

  try {
    const resp = await fetch(`${apiUrl}/v1/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify(reading),
    });

    const data = await resp.json();
    if (!resp.ok) {
      const detail = typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail);
      show("err", `Erreur HTTP ${resp.status} : ${detail}`);
      return;
    }

    const probabilite = (data.failure_probability * 100).toFixed(1);
    show(
      data.alert ? "alert" : "ok",
      `Probabilité de panne : ${probabilite} % — ${data.alert ? "Alerte" : "Pas d'alerte"}`
    );
  } catch (error) {
    show("err", `API injoignable ou blocage CORS : ${error.message}`);
  }
});
```

Ce qu'affiche la page (servie sur le port 5500) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | **« Erreur 503 : Modèle non chargé » a été observée** lors d'un essai ; après entraînement et redémarrage, la page doit afficher la probabilité calculée et l'état d'alerte. |
| 500 °C, bonne clé | **Attendu, à vérifier :** `Erreur HTTP 422` avec le détail de la borne. |
| relevé normal, fausse clé | **Attendu, à vérifier :** `Erreur HTTP 401 : Clé API absente ou invalide`. |

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

**Réponse attendue (à vérifier) :** Lorsque la page est ouverte sur `http://localhost:5501`, l'appel `fetch()` est bloqué par le navigateur, car cette origine n'appartient pas à la liste autorisée. La page peut afficher « API injoignable ou blocage CORS : Failed to fetch ». La console (F12) signale l'absence d'autorisation CORS pour cette origine.

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

**Réponse :** Le contrôle CORS est appliqué par les navigateurs. `curl.exe` n'applique pas cette politique et peut envoyer directement la requête. CORS ne remplace donc pas une authentification : la clé `X-API-Key` demeure nécessaire pour accéder à `/v1/predict`.

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

**Réponse :** Sans `headers=HEADERS`, les **quatre cas de validation** reçoivent **401** à la place du 422 attendu et échouent : la clé API est vérifiée avant le corps JSON. Le cinquième cas, « mauvaise route » (`POST /v1/prediction`), passe quand même et reçoit **404**, car aucune route correspondante n'existe et la dépendance du routeur n'est pas exécutée.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```text
23 passed
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?

   **Réponse :** **401** indique que la clé d'authentification est absente ou invalide ; **422** indique que les données de la requête ne respectent pas les règles Pydantic ; **403** indique que le client a été authentifié, mais n'est pas autorisé à effectuer l'action.

2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?

   **Réponse :** Une clé insérée dans le code ou envoyée sur GitHub peut être divulguée et rester dans l'historique du dépôt. `.env` contient les vraies valeurs locales et doit être exclu de Git. `.env.example` ne contient que des valeurs fictives et peut être commité pour documenter les paramètres nécessaires.

3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?

   **Réponse :** L'en-tête HTTP `X-API-Key` évite d'exposer la clé dans l'URL, qui peut être conservée dans l'historique du navigateur, les journaux ou certains outils de suivi.

4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?

   **Réponse :** `secrets.compare_digest()` limite les différences de temps observables pendant la comparaison de secrets, et réduit ainsi certains risques d'attaque par analyse temporelle.

5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?

   **Réponse :** Une origine est la combinaison du **protocole**, de l'**hôte** et du **port**. Les deux URL ne sont **pas de la même origine**, car leurs ports sont différents : `5500` pour la page web et `8000` pour l'API.

## 8. Le rendu Git

- Lien de la pull request : **[à renseigner avec le lien réel]**.
- Le tag `tp2` existe sur GitHub : **[oui / non — à vérifier]**.
- `git status` avant le commit : le fichier `.env` apparaissait-il ? **[oui / non — à vérifier ; il ne doit pas être versionné]**.
- Qui a relu la pull request, et quel commentaire a-t-il laissé ? **[nom du relecteur et commentaire réel à ajouter]**.

Le dépôt doit inclure `COMPTE_RENDU.md` et `docs/adr/003-securite.md`, mais pas `.env`, `.venv`, les données générées ni les modèles entraînés.

## 9. Ce qui reste flou

Le point qui demandait une vérification pratique était la distinction entre les trois situations : **401** lorsque la clé API est refusée, **422** lorsque les mesures sont invalides, et **503** lorsque le modèle n'est pas chargé. L'erreur 503 observée sur le client web a permis de comprendre que l'API peut fonctionner et authentifier le client tout en ne disposant pas encore d'un modèle prêt à prédire.
