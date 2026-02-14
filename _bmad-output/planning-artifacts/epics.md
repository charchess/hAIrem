---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments: ['_bmad-output/planning-artifacts/prd.md', '_bmad-output/planning-artifacts/architecture.md']
---

# hAIrem - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for hAIrem, decomposing the requirements from the PRD and Architecture into implementable stories.

**Code Status Legend:**
- ✅ EXISTING - Code already exists and works
- ⚠️ PARTIAL - Partially implemented, needs work
- ❌ NEW/REBUILD - Not implemented or lost in disaster

---

## Requirements Inventory

### Functional Requirements (60 FRs)

| FR# | Requirement | Code Status |
|-----|-------------|-------------|
| FR1 | Users can send text messages to agents via the interface | ✅ EXISTING |
| FR2 | Users can receive text responses from agents | ✅ EXISTING |
| FR3 | Agents can initiate conversations based on context and triggers | ⚠️ PARTIAL |
| FR4 | Chat interface displays agent avatars and emotional states | ⚠️ PARTIAL |
| FR5 | Agents can store new memories from conversations | ✅ EXISTING |
| FR6 | Agents can retrieve relevant memories when responding | ✅ EXISTING |
| FR7 | System consolidates short-term memories to long-term storage (night cycle) | ✅ EXISTING |
| FR8 | System implements memory decay (forgetting) over time | ✅ EXISTING |
| FR9 | Memories are reinforced when recalled | ✅ EXISTING |
| FR10 | Each agent has subjective memory (different interpretation of facts) | ⚠️ PARTIAL |
| FR11 | Memory persists across restarts | ✅ EXISTING |
| FR12 | Users can query the memory log of any agent | ❌ NEW |
| FR13 | Agents can communicate directly (1:1) | ✅ EXISTING |
| FR14 | Agents can broadcast to multiple agents (1:many) | ✅ EXISTING |
| FR15 | Agents can send to all agents (1:all) | ✅ EXISTING |
| FR16 | System supports whisper channel for internal prompts | ⚠️ PARTIAL |
| FR17 | Agents can subscribe to specific event channels | ⚠️ PARTIAL |
| FR18 | System determines which agent should respond | ❌ REBUILD |
| FR19 | Arbiter considers agent interests and relevance when scoring | ❌ REBUILD |
| FR20 | Arbiter evaluates emotional context | ❌ REBUILD |
| FR21 | Named agent gets priority when explicitly mentioned | ❌ REBUILD |
| FR22 | Arbiter manages turn-taking in multi-agent conversations | ❌ REBUILD |
| FR23 | Arbiter can suppress or delay low-priority responses | ❌ REBUILD |
| FR24 | System recognizes different users by voice | ❌ NEW |
| FR25 | Each user has separate memory relationship with each agent | ❌ NEW |
| FR26 | Agents maintain distinct memories for each human | ⚠️ PARTIAL |
| FR27 | System tracks emotional history per user (short-term context) | ❌ NEW |
| FR28 | Agents have dynamic relationships with each other | ❌ NEW |
| FR29 | Agents have dynamic relationships with users | ❌ NEW |
| FR30 | Relationship affects discourse tone but NOT service quality | ❌ NEW |
| FR31 | Grille evolves based on interactions and events | ❌ NEW |
| FR32 | Admin can view token consumption per agent | ❌ NEW |
| FR33 | Admin can enable/disable specific agents | ⚠️ PARTIAL |
| FR34 | Admin can configure agent parameters and persona settings | ❌ NEW |
| FR35 | Admin can add new agents to the system | ⚠️ PARTIAL |
| FR36 | Admin can configure LLM providers per agent | ❌ NEW |
| FR37 | Users can speak to agents via microphone | ✅ EXISTING |
| FR38 | Agents can respond with synthesized voice | ✅ EXISTING |
| FR39 | Each agent has a dedicated base voice | ⚠️ PARTIAL |
| FR40 | Voice modulates based on context and emotion | ❌ NEW |
| FR41 | Voice modulation affects prosody and intonation | ❌ NEW |
| FR42 | System generates images of agents | ✅ EXISTING |
| FR43 | Multiple image generation providers supported | ⚠️ PARTIAL |
| FR44 | Providers can be switched without code changes | ❌ NEW |
| FR45 | Agents have visual avatars with customizable outfits | ✅ EXISTING |
| FR46 | Visual assets are cached for reuse | ✅ EXISTING |
| FR47 | Agents can be assigned to physical locations (rooms) | ❌ NEW |
| FR48 | System tracks which location each agent is present in | ❌ NEW |
| FR49 | Mobile clients can report their location | ❌ NEW |
| FR50 | Remote access (phone) has "exterior" space concept | ❌ NEW |
| FR51 | World state includes themes (neutral, christmas, etc.) | ❌ NEW |
| FR52 | Agents can subscribe to system events | ⚠️ PARTIAL |
| FR53 | Agents can react to hardware events (motion, door, etc.) | ⚠️ PARTIAL |
| FR54 | Agents can react to calendar/date events | ❌ NEW |
| FR55 | Entropy (system) can inject stimulus ideas to agents | ❌ NEW |
| FR56 | Night mode suppresses loud interventions | ✅ EXISTING |
| FR57 | Agents have skills separate from persona | ⚠️ PARTIAL |
| FR58 | Skills are defined in modular packages | ⚠️ PARTIAL |
| FR59 | New agents can be added without system restart | ⚠️ PARTIAL |
| FR60 | Skills can be independently enabled/disabled | ❌ NEW |

