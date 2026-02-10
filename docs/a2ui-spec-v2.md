# hAIrem A2UI Specification v2.0: "The Living Stage"

**Status:** Active Design Document  
**Author:** Sally (UX Expert)  
**Date:** 08 Février 2026  

---

## 1. Vision UX: "Cyber-Cozy Presence"
L'interface hAIrem doit cesser d'être un simple tableau de bord technique pour devenir une fenêtre sur une entité vivante. L'esthétique évolue du "Cyber-Néon" froid vers le **"Cyber-Cozy High-Fi"** : une alliance de technologie de pointe (glassmorphism, data-visualisation précise) et de chaleur organique (textures douces, éclairage volumétrique, profondeur).

### Principes Clés :
- **Tactile High-Fi :** Les éléments d'interface doivent avoir du "poids" et de la profondeur (soft shadows, glassmorphism à 15px de flou).
- **Spatialité Cognitive :** L'UI reflète où se trouve l'utilisateur et ce que l'agent "pense" (visualisation de la mémoire).
- **Polyphonie Ordonnée :** Gestion fluide de plusieurs agents sur scène sans chaos visuel.

---

## 2. The Stage (Mise à Jour)

### Calques Dynamiques (Z-Index)
- **Z-0 (Background) :** Profondeur infinie. Le fond se floute (blur 5px) quand un agent réfléchit (`thinking`).
- **Z-10 (Agents) :** Présence physique. Utilisation du Rim Lighting CSS pour faire ressortir le "High-Fi" des illustrations.
- **Z-30 (Dialogue) :** Bulle "Obsidian Soft". Finition mate, texte en streaming (Typewriter) avec un curseur lumineux.

---

## 3. Nouveau Composant : "Agent Deep Dive" (Story 17.5)

L'expérience **"Dossier Confidentiel"** est accessible via le bouton "Détails" sur chaque carte d'agent.

### Structure de la Vue Détaillée :
1.  **Header Lore :** Nom complet, Rôle, et DNA Visuel résumé.
2.  **Belief Graph (Memory) :** 
    - Liste des faits sémantiques stockés en SurrealDB.
    - **Visualisation de la Force :** Une jauge "Pulse" (0.0 à 1.0). Un fait à 1.0 brille intensément ; un fait à 0.3 est délavé et presque transparent (proche de l'oubli).
3.  **Vocal DNA :** Indicateur du provider (Piper/ElevenLabs) et waveform de démonstration.
4.  **Technical Vitals :** Token count total, position actuelle (Room), et humeur (Mood).

---

## 4. Visualisation de la Conscience Spatiale (Story 15.4)
- **Room Badge :** Un petit indicateur dans le `view-nav` montre la pièce active (ex: "📍 Salon").
- **Localisation des outils :** Quand un agent manipule un objet domotique, une icône de pièce apparaît brièvement sur le dialogue (ex: "J'allume la lumière [Icon: Salon]").

---

## 5. Gestion de la Polyphonie (Story 18.1)
- **Active Speaker Focus :** L'agent qui parle avance légèrement (scale 1.05) et devient plus net. Les autres reculent et subissent un léger grayscale (20%).
- **Arbitration Glow :** Un halo de couleur (Diva=Purple, Renarde=Orange) entoure l'agent sélectionné par l'arbitre social avant même qu'il ne commence à parler.

---

## 6. Guide de Style (Couleurs & Typo)
- **Font Principale :** `Inter` pour la lisibilité technique.
- **Font Narrative :** `Spectral` (Serif) pour les dialogues, apportant le côté "Cozy/Livre".
- **Couleurs :** 
    - Base : `#0a0a0a` (Obsidian)
    - Accents : Selon l'agent (ex: `#ff00cc` pour Diva, `#00ffcc` pour Electra).

---

## 7. Next Step: AI Frontend Generation Prompt
Pour générer les nouveaux composants (Vue Détaillée), utilisez le prompt optimisé :
`"Modern glassmorphic dashboard modal for a sci-fi character, obsidian theme with neon accents, includes belief strength meters with pulsing animations, detailed typography using Inter and Spectral fonts, tactile UI elements."`