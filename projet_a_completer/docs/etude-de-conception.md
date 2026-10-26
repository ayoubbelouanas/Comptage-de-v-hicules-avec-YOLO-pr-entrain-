# Étude de conception — Système intelligent de classification des pannes d’équipements industriels

**Groupe :** Oussama BANANI & Ayoub BELOUANAS & Mohamed NEJJARI & Younes LAKBAB 

**Date :** 26/10/2026


## 1. Contexte et utilisateurs

Dans le cadre de la surveillance d'équipements industriels, les opérateurs disposent de mesures relatives à l'état et à l'utilisation des machines : température, vibration, charge et durée de fonctionnement. Le projet vise à exploiter ces mesures pour **classifier un enregistrement comme « panne » (`failure = 1`) ou « absence de panne » (`failure = 0`)** et faciliter la priorisation des contrôles.

- **Utilisateur principal (un rôle précis) :** technicien de maintenance industrielle chargé de contrôler les équipements signalés à risque.
- **Utilisateurs secondaires :** responsable de maintenance, chargé de planifier les interventions et d'examiner les performances du système.
- **Bénéfice attendu :** repérer les situations suspectes plus systématiquement et affecter les ressources de maintenance aux cas prioritaires.
- **Contexte d'utilisation :** prototype hors ligne à partir d'un fichier CSV. L'intégration en temps réel aux capteurs ou à un système industriel n'est pas implémentée.

## 2. Problème et décision

- **Problème :** à partir de quatre indicateurs numériques, déterminer si une observation appartient à la classe « panne » ou « pas de panne ».
- **Décision que l'utilisateur prend avec le système :** en cas de signalement, vérifier l'équipement, compléter le diagnostic et décider d'une inspection ou d'une intervention ; en cas de signalement négatif, poursuivre la surveillance selon les procédures habituelles.
- **Fréquence :** à chaque nouvel enregistrement disponible ou lors de chaque campagne d'analyse, selon la future cadence d'acquisition ; fréquence réelle non définie dans les données.
- **Coût d'une erreur et pour qui :**
  - **Faux négatif** (panne réelle non détectée) : risque d'immobilisation, de perte de production et, selon l'équipement, de conséquences sur la sécurité ; impact sur la maintenance, l'exploitation et les personnes exposées.
  - **Faux positif** (alerte injustifiée) : inspection superflue, temps mobilisé, éventuel arrêt inutile ; impact sur les techniciens et les opérations.
- **Règle de décision :** l'algorithme **assiste** l'agent de maintenance et ne déclenche jamais seul un arrêt ou une manœuvre de sécurité.

**Attention à la portée du problème :** sans date d'observation, identifiant de machine ni horizon de prédiction, le CSV permet une **classification d'état**, pas une prévision validée d'une panne à J+1, J+7, etc.

## 3. Approche par sous-problème

| Sous-problème | Approche (règles / ML / DL / LLM / RAG) | Pourquoi pas une approche plus simple |
|---|---|---|
| Lire les données et vérifier les colonnes | **Règles** avec `pandas` | Le chargement, les types et la présence de `failure` se vérifient sans apprentissage. |
| Gérer les données manquantes et normaliser | **Règles statistiques** : médiane et standardisation | Aucun réseau profond n'est nécessaire pour quatre mesures numériques. |
| Établir un niveau de référence | **Baseline** `DummyClassifier(strategy="most_frequent")` | Référence simple obligatoire pour démontrer l'apport réel du ML. |
| Identifier la classe `failure` | **ML supervisé** : régression logistique, arbre de décision, forêt aléatoire, gradient boosting | Une règle à seuil unique ne décrit pas forcément les interactions entre charge, vibration, température et heures de fonctionnement ; elle pourra néanmoins être comparée si des seuils métier sont connus. |
| Évaluer les alertes et choisir un modèle | **Métriques et règles de sélection** : rappel prioritaire, précision minimale | Optimiser uniquement l'exactitude négligerait les pannes minoritaires. |
| Présenter le résultat à un technicien (évolution) | **Règles d'interface**, score et message d'alerte | Pas besoin de LLM ou de RAG pour afficher une prédiction structurée. |

**Approches non retenues à ce stade :** DL, LLM et RAG : inutilement complexes pour les quatre variables tabulaires disponibles et sans corpus documentaire à interroger.

## 4. Données

| Jeu de données | Source et licence | Volume | Données personnelles ? |
|---|---|---|---|
| `data/exemple_pannes.csv` | Fourni dans l'archive du projet ; origine exacte et licence **non précisées**. Ne pas supposer une licence ouverte. | **5 000 lignes**, **5 colonnes**, dont 4 variables explicatives et 1 cible. | **Aucune donnée personnelle directement identifiable** dans les colonnes observées. |

**Description des attributs :**