### NonFunctional Requirements

- **Performance:** Best effort - optimiser selon les contraintes
- **Chat response time:** depends on LLM provider
- **Voice latency:** depends on STT/TTS provider
- **Integrations:** Via external skills (not native)
- **Testing:** Unit tests et E2E à ajouter

### Additional Requirements

**From Architecture:**
- SurrealDB for memory storage
- Redis for inter-agent communication (H-Link protocol)
- LiteLLM for multi-provider LLM abstraction
- Multi-provider image generation support (NanoBanana, Imagen, etc.)
- Hotplug capability for agents

**From PRD:**
- Web App (SPA) with real-time via WebSocket
- Modern browser support (Chrome, Firefox, Safari)
- Voice input/output as core feature

---

## Epic Summary

| Epic | Name | Phase | FRs | Code Status |
|------|------|-------|-----|-------------|
| 1 | Core Chat | MVP | 4 | ✅ Existing |
| 2 | Memory | MVP | 8 | ✅ Existing |
| 3 | Social Arbiter | MVP | 6 | ❌ REBUILD |
| 4 | Inter-Agent | MVP | 5 | ✅ Existing |
| 5 | Voice | Growth | 5 | ⚠️ Partial |
| 6 | Multi-User & Grid | Growth | 8 | ❌ NEW |
| 7 | Visual | Growth | 5 | ⚠️ Partial |
| 8 | Spatial | Growth | 5 | ❌ NEW |
| 9 | Proactivity | Vision | 5 | ⚠️ Partial |
| 10 | Skills | Vision | 4 | ⚠️ Partial |

---

## Epic 1: Core Chat & Messaging

**Phase:** MVP  
**User Value:** Users can chat with agents and see their responses  
**FRs covered:** FR1, FR2, FR3, FR4

### Story 1.1: Send Text Messages to Agents ✅

**As a** User,  
**I want** to send text messages to agents via the interface,  
**So that** I can communicate with my AI assistants.

**Acceptance Criteria:**

**Given** the user is on the chat interface  
**When** the user types a message and presses send  
**Then** the message appears in the chat thread  
**And** the message is sent to the appropriate agent

**Code Status:** ✅ EXISTS in h-bridge/src/main.py WebSocket handler

---

### Story 1.2: Receive Text Responses from Agents ✅

**As a** User,  
**I want** to receive text responses from agents,  
**So that** I can have a conversation with them.

**Acceptance Criteria:**

**Given** the user has sent a message  
**When** the agent processes the message and responds  
**Then** the response appears in the chat thread  
**And** the response is clearly attributed to the agent

**Code Status:** ✅ EXISTS in BaseAgent.generate_response()

---

