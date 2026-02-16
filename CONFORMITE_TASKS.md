# 📋 Tasklist de Mise en Conformité hAIrem (V4)

Basé sur le rapport d'analyse du 16 Février 2026.

## 🚨 Priorité CRITIQUE (Sprint 1-2) - Déblocage des Piliers
- [ ] **Initialiser les Relations Sociales (Epic 13/18)** : Créer le `RelationshipBootstrapper` pour générer les arêtes `KNOWS`/`TRUSTS` au démarrage (indispensable pour le scoring UTS).
- [ ] **Compléter l'Event System Workers (Epic 10/15)** : Implémenter les workers consommant les événements Home Assistant pour activer la proactivité réelle.
- [ ] **Dynamiser le Mapping des Skills (Epic 15)** : Permettre la lecture automatique de `persona.yaml:skills[]` et le chargement dynamique des outils.
- [ ] **Sécuriser le stockage des clés API (Epic 7.5)** : Implémenter un coffre-fort (Vault) ou un chiffrement pour les clés actuellement en texte clair.

## 🔝 Priorité HAUTE (Sprint 3-4) - Complétion Vision V4
- [ ] **Automatiser la Consolidation (Epic 13)** : Activer le trigger automatique du cycle de sommeil (Sleep Cycle) par inactivité ou commande.
- [ ] **Activer le World State Management (Epic 18)** : Permettre à l'agent Entropy (Dieu) de modifier l'état mondial et déclencher les cascades de régénération (décors/tenues).
- [ ] **Mettre en place le Monitoring de Performance** : Suivre les métriques de latence (Graphe < 500ms, TTS < 800ms) via Prometheus/Grafana.
- [ ] **Réparer la Suite de Tests (Epic 20.2)** : Résoudre les 48 erreurs de collection pour stabiliser la CI/CD.

## ⚖️ Priorité MOYENNE - Optimisation & UX
- [ ] **Implémenter le Social Arbiter basé sur LLM** : Passer du scoring par règles à une micro-inférence LLM (modèle 1B).
- [ ] **Intégrer ElevenLabs** : Ajouter le support TTS haute fidélité avec switching automatique selon la latence.
- [ ] **Finaliser la Visual Bible** : Compléter le mapping FACS → poses et les attitudes YAML.
- [ ] **Gérer le cycle de vie des médias** : Implémenter un worker de nettoyage LRU pour le dossier `/media/generated`.
- [ ] **Détection du Barge-in** : Permettre l'interruption audio de l'utilisateur pour une interaction plus naturelle.
- [ ] **Routage Multi-Client** : Finaliser la visibilité des agents basée sur la localisation (Multi-room).

---
*Généré par Lisa - Régente du Domaine* 🐾⚙️👑