| Colonne | Type / rôle | Description |
|---|---|---|
| `temperature_c` | Numérique, entrée | Température de l'équipement en °C. |
| `vibration_mm_s` | Numérique, entrée | Vibration en mm/s. |
| `load_pct` | Numérique, entrée | Taux de charge en %. |
| `runtime_hours` | Numérique, entrée | Temps de fonctionnement en heures. |
| `failure` | Binaire, cible | `1` : panne ; `0` : absence de panne. |

**Profil constaté dans le CSV :** 4 122 observations sans panne (**82,44 %**) et 878 avec panne (**17,56 %**). Aucune valeur manquante ni ligne strictement dupliquée n'a été constatée. Les variables sont toutes numériques ; aucune date ni identifiant d'équipement n'est disponible.

**Protocole initial proposé :** séparation aléatoire **stratifiée** avec `TEST_SIZE = 0.20` et `SEED = 42`, soit **4 000 lignes d'entraînement** et **1 000 lignes de test** (dont **176 pannes**). Tous les traitements statistiques doivent être ajustés **uniquement sur les données d'entraînement** à l'intérieur d'un `Pipeline`.

**Pour un déploiement réel :** documenter la provenance, la licence, la représentativité, le protocole d'étiquetage des pannes et collecter au minimum des identifiants de machines et horodatages pour mesurer la généralisation temporelle.

## 5. Métriques, baseline et critères d'acceptation

- **Nature du problème :** classification binaire avec classe positive `failure = 1`.
- **Baseline et son score :** `DummyClassifier(strategy="most_frequent")`, entraîné sur le partage stratifié 80/20 (`random_state=42`) : **rappel = 0,000**, précision = 0,000, F1 = 0,000 et exactitude = **0,824**. Ce classifieur prédit toujours « pas de panne ».
- **Métrique principale : `recall` (rappel de la classe panne)**, car il faut limiter les pannes non signalées. Formule : `TP / (TP + FN)`.
- **Métriques complémentaires :** `precision` pour contrôler les fausses alertes, `f1` pour équilibrer précision et rappel, `accuracy` à titre indicatif ; matrice de confusion obligatoire.

### Évaluation exploratoire indépendante

Les valeurs suivantes ont été obtenues sur le CSV fourni, avec une séparation stratifiée 80/20, une graine de 42 et les prédictions de modèles scikit-learn. **Ce n'est pas le résultat de `python -m monprojet.train` puisque les fonctions du projet ne sont pas encore écrites.**

| Modèle testé | Rappel (pannes) | Précision | F1 | Exactitude |
|---|---:|---:|---:|---:|
| DummyClassifier (classe majoritaire) | 0,000 | 0,000 | 0,000 | 0,824 |
| Régression logistique (`class_weight="balanced"`) | **0,847** | **0,527** | 0,649 | 0,839 |
| Arbre de décision pondéré | 0,761 | 0,444 | 0,561 | 0,790 |
| Forêt aléatoire pondérée | 0,693 | 0,649 | 0,670 | 0,880 |
| HistGradientBoosting | 0,574 | 0,697 | 0,629 | 0,881 |

Avec la régression logistique, le test contient **149 vraies alertes**, **27 pannes manquées**, **134 fausses alertes** et **690 vraies absences de panne**. Ces résultats sont **préliminaires** et ne démontrent pas une généralisation industrielle.

**Critères d'acceptation proposés pour un prototype :**

1. Sur un jeu de test indépendant d'au moins 1 000 enregistrements, conserver un **rappel ≥ 0,80 pour la classe panne**.
2. Sur ce même test, atteindre une **précision ≥ 0,50**, pour éviter de maximiser le rappel en alertant sur toutes les observations.
3. **Surpasser la baseline** sur le rappel et enregistrer les autres métriques ainsi que la matrice de confusion.
4. Passer l'ensemble des tests du dépôt (`python -m pytest`) et produire `models/model.joblib` et `models/metrics.json`.
5. Considérer les seuils comme **provisoires** : ils doivent être approuvés avant validation finale avec des données réellement représentatives et un jeu de test non réutilisé pour ajuster les choix.

**Lecture des premiers résultats :** la régression logistique équilibrée franchit les seuils numériques proposés sur cet exemple (rappel 0,847 ; précision 0,527). Un seul découpage ne suffit toutefois pas pour arrêter un choix définitif. Un jeu de validation séparé ou une validation croisée est conseillé pour régler les hyperparamètres et le seuil de décision sans « apprendre » sur le test final.

## 6. Architecture prévue