### Story 1.3: Agents Initiate Conversations ⚠️

**As a** User,  
**I want** agents to initiate conversations based on context,  
**So that** I receive proactive engagement.

**Acceptance Criteria:**

**Given** an agent has relevant context or trigger  
**When** the trigger conditions are met  
**Then** the agent can send a proactive message to the user  
**And** the message is clearly marked as initiated by the agent

**Code Status:** ⚠️ PARTIAL - Workers exist, triggers need implementation

---

### Story 1.4: Display Agent Avatars and Emotional States ⚠️

**As a** User,  
**I want** to see agent avatars and their emotional states,  
**So that** I can understand which agent is responding and their mood.

**Acceptance Criteria:**

**Given** an agent is responding in the chat  
**When** the response is displayed  
**Then** the agent's avatar is shown next to their message  
**And** the avatar reflects the agent's current emotional state

**Code Status:** ⚠️ PARTIAL - Visual service exists, emotional state not integrated in UI

---

## Epic 2: Memory System

**Phase:** MVP  
**User Value:** Agents remember and can recall past interactions  
**FRs covered:** FR5, FR6, FR7, FR8, FR9, FR10, FR11, FR12

### Story 2.1: Store New Memories ✅

**As a** System,  
**I want** agents to store memories from conversations,  
**So that** they can remember past interactions.

**Acceptance Criteria:**

**Given** a conversation between user and agent  
**When** the conversation is processed  
**Then** the key facts are stored in SurrealDB  
**And** the memory is linked to the specific agent

**Code Status:** ✅ EXISTS - surreal.insert_graph_memory()

---

### Story 2.2: Retrieve Relevant Memories ✅

**As a** Agent,  
**I want** to retrieve relevant memories when responding,  
**So that** my responses are contextualized.

**Acceptance Criteria:**

**Given** an agent receives a user message  
**When** the agent queries its memory  
**Then** relevant memories are retrieved and included in context  
**And** the memories are recent/important

**Code Status:** ✅ EXISTS - recall_memory()

---

### Story 2.3: Night Cycle Consolidation ✅

**As a** System,  
**I want** to consolidate short-term memories to long-term storage,  
**So that** important memories are preserved.

**Acceptance Criteria:**

**Given** the system is in night mode  
**When** the sleep cycle worker runs  
**Then** short-term memories are consolidated to long-term  
**And** non-essential memories are cleaned up

**Code Status:** ✅ EXISTS - MemoryConsolidator.consolidate()

---

### Story 2.4: Memory Decay (Oubli) ✅

**As a** System,  
**I want** memories to decay over time,  
**So that** agents forget irrelevant information.

**Acceptance Criteria:**

**Given** memories in the system  
**When** decay is applied  
**Then** old/unused memories lose strength  
**And** memories below threshold are removed

**Code Status:** ✅ EXISTS - apply_decay()

---

### Story 2.5: Memory Reinforcement ✅

**As a** Agent,  
**I want** memories to be reinforced when recalled,  
**So that** important memories are preserved.

**Acceptance Criteria:**

**Given** an agent recalls a memory  
**When** the recall is successful  
**Then** the memory's strength is boosted  
**And** it will last longer

**Code Status:** ✅ EXISTS - update_memory_strength(boost=True)

---

### Story 2.6: Subjective Memory per Agent ⚠️

**As a** Agent,  
**I want** my own interpretation of facts,  
**So that** each agent has unique memories.

**Acceptance Criteria:**

**Given** a fact occurs  
**When** different agents store it  
**Then** each agent has its own record of the fact  
**And** agents can have different interpretations

**Code Status:** ⚠️ PARTIAL - Per-agent ID exists, verification needed

---

### Story 2.7: Query Memory Log ❌

**As a** User,  
**I want** to query the memory log of any agent,  
**So that** I can see what an agent remembers.

**Acceptance Criteria:**

**Given** a user requests memory log  
**When** the query is executed  
**Then** the agent's memories are displayed  
**And** the user can see dates and content

**Code Status:** ❌ NEW - No UI/API exists

---

## Epic 3: Social Arbiter

