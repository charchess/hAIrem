# ADR 001: Migration vers Embeddings Locaux (FastEmbed)

## Contexte
Le projet dépendait initialement des API externes (OpenAI/Google Gemini) pour la vectorisation des textes (Embeddings).
Problèmes rencontrés :
- Instabilité des API (erreurs 404, rate limits).
- Incohérence des dimensions (1536 vs 768) nécessitant des migrations de schéma complexes.
- Latence réseau.

## Décision
Adoption de la librairie **FastEmbed** intégrée directement dans le conteneur `h-core`.
- Modèle choisi : `sentence-transformers/all-MiniLM-L6-v2` (transition vers `paraphrase-multilingual-MiniLM-L12-v2` recommandée pour le support FR).
- Dimension fixée : **384**.
- Base de données : SurrealDB configuré avec `array<float, 384>`.

## Conséquences
- **Autonomie :** Plus de dépendance API pour la mémoire.
- **Performance :** Génération locale CPU très rapide.
- **Breaking Change :** Incompatible avec les anciennes bases de données (768/1536 dims). Nécessite un wipe des volumes existants lors de la migration.

## Statut
Implémenté et Validé le 29/01/2026.
