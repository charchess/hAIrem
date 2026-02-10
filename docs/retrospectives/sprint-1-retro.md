# Sprint 1 Retrospective

**Date:** 2026-02-06
**Scope:** Epic 1 (API Modernization & Security Gateway) + Epic 5 Stories 5.1-5.2 (Dependency Hygiene)
**Facilitator:** Bob (Scrum Master)
**Participants:** Amelia (Dev), Winston (Architect), Quinn (QA), Charchess (Project Lead)

---

## Sprint 1 Summary

### Delivery Metrics

- Stories completed: **5/5** (100%)
- Test suite: **0 → 47 tests** (built from scratch)
- Code Review findings: **20 total** (0 High, 9 Medium, 12 Low — all fixed)
- Regressions: **0** (full suite passed after every story)
- Production incidents: **0**

### Stories Delivered

| Story | Title | Tests Added | CR Findings |
|-------|-------|-------------|-------------|
| 1.1 | API Versioning Migration | 23 | 6 (0H, 3M, 3L) |
| 1.2 | Standardized Error Response Format | 7 | 5 (0H, 3M, 2L) |
| 1.3 | API Key Authentication | 17 | 4 (0H, 1M, 3L) |
| 5.1 | Dependency Pinning & Lockfile | 0 (infra) | 3 (0H, 2M, 1L) |
| 5.2 | Celery Security Upgrade | 0 (dep bump) | 2 (0H, 0M, 2L) |

### Quality Trajectory

CR findings per story: **6 → 5 → 4 → 3 → 2** (continuous improvement)

---

## What Went Well

1. **TDD Red-Green-Refactor cycle** worked effectively — tests written first, implementation driven by failing tests, high confidence in delivered code
2. **Architecture specs translated directly to code** — no fundamental revisions needed for API-001, API-002, SEC-001 through SEC-004
3. **Test infrastructure built from zero** — `conftest.py` with mocked ML dependencies enables full API testing without GPU. Reusable foundation for Sprint 2
4. **Continuous improvement measurable** — findings decreased every story, showing the team learns from CR feedback and applies lessons
5. **Team autonomy** — 5 stories delivered without escalation or blockers requiring Project Lead intervention

---

## Challenges

1. **pip-compile/PyTorch incompatibility** (Story 5.1)
   - `torch==2.1.2` has been removed from all PyTorch CUDA indexes (only 2.2.0+ available)
   - 4 different approaches tried with pip-compile, all failed
   - **Resolution:** Pivoted to `uv pip compile` which handles PyTorch CUDA index correctly
   - **Lesson:** Validate tooling assumptions with a spike before committing to a specific tool in story specs

2. **BaseHTTPMiddleware exception handling gotcha** (Story 1.3)
   - Story spec showed `raise ImagenAPIError(...)` in middleware — doesn't work
   - Starlette `BaseHTTPMiddleware` bypasses FastAPI exception handlers
   - Must return `JSONResponse` directly from middleware
   - **Lesson:** Document framework-specific constraints in architecture specs

3. **Documentation count errors** (Stories 1.1, 1.2, 5.2)
   - "14 decorators" → 13, "23 HTTPExceptions" → 24, "75 packages" → 76
   - Counts written from memory instead of verified with commands
   - **Lesson:** Always validate counts with `grep -c` or equivalent before documenting

4. **Incomplete test coverage on first pass** (Stories 1.1, 1.3)
   - Story 1.1: only 5/13 old paths tested for 404
   - Story 1.3: reference CRUD and civitai endpoints missing auth tests
   - Both caught by Code Review
   - **Lesson:** Write exhaustive tests including edge cases from the start

5. **Timing-unsafe API key comparison** (Story 1.3)
   - Used `!=` instead of `hmac.compare_digest()` for API key comparison
   - Caught in Code Review — real security vulnerability
   - **Lesson:** Security-sensitive operations should be specified in architecture docs (SEC-001 should have mandated constant-time comparison)