**Phase:** MVP  
**User Value:** Right agent responds at the right time  
**FRs covered:** FR18, FR19, FR20, FR21, FR22, FR23

**⚠️ IMPORTANT:** This entire epic needs to be REBUILT. The Sentinel component (which contained the Social Arbiter) was lost in the disaster.

### Story 3.1: Determine Which Agent Responds ❌

**As a** System,  
**I want** to determine which agent should respond to a message,  
**So that** the most appropriate agent replies.

**Acceptance Criteria:**

**Given** a user message arrives  
**When** the arbiter processes it  
**Then** the most relevant agent is selected  
**And** the message is routed to that agent

**Code Status:** ❌ LOST - Was in Sentinel, needs rebuild

---

### Story 3.2: Interest-Based Scoring ❌

**As a** Arbiter,  
**I want** to score agents based on their interests and relevance,  
**So that** the best agent is chosen.

**Acceptance Criteria:**

**Given** a user message  
**When** scoring agents  
**Then** each agent gets a score based on topic relevance  
**And** the agent with highest score is prioritized

**Code Status:** ❌ LOST - Was in Sentinel, needs rebuild

---

### Story 3.3: Emotional Context Evaluation ❌

**As a** Arbiter,  
**I want** to evaluate the emotional context of interactions,  
**So that** responses are emotionally appropriate.

**Acceptance Criteria:**

**Given** a user message with emotional content  
**When** the arbiter analyzes it  
**Then** the emotional tone is detected  
**And** the agent responds appropriately

**Code Status:** ❌ LOST - Was in Sentinel, needs rebuild

---

### Story 3.4: Named Agent Priority ❌

**As a** System,  
**I want** named agents to get priority,  
**So that** when a user says "Lisa, tell me...", Lisa responds.

**Acceptance Criteria:**

**Given** a user explicitly names an agent  
**When** the message is processed  
**Then** that agent gets priority  
**And** other agents are not considered

**Code Status:** ❌ LOST - Was in Sentinel, needs rebuild

---

### Story 3.5: Turn-Taking Management ❌

**As a** Arbiter,  
**I want** to manage turn-taking in conversations,  
**So that** agents don't speak over each other.

**Acceptance Criteria:**

**Given** multiple agents want to respond  
**When** turn-taking is enforced  
**Then** agents respond in sequence  
**And** no overlaps occur

**Code Status:** ❌ LOST - Was in Sentinel, needs rebuild

---

### Story 3.6: Suppress Low-Priority Responses ❌

**As a** Arbiter,  
**I want** to suppress or delay low-priority responses,  
**So that** only relevant responses are sent.

**Acceptance Criteria:**

**Given** an agent has low relevance score  
**When** the arbiter evaluates  
**Then** the response is suppressed or delayed  
**And** only important responses get through

**Code Status:** ❌ LOST - Was in Sentinel, needs rebuild

---

## Epic 4: Inter-Agent Communication

**Phase:** MVP  
**User Value:** Agents can talk to each other  
**FRs covered:** FR13, FR14, FR15, FR16, FR17

### Story 4.1: Agent-to-Agent Direct Messages ✅

**As a** Agent,  
**I want** to send direct messages to another agent,  
**So that** I can communicate privately.

**Acceptance Criteria:**

**Given** an agent wants to message another  
**When** the message is sent  
**Then** only the target agent receives it  
**And** the message is stored in history

**Code Status:** ✅ EXISTS - send_internal_note()

---

### Story 4.2: Agent Broadcast to Multiple Agents ✅

**As a** Agent,  
**I want** to broadcast to a group of agents,  
**So that** multiple agents can receive the message.

**Acceptance Criteria:**

**Given** an agent broadcasts  
**When** the message is sent  
**Then** all subscribed agents receive it  
**And** the message is visible to the group

**Code Status:** ✅ EXISTS - agent:broadcast channel

---

### Story 4.3: Agent Broadcast to All ✅

**As a** Agent,  
**I want** to send a message to all agents,  
**So that** everyone is informed.

**Acceptance Criteria:**

**Given** an agent broadcasts to all  
**When** the message is sent  
**Then** every agent receives it  
**And** the message is logged

