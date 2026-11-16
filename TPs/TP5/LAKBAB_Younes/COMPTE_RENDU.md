# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** 1  ·  **Membres :** LAKBAB Younes  ·  **Date :** 16/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP5.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
 5 failed, 27 passed, 2 warnings in 40.84s
```

Quels tests échouent, et pourquoi ?

FAILED tests/test_tracking.py::test_training_creates_a_run - AssertionError: aucun run MLflow : log_run n'a rien enregistré
FAILED tests/test_tracking.py::test_run_records_metrics - AssertionError: aucun run MLflow : log_run n'a rien enregistré
FAILED tests/test_tracking.py::test_run_records_data_version - AssertionError: aucun run MLflow : log_run n'a rien enregistré
FAILED tests/test_tracking.py::test_run_stores_the_model - AssertionError: aucun run MLflow : log_run n'a rien enregistré
FAILED tests/test_tracking.py::test_options_change_the_run - AssertionError: aucun run MLflow : log_run n'a rien enregistré

Les cinq tests de tests/test_tracking.py échouent parce que la fonction log_run() n’est pas encore implémentée. Elle renvoie une chaîne vide et n’enregistre aucun run dans MLflow. Les tests ne peuvent donc pas vérifier les paramètres d’entraînement, les métriques, l’empreinte des données ni le modèle sauvegardé.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Avant la commande, le package installé dans l’environnement du TP4 pointait vers le code de TP/TP4. Après avoir exécuté pip install -e . depuis TP/TP5, il pointe vers le code de TP/TP5 en mode éditable.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

```python

