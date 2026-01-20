# hAIrem Fullstack Architecture Document

**Version:** 4.2 (Final Consolidated)  
**Status:** Finalized & Verified  
**Author:** Winston (Architect)  

---

## 1. Introduction
hAIrem est un framework d'écosystème d'agents spécialisés, incarnés et inter-agentifs. Il repose sur un modèle d'**Orchestrateur Léger** (Thin Orchestrator).

---

## 2. Architecture de Haut Niveau
Le cœur (**H-Core**) en Python asynchrone utilise **Redis** pour la communication et **SurrealDB** pour une mémoire multi-modèle (Graphe/Vecteur) sous **Kubernetes**.

---

## 3. Tech Stack
*   **Backend:** Python 3.11+ (FastAPI).
*   **Bus:** Redis 7.x.
*   **DB:** SurrealDB (Hot) / MariaDB (Cold).
*   **Inference:** LiteLLM (Hybrid: Local, Remote GPU, Cloud).

---

## 4. Modèles de Données & Mémoire Subjective
Mémoire Dynamique Pondérée (MDP) : Faits bruts immuables + Interprétations subjectives indexées par UUID avec érosion (Decay) et synthèse.

---

## 5. Protocole H-Link
Messages JSON incluant header (msg_id, replaces_id, type, priority) et payload (content, data, metadata).

---

## 6. Orchestration Narrative
*   **Dieu (Entropy):** Plug-in `ENTROPY_AGENT` injectant du chaos via `whisper`.
*   **Dream (Maintenance):** Job nocturne de synthèse et nettoyage.
*   **Safety Governor:** Inhibition P0 automatique.

---

## 7. Système Hotplug & Plugins
Structure : `agent.yaml`, `logic.py`, `/assets/`. Validé par le **Gatekeeper** et isolé via l'objet **Context (ctx)**.

---

## 8. Résilience & Déploiement
Pods K8s, Stockage iSCSI/NFS, Snapshots horaires et exports S3.

---

## 9. Coding Standards
Isolation stricte (pas d'imports système), Asynchronicité obligatoire, Immuabilité des faits bruts.
