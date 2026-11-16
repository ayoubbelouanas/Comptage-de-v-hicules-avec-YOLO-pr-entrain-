# ADR 004 : Choix du modèle et du seuil pour MaintAI

Date : 16/11/2026 · Auteurs : LAKBAB Younes

## Contexte

MaintAI doit détecter les pannes à partir de relevés de capteurs. Une panne manquée coûte plus cher qu’une fausse alerte : le rappel est donc le critère prioritaire pour choisir le modèle et son seuil d’alerte.

## Options étudiées

| Option | Rappel | Précision |
|---|---:|---:|
| Régression logistique, réglages par défaut (seuil `0.3`) | 75,0 % | 62,2 % |
| Régression logistique, `C = 0.01`, seuil `0.3` | 69,1 % | 65,3 % |
| Régression logistique, seuil `0.2` | 83,8 % | 54,3 % |
| Forêt aléatoire, seuil `0.3` | 72,8 % | 56,2 % |
| Régression logistique, seuil `0.25` | 79,4 % | 58,1 % |

## Décision

Nous retenons la **régression logistique avec `C = 1.0` et un seuil de `0.2`**, entraînée sur la v1. Elle obtient le meilleur rappel des cinq essais réalisés sur la v1 : **83,8 %**. Le seuil `0.25` donne une meilleure précision, mais détecte une plus faible proportion des pannes réelles.

- **Identifiant du run MLflow :** `91186fe5f642416a8b985153c6398448`
- **`data_md5` :** `73e0b7cb3c6f795c70c3ddf970b99c15`

## Conséquences

Par rapport au seuil par défaut de `0.3`, le seuil `0.2` permet de détecter davantage de pannes, mais la précision baisse de 62,2 % à 54,3 %. Nous acceptons donc davantage de fausses alertes pour laisser passer moins de pannes. Il faudra surveiller le volume de fausses alertes et vérifier que le rappel reste satisfaisant sur de nouvelles données.