# 13. Modular Visual Bible and Self-Contained Personas

## Status
Accepted - January 28, 2026

## Context
Story 25.1 initially aimed for a centralized visual imagination service. However, during implementation, we identified a need for higher modularity to allow users to modify styles, poses, and attitudes without touching the core code. Additionally, to support a "pluggable" agent architecture, agent identities (descriptions and reference images) needed to be moved out of the core service.

## Decision
1.  **Modular Configuration**: Create a `config/visual/` directory with separate YAML files for:
    *   `STYLE_GLOBAL.yaml`: Overall art direction and engine quality tokens.
    *   `POSES.yaml`: Scientific (FACS-based) facial expression descriptions.
    *   `ATTITUDES.yaml`: Kinesics-based (Mehrabian/Birdwhistell) body orientation.
2.  **Self-Contained Personas**: Each agent now manages its own `persona.yaml` within its specific folder (`agents/[name]/persona.yaml`). This file defines the character's description and its list of reference sheets.
3.  **Automatic Post-Processing**: The "la découpeuse" (background removal) is integrated into the core service via the `rembg` library, triggered automatically for assets of type `pose`.
4.  **Logging Transparency**: Implementation of `RAW_PROMPT` and `RAW_IMAGE_PROMPT` logs broadcasted directly to the UI for full auditability of what is sent to LLM/Image providers.

## Consequences
*   **Modularity**: Adding a new agent or a new emotion no longer requires code changes.
*   **Resource Requirements**: The `h-core` container is now heavier due to `rembg` and `onnxruntime` dependencies.
*   **Auditability**: Users can now precisely see how the "Visual Bible" components are assembled before being sent to the AI.