```text
Fichier CSV des observations
            │
            ▼
Chargement et validation (monprojet/data.py)
            │
            ▼
Séparation stratifiée : 80 % entraînement / 20 % test
            │
            ▼
Prétraitement dans un Pipeline scikit-learn
(imputation médiane + standardisation des variables numériques)
            │
            ▼
Comparaison de modèles (monprojet/models.py)
DummyClassifier / LogisticRegression / DecisionTree / RandomForest / Boosting
            │
            ▼
Évaluation (monprojet/train.py)
recall, precision, f1, accuracy, matrice de confusion à ajouter
            │
            ▼
Sélection du candidat selon rappel + contrainte de précision
            │
            ▼
Export des résultats
models/model.joblib + models/metrics.json
            │
            ▼
Utilisation future : nouveau relevé → prétraitement → classe/alerte
                                        → contrôle par le technicien
```

**Organisation existante :** `monprojet/config.py` définit les paramètres ; `data.py` doit charger et découper les données ; `models.py` doit déclarer les candidats ; `train.py` contient déjà le prétraitement mais l'entraînement et l'évaluation sont à compléter ; `tests/` fournit des tests automatisés ; `docs/` rassemble les décisions de conception.

**Écart entre architecture cible et code actuel :** la logique de sélection prévue dans les commentaires du dépôt utilise seulement la métrique principale ; la contrainte de précision minimale et l'enregistrement de la matrice de confusion sont des améliorations à implémenter si retenues.

## 7. Choix technologiques

| Technologie | Utilisation | Justification |
|---|---|---|
| **Python** | Implémentation du traitement et de l'entraînement | Écosystème adapté au prototypage ML. |
| **pandas** | Lecture et contrôle du CSV | Manipulation simple des données tabulaires. |
| **NumPy** | Opérations numériques | Calculs et support des traitements. |
| **scikit-learn** | Imputation, standardisation, modèles, validation et métriques | Bibliothèque cohérente pour petits jeux de données structurées. |
| **joblib** | Sauvegarde du meilleur `Pipeline` | Réutilisation locale du modèle sans réentraîner. |
| **JSON** | Export des scores | Format léger et lisible par d'autres applications. |
| **pytest** | Tests automatisés des fonctions | Vérification du comportement attendu. |
| **Git** (recommandé) | Versionnage | Traçabilité des modifications et des expériences. |

Le prototype reste **local, sur fichier CSV**. Aucune base de données, API, application web ou plateforme cloud n'est indispensable pour satisfaire le périmètre actuel.

## 8. Risques, éthique, confidentialité

- **Risque de panne manquée :** un faux négatif peut entraîner des coûts importants ; le système ne doit pas remplacer les procédures de sécurité et d'inspection obligatoires.
- **Risque de fausses alertes :** mesurer la précision et le nombre d'inspections inutiles ; choisir le seuil de décision avec les responsables métier.
- **Déséquilibre des classes :** les pannes ne représentent que 17,56 % des données ; ne pas se fier à l'exactitude seule.
- **Fuite de données et surestimation :** appliquer les transformations après découpage et les apprendre uniquement sur l'entraînement ; surveiller de futurs doublons temporels ou plusieurs relevés de la même machine répartis entre ensembles.
- **Validité externe incertaine :** provenance, mode d'acquisition et représentativité du CSV non documentés ; éviter toute revendication de performance sur une installation réelle.
- **Confidentialité :** les colonnes actuelles ne contiennent pas de données personnelles évidentes. Dans une utilisation réelle, protéger les mesures de production, contrôler les accès et définir une durée de conservation.
- **Cybersécurité :** n'accepter des fichiers `joblib` qu'en provenance de sources fiables, car leur chargement peut exécuter du code.
- **Traçabilité :** conserver version du modèle, paramètres, date de test, métriques et procédure de validation ; laisser la décision opérationnelle au personnel autorisé.

## 9. Limites et hors périmètre

**Limites actuelles :**

- Le dépôt transmis est **un squelette non terminé** ; les principales fonctions sont des `TODO`.
- Jeu de données d'exemple de seulement 5 000 lignes, origine et licence non précisées.
- Absence de dates et d'identifiants de machines : impossibilité d'évaluer une véritable prévision temporelle ou la performance sur des équipements totalement nouveaux.
- Quatre attributs numériques uniquement ; pas d'historique de maintenance, de contexte environnemental, de coûts ni de typologie de pannes.
- Résultats exploratoires sur un seul découpage ; pas de garantie en conditions industrielles.

**Hors périmètre de la version actuelle :**

- Déploiement sur capteurs IoT ou traitement temps réel.
- Commande automatique d'équipements ou arrêt automatique d'une ligne de production.
- Prédiction de la date de la prochaine panne ou de la durée de vie restante (RUL).
- Diagnostic détaillé de la cause d'une panne, prédiction du coût ou planification complète des interventions.
- Interface web/mobile, API, système de notification, surveillance de dérive et réentraînement automatique.

**Prochaines étapes :** compléter les cinq fonctions `TODO`, lancer `pytest`, comparer les candidats dans le pipeline du projet, remplir `docs/choix-modele.md` avec les résultats reproduits, puis faire valider le protocole et les critères d'acceptation avant une expérimentation sur données réelles.
