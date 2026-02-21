# Log de Non-Régression (User Feedback Testing)

Ce document répertorie les points critiques identifiés par l'utilisateur lors de la phase de test finale pour garantir qu'aucune régression n'intervienne lors des futures mises à jour.

| Date | Point de Vigilance | Description | Statut |
| :--- | :--- | :--- | :--- |
| 2026-02-16 | **Fermeture Panels** | Fermeture de Crew et Control par clic extérieur à la fenêtre. | ✅ Validé |
| 2026-02-16 | **Conso Tokens** | Présence des infos IN/OUT/TOT/COST dans le Crew Panel pour toutes les entités. | ✅ Validé |
| 2026-02-16 | **Indicateurs Santé** | État des voyants (WS, Redis, LLM, Brain) dans le System Control. | 🔴 En cours (Fix requis) |
| 2026-02-16 | **Config Agents** | Capacité de configurer indépendamment chaque agent (Overrides). | ✅ Validé |
| 2026-02-16 | **Cliquabilité Onglets** | Navigation fonctionnelle entre System, LLM, Logs et Agents. | ✅ Validé |
| 2026-02-16 | **Sélection Agents** | Filtrage des entités techniques (dieu, bridge, core) de la liste de chat. | ✅ Validé |
| 2026-02-16 | **LLM Global Config** | Saisie et persistance (Vault) des clés API globales et par agent. | ✅ Validé |
| 2026-02-16 | **Barge-in / Interruption** | Capacité à couper la parole de l'IA en commençant à parler. | ✅ Validé |
| 2026-02-16 | **Localisation Device** | Mapping de la pièce du périphérique vers l'agent répondant. | ✅ Validé |
