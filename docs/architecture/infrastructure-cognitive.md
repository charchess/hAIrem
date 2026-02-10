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

## 2. Visual Memory & Asset Re-use (Epic 25)
Avant de lancer une génération d'image coûteuse, le `VisualImaginationService` consulte la table `visual_asset` de SurrealDB.

### Mécanisme de Réutilisation
1. **Recherche Sémantique :** Le prompt souhaité est converti en embedding.
2. **K-NN Search :** Une recherche par "plus proches voisins" est effectuée dans la base d'assets existants.
3. **Seuil de Similitude :** Si un asset existant a une similarité > 0.92 avec le nouveau prompt, l'URL de l'ancien asset est renvoyée au lieu de générer une nouvelle image.
4. **LRU Cleanup :** Le Garbage Collector s'assure que seuls les assets les plus pertinents ou récents sont conservés sur disque.

## 3. Social Arbiter & Stimuli Hierarchy (Epic 18)
Pour gérer la polyphonie et éviter la saturation cognitive, le système utilise un **Social Arbiter** couplé à une hiérarchie stricte des flux d'information.

### Niveaux d'Urgence des Stimuli
1. **Niveau 0 (CRITICAL) :** Alertes de sécurité, urgences domotiques (ex: détection incendie via HA). Priorité absolue, coupe toute discussion en cours.
2. **Niveau 1 (NARRATIVE) :** Discussion active avec l'utilisateur. Priorité haute.
3. **Niveau 2 (WHISPER) :** Stimuli internes injectés par Dieu (Entropy). Intégrés organiquement par l'agent si le contexte le permet.
4. **Niveau 3 (BACKGROUND) :** Bruit de fond, mises à jour mineures de status.

### Rôle du Social Arbiter
Le Social Arbiter (micro-LLM local) analyse les stimuli entrants et décide :
- Quel agent est le plus pertinent pour répondre (Scoring d'intérêt).
- Si un stimulus de niveau inférieur doit être "muté" ou différé.
- L'ordre de parole en cas d'interventions multiples.

## 4. Privacy Filter (Epic 9.2)
Le filtre de confidentialité est un utilitaire de nettoyage (scrubbing) conçu pour empêcher la fuite de secrets dans la base de données de mémoire.

### Stratégie de Nettoyage (Layers)
- **Layer 1 (Regex) :** Détection de patterns connus (API Keys Google/OpenAI, adresses IP).
- **Layer 2 (Contextuel) :** Recherche de mots-clés (`password`, `secret`) suivis de valeurs.
- **Layer 3 (Entropie de Shannon) :** Analyse de l'entropie des chaînes de caractères. Si une chaîne > 10 caractères a une entropie > 3.8, elle est considérée comme un hash ou un secret et caviardée.

### Intégration (Cible)
Le filtre doit être injecté dans le service de persistance des messages (`main.py` -> `SurrealDbClient.persist_message`). 
*Note : Audit du 26/01/2026 révèle que cette intégration est actuellement manquante dans le code live.*

---
