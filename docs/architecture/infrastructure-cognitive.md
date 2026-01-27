# Infrastructure Cognitive : Cache & Confidentialité

hAIrem intègre des services transverses pour optimiser les performances et garantir la sécurité des données.

## 1. Semantic Caching (Epic 9.1)
Pour réduire les coûts d'API LLM et la latence, le système utilise un cache sémantique basé sur Redis.

### Fonctionnement
1. **Interception :** Lors d'une demande d'embedding via `LlmClient`, le système calcule le hash SHA-256 du texte normalisé.
2. **Lookup :** Recherche dans Redis sous la clé `hairem:cache:emb:{hash}`.
3. **Hit/Miss :** 
    - Si présent : Retour immédiat du vecteur JSON.
    - Si absent : Appel à l'API (ex: Gemini 004), stockage du résultat avec un TTL de 7 jours.

### Impact
- Réduction drastique de la latence pour les recherches sémantiques récurrentes.
- Économie de tokens sur les modèles d'embedding.

## 2. Privacy Filter (Epic 9.2)
Le filtre de confidentialité est un utilitaire de nettoyage (scrubbing) conçu pour empêcher la fuite de secrets dans la base de données de mémoire.

### Stratégie de Nettoyage (Layers)
- **Layer 1 (Regex) :** Détection de patterns connus (API Keys Google/OpenAI, adresses IP).
- **Layer 2 (Contextuel) :** Recherche de mots-clés (`password`, `secret`) suivis de valeurs.
- **Layer 3 (Entropie de Shannon) :** Analyse de l'entropie des chaînes de caractères. Si une chaîne > 10 caractères a une entropie > 3.8, elle est considérée comme un hash ou un secret et caviardée.

### Intégration (Cible)
Le filtre doit être injecté dans le service de persistance des messages (`main.py` -> `SurrealDbClient.persist_message`). 
*Note : Audit du 26/01/2026 révèle que cette intégration est actuellement manquante dans le code live.*

---
