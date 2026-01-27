# Epic 18: Social Dynamics & Polyphony (L'Équipage)

**Status:** In Definition
**Theme:** Interaction Sociale Émergente
**PRD Version:** V3

## 1. Vision
Passer d'un modèle "Question/Réponse" à un modèle "Conseil d'Experts". L'utilisateur ne parle plus à une IA, mais interagit avec un équipage vivant où les membres peuvent s'interpeller, se contredire ou s'entraider pour répondre à un besoin complexe.

## 2. Objectifs Métier (UX)
- **Richesse Narrative :** Créer une illusion de vie via des interactions spontanées entre agents.
- **Expertise Collaborative :** Un message utilisateur peut être traité par plusieurs agents spécialisés (ex: Jardinier + Domotique + Budget).
- **Engagement :** Transformer l'attente de l'inférence LLM en un moment de divertissement (voir les agents "débattre" en coulisses).

## 3. Règles de Savoir-Vivre (Social Etiquette)
Pour éviter le chaos, le système suit ces principes :
- **Respect de l'Autorité :** L'utilisateur a toujours la priorité. Si l'utilisateur parle, tous les agents s'interrompent immédiatement.
- **Pertinence (Urge) :** Un agent ne parle que s'il a une valeur ajoutée réelle (> 0.75 de score d'intérêt).
- **Courtoisie Technique :** Un agent ne coupe pas un collègue qui est en train de générer un message (gestion séquentielle).
- **Clôture :** Lisa (ou l'agent principal) doit toujours résumer ou clore une discussion si elle s'éternise.

## 4. Expérience Utilisateur (UX)
- **Focus Visuel :** L'A2UI doit mettre en avant l'agent qui parle (opacité, animation).
- **Réactions Passives :** Un agent peut réagir visuellement (pose) à ce qu'un autre dit sans forcément prendre la parole.
- **Budget de Parole :** Maximum 5 interventions d'agents par tour de parole utilisateur pour éviter la saturation cognitive.

---
*Défini par John (PM) le 26 Janvier 2026.*
