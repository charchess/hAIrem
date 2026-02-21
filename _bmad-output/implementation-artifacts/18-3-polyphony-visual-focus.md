# Story 18.3: Mise en Scène de la Polyphonie (Visual Focus)

Status: done

## Story

As a User,
I want to clearly see which agent is currently speaking or reacting in a multi-agent conversation,
so that I can follow the group discussion without confusion.

## Acceptance Criteria

1. [AC1] Given an agent is speaking, when the UI updates, then its avatar should be visually emphasized (e.g. Arbitration Glow, Rim Lighting).
2. [AC2] Given an active speaker, when other agents are present (multi-agent future-proofing), then they should be slightly de-emphasized (e.g. slight grayscale or opacity reduction).
3. [AC3] Given multiple agents responding in sequence (cascade), then the visual focus should shift smoothly between them.

## Tasks / Subtasks

- [x] Task 1: Refine Active Speaker Highlight (AC: #1)
  - [x] Subtask 1.1: Implement "Rim Lighting" effect in CSS for `.active-speaker`
  - [x] Subtask 1.2: Add a "Focus Halo" or subtle pulse animation that doesn't cause layout shifts
- [x] Task 2: Implement De-emphasis for Inactive Agents (AC: #2)
  - [x] Subtask 2.1: Add CSS for `.deemphasized-agent` (grayscale 20%, slightly lower brightness)
  - [x] Subtask 2.2: Update `renderer.js` to apply/remove these classes during speech events (integrated into existing .pensive/.speaking system)
- [x] Task 3: Validation and Polish (AC: #3)
  - [x] Subtask 3.1: Verify smooth transitions between speakers in a cascade
  - [x] Subtask 3.2: Ensure visual stability (non-regression of the 1px jitter fix)

## Dev Notes

- Component: `apps/h-bridge/static/` (CSS/JS)
- Constraint: No `transform: scale` if it causes sub-pixel rendering issues, prefer `box-shadow` or `filter`.
- Note: Currently we only show ONE agent at a time in the main stage. AC2/AC3 are for future-proofing multi-agent presence on screen.

### References

- [Source: docs/stories/18.3-polyphony-visual-focus.md]
- [Source: apps/h-bridge/static/ui_zen.css]

## Dev Agent Record

### Agent Model Used

gemini-3-flash-preview

### File List

- `apps/h-bridge/static/style.css`
- `apps/h-bridge/static/ui_zen.css`
- `apps/h-bridge/static/js/renderer.js`
