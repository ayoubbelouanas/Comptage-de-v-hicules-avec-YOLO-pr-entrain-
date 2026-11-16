# ADR 000 : [titre de la décision]

Date : [16/11/2026] · Auteurs : [Ayoub BELOUANAS]

## Contexte
Le projet doit prédire les pannes à partir des relevés des capteurs. Comme manquer une panne peut être coûteux, le choix du modèle doit tenir compte du rappel, tout en surveillant le nombre de fausses alertes.

## Options étudiées
1. Régression logistique avec le seuil de 0.3 : rappel de 0,750 et précision de 0,622. Ce réglage offre un compromis entre les pannes détectées et les fausses alertes.

2. Régression logistique avec un seuil de 0,2 : rappel de 0,838 et précision de 0,543. Ce réglage détecte davantage de pannes, mais génère plus de fausses alertes.

## Décision
Nous retenons la régression logistique avec un seuil de décision de 0,2, car le rappel obtenu est le plus élevé parmi les options comparées. Cette décision privilégie la détection des pannes, malgré une précision plus faible.
Run MLflow : crawling-perch-641
Identifiant du run : 2e820cd39abc4aa2ac9e1da912787f76
data_md5 : b7fec4274774842dc1f48202c6013490

## Conséquences
Ce réglage devrait réduire le nombre de pannes manquées, mais il peut entraîner davantage de fausses alertes. Il faudra surveiller ces deux effets et réévaluer le seuil si les données ou les besoins métier changent.
