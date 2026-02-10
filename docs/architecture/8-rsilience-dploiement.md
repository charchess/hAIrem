# 8. Résilience & Déploiement

hAIrem repose sur une architecture conteneurisée légère utilisant **Docker-Compose**, privilégiant la réactivité et la simplicité de déploiement sur des machines hôtes disposant de capacités d'inférence (GPU/NPU).

## 8.1 Topologie des Services

Le système est décomposé en services spécialisés isolés dans un réseau virtuel Docker (`hairem-net`) :

- **redis** : Bus de communication central (Pub/Sub) pour tous les services.
- **surrealdb** : Base de données multi-modèle persistante.
- **h-core** : Cerveau narratif et orchestrateur des stimuli.
- **h-bridge** : Pont E/S gérant les WebSockets (UI), l'authentification et le service de fichiers statiques.

## 8.2 Persistance & Volumes

La résilience des données est assurée par le montage de volumes hôtes, permettant au système de conserver sa mémoire après un redémarrage ou une mise à jour :

- `./surreal_data` : Stockage physique des graphes et vecteurs de SurrealDB.
- `/media/generated` : Volume partagé entre le Core et le Bridge pour les images générées par "La Découpeuse".
- `./agents` : Montage en lecture/écriture pour permettre le hotplug d'agents et la mise à jour des bibles visuelles.

## 8.3 Communication Inter-Service

Tous les services communiquent via le nom d'hôte Docker (ex: `ws://surrealdb:8000`).
- **Healthchecks** : Le Core et le Bridge utilisent des clauses `depends_on` avec `service_healthy` pour s'assurer que Redis et SurrealDB sont prêts avant de démarrer, évitant les échecs de connexion au boot.

## 8.4 Stratégie de Mise à Jour (CI/CD)

Bien que le déploiement soit local, la qualité est maintenue par un pipeline de validation :
1. **Secret Scanning** : Gitleaks sur le dépôt.
2. **Tests Unitaires & Régression** : `pytest` et `master_regression_v3.py`.
3. **Rebuild & Restart** : `docker-compose up --build -d`.

---
*Spécifié par Winston (Architect) le 28 Janvier 2026.*
