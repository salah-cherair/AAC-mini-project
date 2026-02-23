# Mini-Projet : Consensus Simplifié (Mini-Raft)

## Présentation du Projet
Ce projet implémente une version simplifiée du protocole de consensus **Raft**. L'objectif principal est de simuler un système distribué où plusieurs nœuds indépendants parviennent à un accord sur une valeur unique, même dans un environnement asynchrone présentant des délais de communication simulés.

Ce travail a été réalisé dans le cadre du module **Algorithmes Avancés et Complexité** à l'Université Ferhat Abbas - Sétif 1.



## Fonctionnalités principales

* **Élection de Leader :** Les nœuds gèrent un cycle de vie complet (Follower → Candidate → Leader) pour élire un chef via un système de vote majoritaire.
* **Réplication de Logs :** Le Leader centralise les décisions et réplique les entrées sur l'ensemble du cluster pour garantir la cohérence des données.
* **Simulation Asynchrone :** Utilisation de la bibliothèque `asyncio` pour modéliser des échanges de messages concurrents et réalistes.
* **Métriques de Performance :** Suivi précis du trafic réseau (RequestVote, AppendEntries) et calcul du temps nécessaire à la convergence du système.

## Spécifications Techniques

### Environnement
* **Langage :** Python 3.10+
* **Bibliothèques :** `asyncio` (concurrence), `matplotlib` (visualisation graphique), `collections` (structures de données).

### Paramètres de la Simulation
* **Nombre de nœuds :** 5
* **Délai d'élection :** Entre 120ms et 280ms (aléatoire pour éviter les collisions).
* **Intervalle de Heartbeat :** 50ms (pour maintenir l'autorité du Leader).



## Installation et Exécution

1. **Cloner le dépôt :**
```bash
git clone [https://github.com/salah-cherair/AAC-mini-project.git](https://github.com/salah-cherair/AAC-mini-project.git)
cd AAC-mini-project**


