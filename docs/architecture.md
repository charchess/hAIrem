**Version:** 4.4 (Final Consolidated)  
**Status:** Finalized & Verified  
**Author:** Winston (Architect)  

---

## 1. Introduction
hAIrem est un framework d'écosystème d'agents spécialisés, incarnés et inter-agentifs, reposant sur un modèle d'**Orchestrateur Léger** (Thin Orchestrator).

---

## 2. Architecture de Haut Niveau
Le cœur (**H-Core**) en Python asynchrone utilise **Redis** pour la communication et **SurrealDB** pour une mémoire multi-modèle (Graphe/Vecteur) sous **Kubernetes**.

---

## 3. Tech Stack
*   **Backend:** Python 3.11+ (FastAPI).
*   **Bus:** Redis 7.x (Pub/Sub).
*   **DB:** SurrealDB (Unified: Graph, Vector, Document).
*   **Inference:** LiteLLM (Universal Connector) + Social Arbiter (Micro-LLM local).
*   **Imaging:** NanoBanana/ComfyUI + rembg (La Découpeuse).

---

## 4. Modèles de Données & Mémoire Subjective
Mémoire Dynamique Pondérée (MDP) : Faits bruts immuables + Interprétations subjectives.
*   **Burning Memory :** Registre d'état visuel immédiat (tenue/lieu) injecté dans le contexte court terme pour la réactivité aux interactions.

---

## 5. Protocole H-Link & Skills
*   **H-Link :** Support des types `system.whisper`, `agent.internal_note`, et `visual.asset`.
*   **Architecture Persona-Skill :** Découplage total entre l'identité (Persona) et les capacités techniques (Skills pluggables) via `persona.yaml`.

---

## 6. Orchestration & Stimuli
*   **Entropy (Dieu) :** Injecteur de stimuli (idées parasites) via un timer RNG.
*   **Hiérarchie des Stimuli :** Priorisation des flux (0: Critique HA > 1: Narratif > 2: Whisper > 3: Background).
*   **Social Arbiter :** Arbitrage de la polyphonie et scoring d'intérêt en temps réel.

---

## 7. Système Hotplug & Personas
Structure : `persona.yaml` (source de vérité pour l'identité et les skills), `logic.py`, `/assets/`.

---

## 8. Résilience & Vaults
*   **Character Vault :** Character sheets de référence et garde-robe (Named Assets).
*   **Background Vault :** Décors de référence pour variations saisonnières/temporelles cohérentes.

## 9. Behavioral Layer (Communication Non-Verbale)
Couche de contrôle comportementale assurant la cohérence visuelle et narrative des agents.
*   **Atlas ACNV :** Système de codage unifié (FACS, BAP, LMA, NEUROGES, Proxémique). 
    *   *Référence :* `docs/references/non-verbal-communication-atlas.md`
    *   *Config :* `config/visual/acnv-atlas.yaml`
*   **Signature Non-Verbale (SNV) :** Profil comportemental propre à chaque agent. 
    *   *Template :* `docs/references/persona-behavioral-template.md`
*   **Prompt Grammar :** Protocole de chaînage hiérarchique.
    *   *Recettes :* `docs/references/prompt-templates.md`

## 10. Deep Presence & Visual Imagination (Epic 25)
- **Bibles Visuelles Modulaires :** Styles, poses (FACS) et attitudes (Mehrabian).
- **La Découpeuse :** Pipeline `rembg` pour le détourage automatique.
- **Observabilité :** Broadcast des `RAW_PROMPT` vers l'UI.
