# Recettes de Prompts ACNV (Standard hAIrem)

Ce document propose des templates et des exemples de "chaînage" utilisant l'Atlas de la Communication Non-Verbale (ACNV) pour garantir des résultats constants et expressifs.

---

## 🏗️ Structure Standard du Prompt (Grammar v2.0)

`[Sujet], [Posture BAP/LMA], [Expression FACS/Regard], [Interaction NEUROGES/Anthro/Haptique], [Physique Fur/Skin/Cloth], [Lighting/Style]`

---

## 🧪 Recettes Prêtes à l'Emploi

### 1. L'Interrogation Malicieuse (Signature Renarde)
*Usage : Quand l'agent cherche à taquiner ou à comprendre un secret.*
- **Posture** : `(H1 head tilt:1.2), (T3 lateral lean:1.1), (light weight effort:1.1)`
- **Visage** : `(AU6 cheek raiser:1.1), (AU12 lip corner puller:1.2), (G-direct eye contact:1.2)`
- **Anthro** : `(E-back ears:1.2), (T-wag tail:1.1)`
- **Final** : `Renarde, H1 head tilt, T3 lateral lean, light weight effort, AU6 cheek raiser, AU12 lip corner puller, G-direct intense gaze, E-back ears, T-wag tail, soft cinematic lighting.`

### 2. Le Stress Technique / Concentration (Signature Electra)
*Usage : En cas de bug système ou de tâche complexe.*
- **Posture** : `(T2 lordosis:1.2), (S1 shoulder elevation:1.1), (press effort:1.2)`
- **Visage** : `(AU4 brow lowerer:1.3), (AU7 lid tightener:1.2), (AU23 lip tightener:1.1)`
- **Geste** : `(F-self hand-to-neck:1.1), (E-clench fists:1.2)`
- **Final** : `Electra, T2 lordosis, S1 shoulder elevation, press effort, AU4 brow lowerer, AU7 lid tightener, AU23 lip tightener, F-self hand-to-neck contact, E-clench fists, blue futuristic lighting.`

### 3. La Vulnérabilité / Tristesse
*Usage : En cas de déception ou de solitude.*
- **Posture** : `(T1 trunk kyphosis:1.3), (H2 head pitch flexion:1.2), (heavy weight effort:1.2)`
- **Visage** : `(AU1 inner brow raiser:1.4), (AU15 lip corner depressor:1.3), (G-aversion looking down:1.2)`
- **Anthro** : `(E-flat ears:1.3), (T-tucked tail:1.4)`
- **Final** : `[Agent], T1 trunk kyphosis, H2 head pitch flexion, heavy weight effort, AU1 inner brow raiser, AU15 lip corner depressor, G-aversion gaze, E-flat ears, T-tucked tail, low-key lighting.`

### 4. La Dominance / Autorité
*Usage : Pour affirmer une position de leader ou de contrôle.*
- **Posture** : `(T2 trunk lordosis:1.4), (S3 shoulder retraction:1.2), (strong weight:1.2)`
- **Visage** : `(AU2 outer brow raiser:1.1), (G-direct piercing eye contact:1.3)`
- **Anthro** : `(E-erect ears:1.3), (T-high tail:1.2)`
- **Final** : `[Agent], T2 trunk lordosis, S3 shoulder retraction, strong weight effort, AU2 outer brow raiser, G-direct piercing eye contact, E-erect ears, T-high tail, L-rim lighting.`

---

## 🛠️ Conseils de Mixage

1. **Intensité** : Utilisez les poids `(tag:weight)` entre `1.1` et `1.4`. Ne dépassez pas `1.5` sous peine de déformer l'anatomie.
2. **Cohérence** : Si vous utilisez `T1 (Kyphose)`, évitez de mettre `T-high (Queue haute)`, cela crée un conflit d'intention que l'IA gère mal.
3. **Ordre** : Toujours placer la posture (`T1/T2`) avant l'expression faciale (`AU`). L'IA "construit" le personnage de la structure vers le détail.
