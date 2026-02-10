# 7. Système Hotplug & Plugins

Le système hAIrem est conçu pour être extensible sans redémarrage du Core. Chaque agent est traité comme un "Plugin" autonome.

## 7.1 Structure d'un Agent (Agent Bundle)
Un agent réside dans son propre sous-répertoire de `agents/` et doit respecter la structure standard définie dans l'ADR-0009 :
- `manifest.yaml` (Obligatoire) : Configuration technique et métadonnées.
- `persona.yaml` (Optionnel) : Instructions narratives et personnalité.
- `logic.py` (Optionnel) : Code Python personnalisé pour étendre `BaseAgent`.

## 7.2 Le PluginLoader
Le `PluginLoader` surveille le répertoire `agents/` en temps réel (via `watchdog`).
1. **Détection :** À la détection d'un `manifest.yaml`, un cycle de chargement est lancé.
2. **Chargement Dynamique :** Utilisation de `importlib` pour charger la classe `Agent` du fichier `logic.py`.
3. **Contrainte de Classe :** La classe chargée **doit** s'appeler `Agent` et hériter de `BaseAgent`.
4. **Instanciation :** L'agent est instancié avec ses dépendances (Redis, LLM, SurrealDB).
5. **Remplacement à chaud :** Si un agent du même nom existe déjà, il est stoppé proprement (`agent.stop()`) avant d'être remplacé dans l'**AgentRegistry**.

## 7.3 AgentRegistry
Le registre central (`AgentRegistry`) maintient l'état "Live" de tous les agents chargés. Il est exposé via l'API `/api/agents` pour permettre à l'A2UI d'afficher dynamiquement les membres de l'équipage.

## 7.4 Isolation
Chaque agent dispose de son propre `AgentContext` (historique local, état interne) garantissant qu'une défaillance d'un plugin n'impacte pas la stabilité des autres.

---

L'architecture hAIrem repose sur le paradigme **AAA (Agent-as-an-App)**. Le Core est agnostique vis-à-vis des fonctionnalités métiers des agents.

## 7.1 Autonomie des Drivers
Contrairement à la V1, aucun driver technique (Home Assistant, Spotify, Zigbee) ne doit résider dans le Core (`src/infrastructure/`).
- Chaque agent **porte son propre driver** dans son dossier racine.
- L'agent est responsable de l'initialisation et de la configuration de son driver via son `expert.yaml`.

## 7.2 Structure d'un Package Agent
```text
agents/{agent_name}/
├── expert.yaml       # Configuration & Metadata
├── logic.py          # Logique métier (Classe Agent)
├── requirements.txt  # Dépendances spécifiques
└── [lib/drivers]     # Drivers et librairies privées
```

## 7.3 Cycle de Vie & Task Nursery
Pour permettre la proactivité (réaction à des événements externes sans intervention utilisateur), le Core expose une **Task Nursery**.

- **Méthode `setup()`** : Appelée une seule fois au chargement. C'est ici que l'agent doit enregistrer ses outils et lancer ses boucles de surveillance.
- **Méthode `spawn_task(coroutine)`** : Permet à l'agent de confier une tâche asynchrone au Core. Le Core assure le monitoring et l'arrêt propre de la tâche si l'agent est déchargé.

## 7.4 Gestion des Dépendances
Le `PluginLoader` doit isoler les environnements. 
- *Évolution future* : Utilisation de `venv` ou de containers sidecars pour éviter les conflits de librairies entre agents.

## 7.5 Flux Proactif (Exemple Electra)

1. `Electra.setup()` lance une boucle WebSocket vers Home Assistant via `spawn_task`.

2. Le driver HA détecte un événement `motion_detected`.

3. Electra capture l'événement dans sa boucle, demande au LLM une analyse ("L'utilisateur rentre, que dire ?").

4. Electra publie un `narrative.text` sur le bus Redis.

5. L'A2UI affiche la réaction d'Electra spontanément.



## 7.6 Arrêt Propre (Graceful Shutdown)

Chaque agent est responsable du nettoyage de ses ressources.

- **Tâches** : Toutes les coroutines lancées via `spawn_task` doivent être annulées par le Core lors du déchargement de l'agent.

- **Méthode `teardown()`** : Hook optionnel permettant à l'agent de fermer ses connexions (sockets, fichiers) proprement.



## 7.7 Gestion des Secrets

Les agents ne doivent pas partager leurs clés API.

- Les secrets spécifiques à un agent doivent être injectés via son fichier `expert.yaml` (sous une clé `config` ou `secrets`) ou via des variables d'environnement préfixées par le nom de l'agent (ex: `ELECTRA_HA_TOKEN`).
