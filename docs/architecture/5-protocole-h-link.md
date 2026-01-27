# 5. Protocole H-Link (Spécification v1.0)

Le protocole H-Link est le langage commun de l'écosystème hAIrem. Il définit comment les messages circulent de manière asynchrone sur le bus Redis.

## 5.1 Enveloppe de Message (JSON Schema)

Tous les messages DOIVENT respecter cette structure :

```json
{
  "id": "uuid-v4",
  "timestamp": "ISO-8601-UTC",
  "type": "enum",
  "sender": {
    "agent_id": "string",
    "role": "string"
  },
  "recipient": {
    "target": "broadcast|agent_id",
    "room": "optional_string"
  },
  "payload": {
    "content": "any",
    "format": "text|json|markdown",
    "emotion": "neutral|happy|pensive|etc"
  },
  "metadata": {
    "priority": "normal|high|system",
    "correlation_id": "uuid-v4",
    "ttl": 5
  }
}
```

## 5.2 Types de Messages (`type`)

| Type | Description | Exemple de Payload |
| :--- | :--- | :--- |
| `narrative.text` | Message parlé complet. | `{"content": "Bonjour Lisa !", "emotion": "happy"}` |
| `narrative.chunk` | Fragment de texte en streaming. | `{"content": "Bonj", "is_final": false}` |
| `narrative.action` | Action narrative (VN). | `{"content": "La Renarde sourit doucement."}` |
| `expert.command` | Commande technique. | `{"content": {"service": "light.turn_on", "entity": "living_room"}}` |
| `expert.response` | Résultat d'une commande. | `{"content": {"status": "success"}}` |
| `system.status_update` | Mise à jour d'état système (ex: activation agent). | `{"content": {"agent_id": "lisa", "active": false}}` |
| `system.log` | Log technique interne. | `{"content": "Agent loaded: expert-domotique"}` |

## 5.3 Diagrammes de Séquence

### Scénario A : Interaction Simple (User -> Renarde)
L'utilisateur salue le système via l'A2UI.

```mermaid
sequence_diagram
    participant User
    participant A2UI
    participant Redis
    participant Renarde

    User->>A2UI: "Bonjour"
    A2UI->>Redis: Publish [type: narrative.text, sender: user, payload: "Bonjour"]
    Redis->>Renarde: Deliver message
    Note over Renarde: Analyse du prompt + Inférence
    Renarde->>Redis: Publish [type: narrative.text, sender: renarde, payload: "Enchantée !"]
    Redis->>A2UI: Deliver response
    A2UI->>User: Affiche texte + Pose "Happy"
```

### Scénario B : Délégation technique (User -> Renarde -> Expert)
L'utilisateur demande d'allumer la lumière.

```mermaid
sequence_diagram
    participant User
    participant A2UI
    participant Redis
    participant Renarde
    participant ExpertDomotique
    participant HomeAssistant

    User->>A2UI: "Allume le salon"
    A2UI->>Redis: Publish [type: narrative.text, sender: user, content: "Allume le salon"]
    Redis->>Renarde: Deliver
    Note over Renarde: Identifie besoin technique
    Renarde->>Redis: Publish [type: expert.command, target: expert-domotique, content: "turn_on_living_room"]
    Redis->>ExpertDomotique: Deliver
    ExpertDomotique->>HomeAssistant: API Call (light.turn_on)
    HomeAssistant-->>ExpertDomotique: Success
    ExpertDomotique->>Redis: Publish [type: expert.response, content: "done"]
    Redis->>Renarde: Deliver
    Renarde->>Redis: Publish [type: narrative.text, content: "C'est fait, le salon est éclairé !"]
    Redis->>A2UI: Deliver
    A2UI->>User: Feedback visuel
```

## 5.4 Gestion des Erreurs
- **Message malformé :** Tout message ne passant pas la validation Pydantic est rejeté par le H-Core et loggué en `system.log` avec un niveau `ERROR`.
- **Timeout :** Si un expert ne répond pas à une `expert.command` sous 10 secondes, la Coordinatrice doit informer l'utilisateur d'un problème technique.