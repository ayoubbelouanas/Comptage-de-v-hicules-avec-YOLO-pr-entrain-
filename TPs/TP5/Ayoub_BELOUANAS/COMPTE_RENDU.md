# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** …  ·  **Membres :** Ayoub BELOUANAS  ·  **Date :** 16/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP5.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
5 failed, 27 passed, 2 warnings in 92.71s (0:01:32)
```

Quels tests échouent, et pourquoi ?

FAILED tests/test_tracking.py::test_training_creates_a_run - AssertionError: aucun run MLflow : log_run n'a rien enregistré
FAILED tests/test_tracking.py::test_run_records_metrics - AssertionError: aucun run MLflow : log_run n'a rien enregistré
FAILED tests/test_tracking.py::test_run_records_data_version - AssertionError: aucun run MLflow : log_run n'a rien enregistré
FAILED tests/test_tracking.py::test_run_stores_the_model - AssertionError: aucun run MLflow : log_run n'a rien enregistré
FAILED tests/test_tracking.py::test_options_change_the_run - AssertionError: aucun run MLflow : log_run n'a rien enregistré

-> Les cinq tests de tests/test_tracking.py échouent parce que log_run n’enregistre pas encore les entraînements dans MLflow. Aucun run n’est donc disponible pour vérifier ses paramètres, ses métriques, la version des données ou le modèle.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

-> Avant pip install -e ., maintai pointait vers le code du TP4. Après l’installation éditable dans le TP5, il pointe vers /Users/sm/Desktop/Emsi_5/Dev App AI/TP5/maintai/__init__.py.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    # TODO TP5 sprint 1 : enregistrer le run dans MLflow
    # Choisit l’expérience commune à tous les entraînements MaintAI.
    mlflow.set_experiment(EXPERIMENT)

    # Regroupe paramètres, version des données, métriques et modèle dans un run.
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        # Enregistre l’empreinte pour retrouver les données utilisées.
        mlflow.log_param("data_md5", file_md5(data_path))

        mlflow.log_metrics(metrics)

        # Stocke le pipeline complet, avec un exemple d'entrée pour l'interface MLflow.
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES,
        )

        run_id = run.info.run_id
    return run_id
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
32 passed, 4 warnings in 31.85s
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.75 | 0.622 | 0.904|
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| (votre essai) | | | |

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

-> Je choisirais le run `--threshold 0.2`, car son rappel est le plus élevé (0,838). Il détecte davantage de pannes, ce qui est prioritaire puisque manquer une panne coûte plus cher qu’une fausse alerte. En contrepartie, sa précision (0,543) et son exactitude (0,882) sont plus faibles.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

-> scikit-learn==1.8.0 
-> Cette version enregistrée avec le modèle aide à éviter le problème de compatibilité rencontré au TP4, quand le modèle avait été entraîné avec une version différente de scikit-learn.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

-> MLflow enregistre les informations de suivi dans `mlflow.db` et les artefacts des runs dans `mlruns/`, dans le dossier TP5. Ces fichiers ne sont pas à versionner avec Git : ce sont des résultats générés par les entraînements et ils peuvent prendre beaucoup de place. Git conserve le code ; MLflow conserve les runs et DVC gère les versions des données.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: b7fec4274774842dc1f48202c6013490
  size: 121814
  hash: md5
  path: sensors.csv

```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

- params.data_md5 : b7fec4274774842dc1f48202c6013490
- md5: b7fec4274774842dc1f48202c6013490

Ils ont le même Hashage.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

…

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
data/sensors.csv.dvc:                                                                                                               
        changed outs:
                modified:           data/sensors.csv
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | 559fbfd chore(dvc): track dataset v1 | b7fec4274774842dc1f48202c6013490 | 5000 |
| v2 | fd044e8 (HEAD -> main) data: track dataset v2 | 31ef5ebb63ef2331a31dfe009ef8796a | 8000 |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

(.venv) (base) sm@MacBookPro TP5 % git checkout 559fbfd -- data/sensors.csv.dvc
dvc checkout
wc -l data/sensors.csv
Building workspace index                                                                                  |2.00 [00:00, 69.8entry/s]
Comparing indexes                                                                                         |3.00 [00:00,  301entry/s]
Applying changes                                                                                          |1.00 [00:00,   375file/s]
M       data/sensors.csv
    5001 data/sensors.csv


 (base) sm@MacBookPro TP5 % git checkout fd044e8 -- data/sensors.csv.dvc
dvc checkout
wc -l data/sensors.csv
Building workspace index                                                                                  |2.00 [00:00, 94.5entry/s]
Comparing indexes                                                                                         |3.00 [00:00,  709entry/s]
Applying changes                                                                                          |1.00 [00:00,   377file/s]
M       data/sensors.csv
    8001 data/sensors.csv

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

-> dvc pull récupère le fichier depuis ce stockage et recrée data/sensors.csv, même après la suppression du CSV et du cache local.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 | b7fec4274774842dc1f48202c6013490 | 4000 | 0.728 | 0.562 |
| v2 | 31ef5ebb63ef2331a31dfe009ef8796a | 6400 | 0.741 | 0.65 |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

-> on ne peut pas conclure que le modèle v2 est « meilleur » simplement parce que ses métriques sont plus hautes : il a été entraîné sur des données différentes et plus nombreuses. La comparaison dépend aussi de la composition des données et de la séparation entraînement/évaluation. Il faut donc interpréter les métriques avec prudence.

## 5. Décision : l'ADR 004

Dans `docs/adr/004-choix-du-modele.md` : le modèle et le seuil retenus, à partir de votre tableau MLflow. Indiquez l'identifiant du run et le `data_md5` de la version des données utilisée.

## 6. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?

   -> Git versionne le code et les fichiers de configuration. DVC suit les versions des données et permet de retrouver les fichiers correspondants. MLflow conserve les paramètres, les métriques, les versions des données associées aux runs et les artefacts des modèles.

2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?
   
   -> Le stockage DVC est configuré avec --local pour que son chemin reste dans la configuration locale, sans être partagé dans Git. Pour partager les données en groupe, il faudrait un stockage distant commun, accessible à tous, puis configurer chaque poste avec ce même stockage et les accès nécessaires.

3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
   
   -> Livrer un modèle demande le code, le modèle entraîné et les dépendances nécessaires pour l’exécuter. Ici, le code est dans Git, le modèle entraîné est enregistré parmi les artefacts MLflow, et les dépendances sont déclarées dans pyproject.toml et requirements.txt.

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp5` existe sur GitHub : oui / non
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? oui / non

## 8. Ce qui reste flou

…

## GridSearch

Nous avons comparé 25 configurations d’hyperparamètres avec une recherche sur grille. Le run retenu utilise une forêt aléatoire avec `n_estimators=50`, `max_depth=None` et un seuil de décision de `0.3`.

| Modèle retenu | Rappel | Précision | Accuracy | n_train |
|---|---:|---:|---:|---:|
| Forêt aléatoire | 0.760 | 0.592 | 0.902 | 4800 |

Run MLflow : `76e846314add4c62a17bce437ecb8d3a`  
data_md5 : `31ef5ebb63ef2331a31dfe009ef8796a`

Le rappel de 0.760 signifie que le modèle a détecté 76 % des pannes dans l’évaluation enregistrée par MLflow. La précision de 0.592 indique que 59,2 % des alertes émises correspondaient à une panne.
