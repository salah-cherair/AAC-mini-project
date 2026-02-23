# Mini-Projet : Consensus Simplifié (Mini-Raft)

## Présentation du Projet
Ce projet implémente une version simplifiée du protocole de consensus **Raft**. L'objectif principal est de simuler un système distribué où plusieurs nœuds indépendants parviennent à un accord sur une valeur unique, même dans un environnement asynchrone présentant des délais de communication simulés.

Ce travail a été réalisé dans le cadre du module **Algorithmes Avancés et Complexité** à l'Université Ferhat Abbas - Sétif 1.



## Fonctionnalités
* **Élection de Leader :** Les nœuds passent de l'état de Follower à celui de Candidate pour élire un Leader via un vote majoritaire.
* **Réplication de Logs :** Le Leader gère un journal et réplique les entrées sur l'ensemble du cluster pour garantir la cohérence.
* **Simulation Asynchrone :** Utilisation de la bibliothèque `asyncio` pour gérer les échanges de messages concurrents entre les nœuds.
* **Métriques de Performance :** Suivi en temps réel du nombre de messages (RequestVote, AppendEntries) et de la durée des élections.

## Spécifications Techniques
* **Langage :** Python 3.10+
* **Bibliothèques Principales :** `asyncio`, `matplotlib`, `collections`.

**Configuration de la Simulation :**
* Nombre de nœuds : 5
* Délai d'élection : 120ms à 280ms
* Intervalle de battement de cœur (Heartbeat) : 50ms

## Installation et Exécution

**1. Installer les dépendances nécessaires :**
```bash
pip install matplotlib


