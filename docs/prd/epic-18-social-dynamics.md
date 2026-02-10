# Epic 18: Social Dynamics & Social Arbiter

**Version:** 2.0
**Status:** To Do
**Theme:** Interaction Sociale Émergente & Arbitrage
**PRD Version:** V4

---

## 1. Vision
Transformer hAIrem d'un modèle "Question/Réponse" en un "Équipage Vivant". Cette Epic introduit le **Social Arbiter** pour gérer la polyphonie et le cycle de vie social des agents.

## 2. Objectifs Métier
- **Conscience Collective :** Les agents connaissent l'existence de leurs pairs et peuvent interagir entre eux.
- **Onboarding Relationnel :** Session initiale d'entretien d'embauche pour définir les affinités (`TRUSTS`, `KNOWS`).
- **Arbitrage des Flux :** Gestion intelligente des priorités entre les alertes domotiques, les discussions et les stimuli subconscients.

## 3. Requirements

### 3.1 Functional Requirements (FR)
...
- **FR18.6 (World State Management) :** Dieu (Entropy) peut modifier l'état global du monde (`theme: christmas`, `weather: snow`), déclenchant des réactions en cascade dans tous les services.
- **FR18.7 (Telepathic Cognition) :** Les agents entendent et peuvent répondre à tous les messages du bus Redis, même s'ils ne sont pas présents visuellement sur le client local de l'utilisateur.
- **FR18.8 (Thematic Costume Trigger) :** En cas de changement de thème mondial, les agents sont incités (via Whisper) à changer de tenue pour correspondre à l'ambiance (ex: bonnet de Noël).

### 3.2 Non-Functional Requirements (NFR)
- **NFR18.1 (Latency) :** L'arbitrage social doit s'exécuter en moins de 500ms (utilisation de micro-LLM local).
- **NFR18.2 (Saturation) :** Limiter à 5 interventions d'agents par tour utilisateur pour éviter la saturation cognitive.

---
*Mis à jour par John (PM) le 28 Janvier 2026.*