**Code Status:** ✅ EXISTS - broadcast channel

---

### Story 4.4: Whisper Channel ⚠️

**As a** System,  
**I want** to send internal prompts to agents without user visibility,  
**So that** I can inject thoughts/imagination.

**Acceptance Criteria:**

**Given** system wants to whisper to an agent  
**When** whisper message is sent  
**Then** only that agent receives it  
**And** it's marked as internal (not visible to user)

**Code Status:** ⚠️ PARTIAL - WhisperService exists, whisper channel incomplete

---

### Story 4.5: Event Subscriptions ⚠️

**As a** Agent,  
**I want** to subscribe to specific event channels,  
**So that** I can react to system events.

**Acceptance Criteria:**

**Given** an agent subscribes to events  
**When** events occur  
**Then** the agent receives notifications  
**And** can react accordingly

**Code Status:** ⚠️ PARTIAL - Redis streams exist, subscription system incomplete

---

## Epic 5: Voice Capabilities

**Phase:** Growth  
**User Value:** Users can speak to agents and hear responses  
**FRs covered:** FR37, FR38, FR39, FR40, FR41

### Story 5.1: Microphone Input ✅

**As a** User,  
**I want** to speak to agents via microphone,  
**So that** I can communicate verbally.

**Acceptance Criteria:**

**Given** the user clicks the microphone button  
**When** audio is captured and transcribed  
**Then** the text is sent to the agent  
**And** the user sees the transcription

**Code Status:** ✅ EXISTS - audio handler + faster-whisper

---

### Story 5.2: Synthesized Voice Output ✅

**As a** User,  
**I want** agents to respond with synthesized voice,  
**So that** I can hear their responses.

**Acceptance Criteria:**

**Given** an agent responds  
**When** the response is generated  
**Then** audio is synthesized  
**And** played to the user

**Code Status:** ✅ EXISTS - TTS service

---

### Story 5.3: Dedicated Base Voice ⚠️

**As a** Agent,  
**I want** a dedicated base voice,  
**So that** each agent has a unique vocal identity.

**Acceptance Criteria:**

**Given** an agent is configured  
**When** voice synthesis is requested  
**Then** the agent's dedicated voice is used  
**And** it's consistent across interactions

**Code Status:** ⚠️ PARTIAL - pyttsx3 partial support, needs voice profiles

---

### Story 5.4: Voice Modulation ❌

**As a** Agent,  
**I want** my voice to modulate based on context and emotion,  
**So that** my responses sound emotionally appropriate.

**Acceptance Criteria:**

**Given** an agent responds with emotion  
**When** voice synthesis is triggered  
**Then** the voice is modulated (faster/slower, higher/lower)  
**And** it matches the emotional context

**Code Status:** ❌ NEW - Not implemented

---

### Story 5.5: Prosody and Intonation ❌

**As a** Agent,  
**I want** my voice to have proper prosody and intonation,  
**So that** I sound natural.

**Acceptance Criteria:**

**Given** text to be spoken  
**When** TTS is generated  
**Then** prosody and intonation are applied  
**And** the speech sounds natural

**Code Status:** ❌ NEW - Not implemented

---

## Epic 6: Multi-User & Social Grid

**Phase:** Growth  
**User Value:** Different users have personalized relationships with agents  
**FRs covered:** FR24, FR25, FR26, FR27, FR28, FR29, FR30, FR31

**⚠️ NOTE:** This epic is mostly NEW - these features were never fully implemented.

### Story 6.1: Voice Recognition ❌

**As a** System,  
**I want** to recognize different users by voice,  
**So that** I know who is speaking.

**Acceptance Criteria:**

**Given** a user speaks  
**When** audio is captured  
**Then** the voice is identified  
**And** the user is recognized

**Code Status:** ❌ NEW - Not implemented

---

### Story 6.2: Per-User Memory ❌

**As a** Agent,  
**I want** to have separate memories for each user,  
**So that** I remember interactions with each person differently.

**Acceptance Criteria:**

**Given** an agent interacts with multiple users  
**When** memories are stored  
**Then** each user's memories are separate  
**And** retrievable by user

