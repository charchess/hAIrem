# Template : Signature Non-Verbale (Persona)

Ce document définit les spécifications comportementales à intégrer dans la définition d'un Persona pour garantir sa cohérence visuelle via l'Atlas ACNV.

---

## 🏗️ Structure de la Signature Non-Verbale (SNV)

Chaque persona doit définir ses "réglages par défaut" selon les axes suivants :

### 1. Posture de Base (Base Stance)
Définit la silhouette habituelle de l'agent au repos.
- **BAP Trunk** : (T1 Kyphose / T2 Lordose / T3 Lean)
- **BAP Shoulders** : (S1 High / S2 Forward / S3 Back)
- **LMA Effort** : (Light / Strong / Bound / Free)

### 2. Expression Signature (Default Face)
L'expression "neutre" qui définit le caractère.
- **FACS AU** : (ex: AU6+12 léger pour un agent joyeux)
- **Gaze Style** : (G-direct / G-aversion / G-soft)

### 3. Tics Gestuels (Default Gestures)
Les mouvements réflexes ou positions de mains habituelles.
- **NEUROGES** : (ex: F-self chin contact / F-space illustrations)
- **Anthro (si applicable)** : (ex: E-back ears / T-horizontal tail)

### 4. Dynamique de Relation (Proxemics)
Comment l'agent se positionne par rapport à l'utilisateur ou aux autres.
- **Distance** : (P1 Intimate / P2 Personal)
- **Orientation** : (O-Frontal / O-Canted)

---

## 📑 Exemple : Profil SNV pour "La Renarde"

```yaml
behavioral_signature:
  base_stance:
    trunk: "T2 Lordosis (slight)"
    shoulders: "S3 Retraction (open chest)"
    effort: "Float (light, sustained, free)"
  default_face:
    aus: "AU6 + AU12 (subtle playful smirk)"
    gaze: "G-direct (intense but warm)"
  gestures:
    neuroges: "F-self hand-to-chin (contemplative)"
    anthro:
      ears: "E-back (playful)"
      tail: "T-wag (gentle swaying)"
  proxemics:
    distance: "P2 (Personal, inviting)"
    orientation: "O-Canted (collaborative/open)"
```

---

## 🛠️ Utilisation par l'Orchestrateur

Lors de la génération d'un prompt, l'Orchestrateur doit :
1. Extraire la **SNV** du persona.
2. Injecter les codes `(tag:weight)` correspondants dans le bloc de départ du prompt.
3. Superposer l'émotion contextuelle (ex: "Colère") en modifiant temporairement les AU et les codes d'effort, tout en gardant une trace de la posture de base si possible (cohérence).
