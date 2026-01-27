# 4. Modèles de Données & Mémoire Subjective

hAIrem utilise une **Mémoire Dynamique Pondérée (MDP)** basée sur un modèle de graphe dans SurrealDB. Contrairement aux approches RAG classiques qui stockent des documents plats, la MDP modélise les relations entre les agents, les faits et les sujets.

## 4.1 Architecture du Graphe

Le schéma est défini de manière `SCHEMAFULL` pour garantir l'intégrité des relations cognitives.

### Les Noeuds (Nodes)
- **`fact`** : L'unité atomique d'information. Contient le texte (`content`) et son vecteur (`embedding`).
- **`subject`** : Une entité (Utilisateur ou Agent) à laquelle un fait se rapporte.
- **`concept`** : Une catégorie abstraite pour l'organisation thématique.

### Les Relations (Edges)
- **`BELIEVES`** (`subject` → `fact`) :
    - La relation la plus critique. Elle porte la **subjectivité**.
    - Champs : `confidence` (certitude initiale), `strength` (poids actuel/persistance), `last_accessed`.
- **`ABOUT`** (`fact` → `subject`) : Lie une information à son sujet (ex: "Lisa aime le café" -> `ABOUT` Lisa).
- **`CAUSED`** (`fact` → `fact`) : Modélise la causalité ou les dépendances logiques entre les connaissances.

## 4.2 Dynamique Cognitive

### Érosion (Decay)
La mémoire simule l'oubli biologique via un algorithme de decay exponentiel.
- Chaque nuit (ou via déclencheur), la `strength` de toutes les arêtes `BELIEVES` est réduite.
- Formule : `strength = strength * math::pow(0.9, decay_rate)`.
- Si `strength < 0.1`, la relation est supprimée (L'agent a "oublié"). Le noeud `fact` reste en base tant qu'un autre agent y croit.

### Renforcement
Lorsqu'un fait est rappelé avec succès via une recherche sémantique, sa `strength` est réinitialisée à 1.0 et sa date `last_accessed` mise à jour. Cela simule l'importance des informations fréquemment utilisées.

### Synthèse de Conflits (Dialectique)
Lors de l'insertion d'un nouveau fait, le `MemoryConsolidator` vérifie les contradictions :
1. Recherche sémantique pour détecter des faits similaires (> 0.85).
2. Si conflit potentiel (ex: "Le ciel est bleu" vs "Le ciel est rouge"), le `ConflictResolver` (LLM) arbitre.
3. Résolution :
    - **OVERRIDE** : Le nouveau fait remplace l'ancien.
    - **MERGE** : Les informations sont fusionnées dans une nouvelle synthèse.

## 4.3 Récupération Subjective
La recherche ne se fait pas sur l'ensemble de la base, mais à travers le prisme de l'agent :
```surql
SELECT *, vector::similarity::cosine(embedding, $query_vector) AS score 
FROM fact 
WHERE (<-BELIEVES[WHERE in = $agent_id OR in = subject:system]).id
ORDER BY score DESC;
```
Cela permet à Lisa et Electra d'avoir des bases de connaissances divergentes tout en partageant les faits "système" (universels).

---