**Code Status:** ❌ NEW - Not implemented

---

### Story 6.3: Emotional History Tracking ❌

**As a** System,  
**I want** to track emotional history per user,  
**So that** I understand short-term context.

**Acceptance Criteria:**

**Given** a user interacts  
**When** emotional state is detected  
**Then** it's stored in short-term context  
**And** affects next interactions

**Code Status:** ❌ NEW - Not implemented

---

### Story 6.4: Agent-to-Agent Relationships ❌

**As a** Agent,  
**I want** to have dynamic relationships with other agents,  
**So that** my interactions reflect my feelings toward them.

**Acceptance Criteria:**

**Given** agents interact  
**When** relationships evolve  
**Then** each agent's attitude is tracked  
**And** affects communication tone

**Code Status:** ❌ NEW - Not implemented

---

### Story 6.5: Agent-to-User Relationships ❌

**As a** Agent,  
**I want** to have dynamic relationships with users,  
**So that** my interactions reflect how I feel about them.

**Acceptance Criteria:**

**Given** an agent interacts with a user  
**When** relationship evolves  
**Then** the agent's attitude is updated  
**And** affects discourse tone

**Code Status:** ❌ NEW - Not implemented

---

### Story 6.6: Tone Varies, Quality Constant ❌

**As a** System,  
**I want** relationship to affect tone but NOT service quality,  
**So that** all users receive equal service.

**Acceptance Criteria:**

**Given** an agent has poor relationship with user  
**When** the user requests service  
**Then** the tone may vary but quality remains constant  
**And** the service is always provided correctly

**Code Status:** ❌ NEW - Not implemented

---

### Story 6.7: Evolving Social Grid ❌

**As a** System,  
**I want** the social grid to evolve over time,  
**So that** relationships change based on interactions.

**Acceptance Criteria:**

**Given** interactions occur  
**When** relationship thresholds are crossed  
**Then** relationships evolve  
**And** the grid updates

**Code Status:** ❌ NEW - Not implemented

---

## Epic 7: Administration

**Phase:** Growth  
**User Value:** Admin can manage agents and monitor usage  
**FRs covered:** FR32, FR33, FR34, FR35, FR36

### Story 7.1: View Token Consumption ❌

**As an** Admin,  
**I want** to view token consumption per agent,  
**So that** I can monitor costs.

**Acceptance Criteria:**

**Given** admin accesses dashboard  
**When** consumption is requested  
**Then** token usage per agent is displayed  
**And** costs are calculated

**Code Status:** ❌ NEW - Not implemented

---

### Story 7.2: Enable/Disable Agents ⚠️

**As an** Admin,  
**I want** to enable or disable specific agents,  
**So that** I can control which agents are active.

**Acceptance Criteria:**

**Given** admin modifies agent status  
**When** the change is saved  
**Then** the agent is enabled/disabled  
**And** responds accordingly

**Code Status:** ⚠️ PARTIAL - is_active flag exists, UI missing

---

### Story 7.3: Configure Agent Parameters ❌

**As an** Admin,  
**I want** to configure agent parameters and persona settings,  
**So that** I can customize agent behavior.

**Acceptance Criteria:**

**Given** admin accesses configuration  
**When** parameters are modified  
**Then** agent behavior changes  
**And** changes persist

**Code Status:** ❌ NEW - Not implemented

---

### Story 7.4: Add New Agents ⚠️

**As an** Admin,  
**I want** to add new agents to the system,  
**So that** new personas can join.

**Acceptance Criteria:**

**Given** admin adds new agent  
**When** agent configuration is saved  
**Then** the agent is created  
**And** can interact

**Code Status:** ⚠️ PARTIAL - AgentRegistry exists, hotplug incomplete

---

### Story 7.5: Configure LLM Providers ❌

**As an** Admin,  
**I want** to configure LLM providers per agent,  
**So that** each agent can use different LLMs.

**Acceptance Criteria:**

**Given** admin configures provider  
**When** agent makes LLM request  
**Then** the configured provider is used  
**And** fallback works if down

**Code Status:** ❌ NEW - Not implemented

---

