# Story 18.2: L'Arbitre Social (Algorithme UTS)

Status: done

## Story

As a User,
I want the system to automatically decide which agent should speak based on the topic and emotional context using LLM-based scoring,
so that the conversation feels natural, intelligent, and relevant.

## Acceptance Criteria

1. [AC1] Given a new message on the bus, when the Social Arbiter evaluates the interaction, then it calculates an LLM-based "Urge-to-Speak" (UTS) score for each active agent.
2. [AC2] Given UTS scores are calculated, when one or more agents are relevant (> 0.75), then they are activated in sequence.
3. [AC3] Given a collective greeting (e.g. "bonjour les filles"), then the arbiter selects a single random spokesperson among active agents (already partially implemented, but should be integrated into UTS logic).
4. [AC4] Given a named mention, then that agent gets a priority boost (UTS = 1.0).

## Tasks / Subtasks

- [x] Task 1: Implement LLM-based Scoring Engine (AC: #1)
  - [x] Subtask 1.1: Create prompt template for UTS scoring (evaluating relevance, expertise, and emotional fit)
  - [x] Subtask 1.2: Implement `calculate_relevance_llm` in `ScoringEngine` using a micro-LLM call or optimized prompt
- [x] Task 2: Integrate UTS logic into Social Arbiter (AC: #1, #2)
  - [x] Subtask 2.1: Update `determine_responder_async` to use the new LLM scoring
  - [x] Subtask 2.2: Implement thresholding logic (> 0.75) for automatic activation
- [x] Task 3: Refine Addressing and Mentions (AC: #3, #4)
  - [x] Subtask 3.1: Re-integrate collective greeting logic into the new flow
  - [x] Subtask 3.2: Ensure named mentions correctly bypass or top the scoring
- [x] Task 4: Integration and Tests (AC: #1, #2, #3, #4)
  - [x] Subtask 4.1: Update `tests/unit/test_uts_arbiter.py` with real assertions
  - [x] Subtask 4.2: Verify non-regression with `tests/e2e/conversation-flow.spec.ts`

## Dev Notes

- Component: `apps/h-core/src/features/home/social_arbiter/`
- Pattern: "Urge to Speak" (UTS) algorithm [Source: docs/architecture/10-social-arbiter.md]
- LLM Usage: Use the system-level `LlmClient` ( Nemotron ) for scoring to avoid high cost/latency.

### References

- [Source: docs/stories/18.2-uts-algorithm.md]
- [Source: apps/h-core/src/features/home/social_arbiter/arbiter.py]

## Dev Agent Record

### Agent Model Used

gemini-3-flash-preview

### File List

- `apps/h-core/src/features/home/social_arbiter/scoring.py`
- `apps/h-core/src/features/home/social_arbiter/arbiter.py`
- `tests/unit/test_uts_arbiter.py`
