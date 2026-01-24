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
*   **Bus:** Redis 7.x (Pub/Sub).
*   **DB:** SurrealDB (Unified: Graph, Vector, Document).
*   **Inference:** LiteLLM (Universal Connector: Gemini, Ollama, etc.).

---

## 4. Modèles de Données & Mémoire Subjective
Mémoire Dynamique Pondérée (MDP) : Faits bruts immuables + Interprétations subjectives indexées par UUID avec érosion (Decay) et synthèse. Support natif des embeddings vectoriels dans SurrealDB.

---

## 5. Protocole H-Link
Messages JSON incluant header (msg_id, replaces_id, type, priority) et payload (content, data, metadata). Support des types `system.whisper` et `agent.internal_note`.

---

## 6. Orchestration Narrative
*   **Dieu (Entropy):** Plugin spécialisé (`agents/entropy`) injectant du chaos via des murmures (whispers).
*   **Sleep Cycle:** Processus automatique de synthèse et consolidation mémorielle.
*   **Safety Governor:** Redaction automatique des données sensibles (Privacy Filter).

---

## 7. Système Hotplug & Plugins
Structure : `expert.yaml`, `logic.py` (optionnel), `/assets/`. Chargement dynamique via `PluginLoader` supportant l'instanciation de classes personnalisées.

---

## 8. Résilience & Déploiement
Pods K8s, Stockage iSCSI/NFS, Snapshots horaires et exports S3.

---

## 9. Coding Standards
Isolation stricte (pas d'imports système), Asynchronicité obligatoire, Immuabilité des faits bruts.