## Epic 8: Visual Generation

**Phase:** Growth  
**User Value:** Agents have visual representations  
**FRs covered:** FR42, FR43, FR44, FR45, FR46

### Story 8.1: Image Generation ✅

**As a** System,  
**I want** to generate images of agents,  
**So that** they have visual representations.

**Acceptance Criteria:**

**Given** an agent needs an image  
**When** generation is triggered  
**Then** an image is created  
**And** displayed to user

**Code Status:** ✅ EXISTS - Visual service

---

### Story 8.2: Multi-Provider Support ⚠️

**As a** System,  
**I want** to support multiple image generation providers,  
**So that** I can switch between them.

**Acceptance Criteria:**

**Given** multiple providers configured  
**When** generation is requested  
**Then** the configured provider is used  
**And** providers are interchangeable

**Code Status:** ⚠️ PARTIAL - Provider abstraction incomplete

---

### Story 8.3: Switchable Providers ❌

**As an** Admin,  
**I want** to switch providers without code changes,  
**So that** I can change providers easily.

**Acceptance Criteria:**

**Given** admin changes provider  
**When** configuration is updated  
**Then** new provider is used  
**And** no code changes needed

**Code Status:** ❌ NEW - Not implemented

---

### Story 8.4: Customizable Outfits ✅

**As a** User,  
**I want** agents to have customizable outfits,  
**So that** they can look different.

**Acceptance Criteria:**

**Given** outfit is requested  
**When** agent generates image  
**Then** the specified outfit is used  
**And** saved to vault

**Code Status:** ✅ EXISTS - Vault service

---

### Story 8.5: Asset Caching ✅

**As a** System,  
**I want** visual assets to be cached,  
**So that** generation is faster.

**Acceptance Criteria:**

**Given** asset was generated  
**When** same asset is requested  
**Then** cached version is returned  
**And** generation is skipped

**Code Status:** ✅ EXISTS - Cache service

---

## Epic 9: Spatial Presence

**Phase:** Growth  
**User Value:** Agents aware of location  
**FRs covered:** FR47, FR48, FR49, FR50, FR51

### Story 9.1: Room Assignment ❌

**As a** System,  
**I want** agents to be assigned to physical locations,  
**So that** I know which agent is in which room.

**Acceptance Criteria:**

**Given** agents are configured  
**When** room assignment is set  
**Then** agents are linked to rooms  
**And** location is tracked

**Code Status:** ❌ NEW - Not implemented

---

### Story 9.2: Location Tracking ❌

**As a** System,  
**I want** to track which location each agent is present in,  
**So that** I know where agents are.

**Acceptance Criteria:**

**Given** location updates  
**When** agent moves  
**Then** location is updated  
**And** persisted

**Code Status:** ❌ NEW - Not implemented

---

### Story 9.3: Mobile Location ❌

**As a** System,  
**I want** mobile clients to report their location,  
**So that** agents can be mobile.

**Acceptance Criteria:**

**Given** mobile client sends location  
**When** location is received  
**Then** agent's location is updated  
**And** tracked

**Code Status:** ❌ NEW - Not implemented

---

### Story 9.4: Exterior Space ❌

**As a** System,  
**I want** remote access to have "exterior" space concept,  
**So that** agents know when user is outside.

**Acceptance Criteria:**

**Given** user accesses via phone  
**When** location is exterior  
**Then** "exterior" space is set  
**And** agents respond accordingly

**Code Status:** ❌ NEW - Not implemented

---

### Story 9.5: World Themes ❌

**As a** System,  
**I want** world state to include themes,  
**So that** agents can respond to seasonal/contextual changes.

**Acceptance Criteria:**

**Given** theme is set  
**When** agents respond  
**Then** theme context is included  
**And** responses reflect theme

**Code Status:** ❌ NEW - Not implemented

---

## Epic 10: Proactivity & Events

**Phase:** Vision  
**User Value:** Agents proactively engage  
**FRs covered:** FR52, FR53, FR54, FR55, FR56

### Story 10.1: Event Subscriptions ⚠️

**As an** Agent,  
**I want** to subscribe to system events,  
**So that** I can react to them.

