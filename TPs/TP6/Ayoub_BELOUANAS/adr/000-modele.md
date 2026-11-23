# ADR 000 : Contenu de l’image Docker et fichiers fournis au lancement

Date : 23/11/2026 · Heure : 11:25 · Auteurs : Ayoub BELOUANAS

## Contexte
MaintAI doit pouvoir fonctionner sur une machine équipée de Docker sans qu’il soit nécessaire d’y installer manuellement Python et les bibliothèques du projet. Le modèle, les données et la clé API doivent être fournis sans les intégrer à une image Docker partageable.

## Options étudiées
1. Inclure le modèle dans l’image : l’image contient tout ce qui est nécessaire au démarrage du modèle et le déploiement est plus simple. En revanche, l’image est plus volumineuse et chaque changement du modèle impose de la reconstruire.

2. Fournir le modèle par un volume au lancement : l’image reste plus légère et le modèle peut être remplacé sans reconstruire l’image. Cette option exige que le fichier du modèle soit présent sur la machine hôte au démarrage.

Pour les données, les inclure dans l’image rendrait celle-ci plus volumineuse et nécessiterait une reconstruction à chaque mise à jour. Nous les fournissons plutôt à l’interface par un volume en lecture seule.

Pour la clé API, l’inscrire dans l’image faciliterait sa récupération par toute personne ayant accès à l’image. Nous la fournissons au conteneur API depuis le fichier .env avec env_file.

## Décision
L’image contient le code MaintAI et les dépendances épinglées dans requirements-docker.txt. Le modèle est monté depuis ./models vers /app/models, et les données depuis ./data vers /app/data, tous deux en lecture seule. La clé API est injectée au lancement par .env.

Le fichier .dockerignore exclut notamment .env, models/, data/, mlflow.db, mlruns/ et les fichiers de DVC. Il évite d’inclure dans l’image des secrets, des données, des modèles ou des artefacts de développement.

## Conséquences
L’image est plus légère et peut servir à lancer l’API et l’interface. Un nouveau modèle ou de nouvelles données peuvent être fournis sans reconstruire l’image. En contrepartie, les fichiers montés doivent être présents sur la machine qui lance Docker. Il faut aussi conserver une version de scikit-learn compatible avec le modèle sauvegardé.