---

## Significant Discoveries

1. **3 operational scripts broken by Sprint 1 changes**
   - `benchmark.sh`, `generate.sh`, `generate_panther_cyborg.sh`
   - All use pre-Sprint-1 API paths (no `/v1/` prefix)
   - No `X-API-Key` header (will get 401)
   - Error parsing assumes old response format
   - **Impact:** Anyone running these scripts will get failures

2. **Docker available in WSL2** (new environment)
   - Docker CLI v28.2.2 installed
   - Permission issue on daemon socket (fixable: `usermod -aG docker`)
   - `docker compose` plugin not installed
   - **Impact:** Can enable Docker integration tests for Sprint 2

3. **CLAUDE.md desynchronized**
   - Still references Celery 5.3.4 (now 5.6.2), diffusers 0.25.0 (now 0.27.2), etc.
   - Stack table outdated

---

## Previous Retrospective

First retrospective — no previous retro to reference. Baseline established.

---

## Action Items

### Process Improvements

| # | Action | Owner | Criteria | When |
|---|--------|-------|----------|------|
| 1 | Verify counts in dev notes with commands | Amelia (Dev) | `grep -c` or equivalent used before documenting | Sprint 2 onwards |
| 2 | Add framework constraints to story specs | Winston (Architect) | "Framework Constraints" section in middleware/exception stories | Sprint 2 stories |
| 3 | Write exhaustive tests on first pass | Amelia (Dev) + Quinn (QA) | Coverage checklist in story template | Sprint 2 onwards |

### Technical Debt

| # | Item | Owner | Priority | Scope |
|---|------|-------|----------|-------|
| 1 | Update 3 operational scripts | Amelia (Dev) | **High** | `/v1/` endpoints, `X-API-Key` header, error envelope parsing |
| 2 | Fix Docker permissions in WSL2 | Charchess / Amelia | Medium | `usermod -aG docker`, install docker compose plugin |
| 3 | Synchronize CLAUDE.md | Amelia (Dev) | Low | Update versions, stack table, endpoint paths |

### Team Agreements

- Validate all counts/numbers with commands before documenting
- Story specs include known framework constraints
- Code Review verifies exhaustive coverage, not just happy paths

---

## Sprint 2 Preparation

### Scope

- **Epic 2:** Generation Pipeline Validation & Enhancement (Stories 2.1, 2.2, 2.3)
- **Epic 5 (continued):** Stories 5.3 (Logging Migration), 5.4 (Dependency Upgrades)

### Dependencies on Sprint 1

All satisfied:
- API versioning (`/v1/`) — done (Story 1.1)
- Error envelope format — done (Story 1.2)
- API key authentication — done (Story 1.3)
- Lockfile infrastructure (`make lock`, `uv`) — done (Story 5.1)
- Celery 5.6.2 — done (Story 5.2)

### Risks

- Epic 2 touches ML pipeline core (`pipeline.py`, `worker.py`) — more complex than Sprint 1 API layer
- Story 5.4 (dependency upgrades) has high regression surface (FastAPI, Pillow, Transformers)
- Mock sophistication needs to increase for pipeline/worker testing

### Prerequisites

- [ ] Fix Docker permissions (enables integration tests)
- [ ] Update operational scripts (enables manual validation)

### No blockers identified

---

## Readiness Assessment

| Area | Status | Notes |
|------|--------|-------|
| Testing & Quality | OK | 47 tests, zero regressions |
| Deployment | Pending | Not yet deployed — Docker build/runtime validation deferred |
| Technical Health | Stable | Clean codebase, lockfile in place |
| Unresolved Blockers | None | All Sprint 1 work complete |

**Verdict:** Sprint 1 complete. Ready for Sprint 2 after fixing Docker permissions and updating scripts.

---

## Sprint 1 Retrospective Status: COMPLETE