**Acceptance Criteria:**

**Given** agent subscribes to event  
**When** event occurs  
**Then** agent is notified  
**And** can react

**Code Status:** ⚠️ PARTIAL - Redis streams exist, subscription system incomplete

---

### Story 10.2: Hardware Events ⚠️

**As an** Agent,  
**I want** to react to hardware events,  
**So that** I can respond to motion, door, etc.

**Acceptance Criteria:**

**Given** hardware event occurs  
**When** agent is subscribed  
**Then** agent reacts  
**And** response is generated

**Code Status:** ⚠️ PARTIAL - HA integration exists, event routing incomplete

---

### Story 10.3: Calendar Events ❌

**As an** Agent,  
**I want** to react to calendar/date events,  
**So that** I can acknowledge special dates.

**Acceptance Criteria:**

**Given** calendar event occurs  
**When** agent is subscribed  
**Then** agent acknowledges  
**And** responds appropriately

**Code Status:** ❌ NEW - Not implemented

---

### Story 10.4: System Stimulus (Entropy) ❌

**As a** System,  
**I want** to inject stimulus ideas to agents,  
**So that** they can imagine/thinking proactively.

**Acceptance Criteria:**

**Given** system wants to stimulate  
**When** stimulus is injected  
**Then** agent receives whisper  
**And** can act on it

**Code Status:** ❌ NEW - Not implemented

---

### Story 10.5: Night Mode ✅

**As a** System,  
**I want** night mode to suppress loud interventions,  
**So that** users are not disturbed.

**Acceptance Criteria:**

**Given** night mode is active  
**When** agent wants to respond loudly  
**Then** response is suppressed or softened  
**And** user is not disturbed

**Code Status:** ✅ EXISTS - Sleep cycle worker

---

## Epic 11: Skills & Hotplug

**Phase:** Vision  
**User Value:** Extend agent capabilities dynamically  
**FRs covered:** FR57, FR58, FR59, FR60

### Story 11.1: Skills Separation ⚠️

**As an** Agent,  
**I want** skills to be separate from persona,  
**So that** I can have different capabilities.

**Acceptance Criteria:**

**Given** agent is configured  
**When** skills are loaded  
**Then** skills are separate from persona  
**And** can be mixed/matched

**Code Status:** ⚠️ PARTIAL - Plugin loader exists

---

### Story 11.2: Modular Skill Packages ⚠️

**As a** System,  
**I want** skills to be defined in modular packages,  
**So that** they can be reused.

**Acceptance Criteria:**

**Given** skill package exists  
**When** loaded  
**Then** it's modular  
**And** reusable

**Code Status:** ⚠️ PARTIAL - Structure exists

---

### Story 11.3: Hotplug ⚠️

**As an** Admin,  
**I want** to add new agents without system restart,  
**So that** deployment is seamless.

**Acceptance Criteria:**

**Given** new agent folder is added  
**When** hotplug detects it  
**Then** agent is loaded  
**And** ready without restart

**Code Status:** ⚠️ PARTIAL - File watcher exists

---

### Story 11.4: Enable/Disable Skills ❌

**As an** Admin,  
**I want** to enable or disable skills independently,  
**So that** I can control capabilities.

**Acceptance Criteria:**

**Given** skill is configured  
**When** admin toggles it  
**Then** skill is enabled/disabled  
**And** agent updates accordingly

**Code Status:** ❌ NEW - Not implemented

---

## Implementation Priority

### MVP (Phase 1) - Highest Priority

1. **Epic 3: Social Arbiter** - REBUILD (lost in disaster)
2. **Epic 1: Core Chat** - Validate existing code works
3. **Epic 2: Memory** - Validate existing code works
4. **Epic 4: Inter-Agent** - Validate existing code works

### Growth (Phase 2)

1. **Epic 5: Voice** - Complete modulation
2. **Epic 6: Multi-User** - NEW
3. **Epic 7: Admin** - New UI features
4. **Epic 8: Visual** - Complete provider switching

### Vision (Phase 3)

1. **Epic 9: Spatial** - NEW
2. **Epic 10: Skills** - Complete hotplug
