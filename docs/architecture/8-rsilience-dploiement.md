# 8. Résilience & Déploiement

Pour supporter la complexité de la V3, hAIrem doit passer d'un monolithe FastAPI à une architecture de micro-services découplés par le bus Redis.

## 8.1 Découplage du HLinkBridge
La stratégie de refactoring consiste à extraire la gestion des WebSockets dans un service dédié : le **HLinkBridge**.

### Étapes de Migration
1. **Extraction de l'A2UI** : Déplacer `apps/a2ui` vers `apps/h-bridge/static`.
2. **Création du Bridge** : Développer `apps/h-bridge/src/main.py` (FastAPI pur).
3. **Purification du Core** : Supprimer FastAPI/Uvicorn de `apps/h-core`. Remplacer la boucle principale par une boucle asyncio infinie.
4. **Middleware de Confidentialité** : Migrer le `PrivacyFilter` dans un middleware Redis partagé ou l'injecter dans le Core comme un service de filtrage global.

### Avantages
- **Résilience** : Un crash du H-Core ne déconnecte plus l'interface utilisateur.
- **Scalabilité** : On peut déployer plusieurs instances du Bridge.

## 8.3 Stratégie CI/CD (Automatisation)

L'automatisation est le dernier rempart pour garantir la stabilité de hAIrem V3.

### Pipeline de Continuité
Tout changement de code doit franchir les étapes suivantes avant d'être éligible au déploiement :
1. **Secret Scanning** : Utilisation de Gitleaks pour empêcher toute fuite de clé API dans le dépôt.
2. **Validation Statique** : Analyse de type (Mypy) et linting.
3. **Tests de Régression** : Exécution de la suite `pytest` intégrale (47+ tests).
4. **Validation E2E** : Exécution du `scripts/master_regression_v3.py`.
5. **Build Integrity** : Construction des images Docker.

### Déploiement Continu (CD) & Kubernetes
Le système est conçu pour être "K8s-Ready". 
- Les services (Bridge/Core) sont découplés et scalables horizontalement.
- Le déploiement futur pourra migrer vers une orchestration Kubernetes via Helm charts pour une résilience de niveau industriel.

---
*Spécifié par Winston (Architect) le 26 Janvier 2026.*