def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement dans MLflow et renvoie son identifiant."""
    mlflow.set_experiment(EXPERIMENT)

    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))
        mlflow.log_metrics(metrics)

        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES,
        )

    return run.info.run_id

```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
32 passed, 4 warnings in 72.81s (0:01:12)
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.75| 0.622|0.904 |
| `python -m maintai.train --C 0.01` |0.691 | 0.653|0.908 |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train --threshold 0.25` | 0.794 |0.581 | 0.894|

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

Je retiens la **régression logistique avec un seuil de 0,2** (`python -m maintai.train --threshold 0.2`). Elle obtient le **meilleur rappel des cinq essais (83,8 %)**, contre **79,4 %** au seuil de 0,25, **75,0 %** avec le réglage par défaut et **72,8 %** pour la forêt aléatoire. Pour MaintAI, le rappel est prioritaire, car une panne manquée coûte plus cher qu’une fausse alerte.

Le seuil de 0,25 offre une meilleure précision (**58,1 %** contre **54,3 %**), mais il détecte moins de pannes. Je retiens donc le seuil de 0,2 en acceptant davantage de fausses alertes. L’essai `--C 0.01` obtient la meilleure accuracy (**90,8 %**), mais son rappel de **69,1 %** le rend moins adapté à cette priorité.

**Identifiant du run retenu :** `91186fe5f642416a8b985153c6398448`.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

Le fichier requirements.txt du modèle indique scikit-learn==1.8.0. Au TP4, la version figurait dans model_info.json. Avec MLflow, le modèle est accompagné d’un fichier de dépendances installable. Cela aide à recréer un environnement compatible et à éviter de recharger le modèle avec une version différente de celle utilisée pour l’entraînement.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Dans ce TP, la base locale mlflow.db contient les informations de suivi, notamment les paramètres et les métriques. Les artefacts des modèles sont stockés dans mlruns/. Ces éléments sont exclus de Git par le .gitignore : ils sont générés par les entraînements et ne font pas partie du code source.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv

```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

Le paramètre data_md5 du dernier run sur la v1 est identique au md5 du reçu DVC : 73e0b7cb3c6f795c70c3ddf970b99c15. Cela confirme que le fichier CSV utilisé pour cet entraînement est le même que celui versionné sous DVC en v1.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

DVC conserve les différentes versions du CSV dans son cache et dans le stockage configuré. Git ne conserve que le petit fichier data/sensors.csv.dvc, qui contient notamment l’empreinte, la taille et le chemin du CSV. Ce reçu permet à DVC de retrouver la bonne version sans ajouter les données elles-mêmes à l’historique Git.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
data\sensors.csv.dvc:
        changed outs:
                modified:           data\sensors.csv
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | dd45d5c | 73e0b7cb | 5000 |
| v2 | e3aa66e | 93fdeef2 | 8000 |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

J’ai restauré le reçu de la v1 à partir du commit dd45d5c, puis exécuté dvc checkout. Le CSV restauré contenait 5 000 relevés. J’ai ensuite remis le reçu de la v2 avec git checkout HEAD -- data/sensors.csv.dvc et relancé dvc checkout. Le CSV contenait de nouveau 8 000 relevés. Ces deux versions ont été restaurées depuis le cache DVC, sans régénérer les données.

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

En l’absence du CSV et du cache, dvc pull a lu le reçu data/sensors.csv.dvc, récupéré la v2 depuis le stockage DVC configuré et recréé le fichier data/sensors.csv. Le fichier restauré contient 8 000 relevés. Contrairement à dvc checkout, qui a utilisé le cache local lors du test précédent, dvc pull a récupéré les données depuis le stockage.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 | 73e0b7cb | 4 000 |  0.750 | 0.622 |
| v2 | 93fdeef2 |  6400 | 0.741 | 0.65 |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

Non, on ne peut pas conclure que le modèle entraîné sur la v2 est meilleur. Avec les mêmes réglages, la v2 obtient une **précision plus élevée** (65,0 % contre 62,2 %), mais un **rappel légèrement plus faible** (74,1 % contre 75,0 %). Sur son jeu de test, une plus grande part de ses alertes correspondent donc à de vraies pannes, mais elle détecte une plus faible proportion des pannes réelles. Or, pour MaintAI, le rappel est prioritaire, car une panne manquée coûte plus cher qu’une fausse alerte.

Il faut rester prudent : les deux modèles n’ont été ni entraînés ni évalués sur les mêmes données. L’écart de scores peut donc venir des différences entre les jeux de test, et pas seulement des modèles. Pour les départager, il faudrait les évaluer sur **un même jeu de test indépendant**, qui n’a servi à entraîner aucun des deux modèles.

## 5. Décision : l'ADR 004

Dans `docs/adr/004-choix-du-modele.md` : le modèle et le seuil retenus, à partir de votre tableau MLflow. Indiquez l'identifiant du run et le `data_md5` de la version des données utilisée.

## 6. Questions de compréhension

**1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?**

Git conserve l’historique du **code** et des petits fichiers `.dvc` qui identifient les versions des données. DVC conserve les différentes versions des **fichiers de données**, comme `data/sensors.csv`, et permet de les restaurer à partir de leur fichier `.dvc`. MLflow garde la trace de chaque **entraînement** : ses paramètres, ses métriques, le modèle obtenu et l’empreinte `data_md5` des données utilisées. Cette empreinte permet de relier un run MLflow à une version des données suivie par DVC.

**2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?**

Dans ce TP, le stockage DVC est un dossier sur mon PC. L’option `--local` enregistre ce chemin dans `.dvc/config.local`, qui n’est pas suivi par Git. Cela évite d’imposer aux autres membres un chemin qui n’existe que sur ma machine. Pour partager les données, il faudrait configurer un **stockage DVC commun** accessible à tous les membres du groupe. Un membre y envoie les données avec `dvc push`, puis les autres récupèrent le fichier `.dvc` depuis Git et lancent `dvc pull` pour télécharger la bonne version du CSV.

**3. Livrer un modèle, c’est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?**

1. **Le code** est suivi dans Git et peut être distribué sous la forme du paquet `wheel` préparé au TP4.
2. **Les données** sont conservées dans le stockage DVC ; leur version est identifiée par le fichier `.dvc` suivi dans Git.
3. **Le modèle entraîné** est sauvegardé dans MLflow et rattaché à un identifiant de run. Son fichier `requirements.txt` indique les versions des dépendances à installer pour le recharger dans un environnement compatible.

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp5` existe sur GitHub : oui / non
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? oui / non

## 8. Ce qui reste flou

…
