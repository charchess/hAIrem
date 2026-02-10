# Epic 25: Visual Imagination (NanoBanana/ComfyUI)

**Version:** 1.2
**Status:** Approved ✅
**Theme:** Pillar 2 - Deep Presence & Proactive Imagination
**PRD Version:** V4

---

## 1. Vision & Goals

**Vision:** Transformer hAIrem d'un système textuel en une entité capable de "voir" et de "montrer". L'imagination visuelle permet aux agents de matérialiser leurs pensées, d'illustrer leurs récits et d'adapter leur environnement de manière proactive, avec une précision scientifique, une modularité totale et une conscience de leur propre état physique.

**Objectifs (Goals):**
- **Deep Presence:** Donner aux agents la capacité de générer des images pour enrichir l'immersion.
- **Modularité Totale:** Découpler les styles, poses et attitudes via des bibles YAML.
- **Consistance Visuelle & Identité :** Garantir la ressemblance via des bibles de personas (`persona.yaml`), des images de référence et un système de Vaults (Garde-robe/Décors).
- **Mémoire Brûlante :** Permettre aux agents d'accéder à leur état visuel actuel (tenue, lieu) pour réagir aux interactions.

---

## 2. Requirements

### 2.1 Functional Requirements (FR)
- **FR25.1 (Generic Provider):** Interface `GenericVisualProvider` pour abstraire les APIs de génération.
- **FR25.2 (NanoBanana Client):** Client asynchrone pour NanoBanana/ComfyUI.
- **FR25.3 (Asset Manager):** Indexation sémantique (K-NN search) dans SurrealDB pour la réutilisation des assets.
- **FR25.4 (A Priori Orchestration):** Cycle "Dreamer" générant des assets selon le contexte HA.
- **FR25.5 (Character Consistency):** Support des Character Sheets et du Persona Vault.
- **FR25.6 (Modular Visual Bible):** Utilisation de `config/visual/` pour les styles, poses (FACS) et attitudes (Mehrabian).
- **FR25.7 (Automatic Background Removal):** Intégration de `rembg` (La Découpeuse) pour les assets de type `pose`.
- **FR25.8 (Observability):** Broadcast des `RAW_PROMPT` vers l'UI pour audit technique.
- **FR25.9 (Outfit System):** Changement de tenue dynamique via la commande `/outfit`.
- **FR25.10 (Bootstrap Avatar):** Génération automatique de l'image de référence si absente.
- **FR25.11 (Vaults System):** Gestion d'un inventaire nommé de tenues et de décors de référence pour une réutilisation 100% fidèle.
- **FR25.12 (Burning Memory):** Injection de l'état visuel actuel (url_asset, tags_tenue, tags_lieu) dans le contexte court terme de l'agent.

### 2.2 Non-Functional Requirements (NFR)
- **NFR25.1 (Async Operations):** Toutes les interactions APIs non-bloquantes.
- **NFR25.2 (Resilience):** Fallback sur les assets locaux ou images par défaut.
- **NFR25.3 (Resource Management):** Nettoyage LRU du volume `/media/generated`.
- **NFR25.4 (Auditability):** Transparence totale des prompts envoyés aux moteurs.

---

## 5. Epic & Story Structure

### Epic 25: Visual Imagination

**Story 25.1: Moteur Modulaire & Bibles Visuelles**
- **AC:** Support de NanoBanana, bibles YAML (FACS/Mehrabian) fonctionnelles, client rembg intégré.

**Story 25.2: Persona Vault & Asset Indexing**
- **AC:** `persona.yaml` par agent, indexation SurrealDB avec recherche sémantique.

**Story 25.3: Orchestration Proactive & Dreamer**
- **AC:** Trigger nocturne HA, cache matinal prêt.

**Story 25.4: Système d'Outfits & Bootstrap**
- **AC:** Commande `/outfit` fonctionnelle, génération auto de character sheet.

