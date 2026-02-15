# Test Design: hAIrem Project - Cross-Epic Coverage Analysis

**Date:** 2026-02-15
**Author:** Charchess
**Status:** Draft
**Mode:** Epic-Level (Comprehensive Cross-Epic Analysis)

---

## Executive Summary

**Scope:** Full test design analysis for hAIrem project covering Epics 1-14

**Risk Summary:**

- Total risks identified: 18
- High-priority risks (≥6): 8
- Critical categories: PERF, SCAL, RELI, SEC

**Coverage Summary:**

- Current test coverage: ~60% functional, ~10% performance, ~0% scalability, ~50% reliability
- Known gaps: Performance (~90% gap), Scalability (~100% gap), Reliability (~50% gap)
- P0 scenarios: 12 (~30-40 hours)
- P1 scenarios: 18 (~25-35 hours)
- P2/P3 scenarios: 24 (~15-25 hours)
- **Total effort needed to close gaps**: 70-100 hours

---

## Not in Scope

| Item | Reasoning | Mitigation |
| ---- | --------- | ---------- |
| **Epic 10 (Proactivity)** | Not yet started - stories in backlog | Test design will be created when Epic starts |
| **Epic 11 (Skills & Hotplug)** | Not yet started - stories in backlog | Test design will be created when Epic starts |
| **Legacy API v1 deprecation** | Deprecated, no longer maintained | Covered by sunset monitoring |
| **Third-party LLM provider testing** | Providers have own QA (OpenAI, Anthropic) | Rely on provider SLAs |

---

## Risk Assessment

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- | -------- |
| R-001 | PERF | Message latency >2s under load (50+ concurrent users) | 3 | 3 | 9 | Load testing, caching layer | Dev | 2026-03-15 |
| R-002 | SCAL | Memory leak in long-running conversations (>100 turns) | 3 | 3 | 9 | Memory profiling, leak detection | Dev | 2026-03-01 |
| R-003 | SCAL | Database connection pool exhaustion at scale | 2 | 3 | 6 | Connection pooling, rate limiting | Dev | 2026-03-15 |
| R-004 | RELI | Night cycle consolidation fails silently | 2 | 3 | 6 | Monitoring, alerting, retry logic | Dev | 2026-02-28 |
| R-005 | SEC | Agent memory injection via prompt | 2 | 3 | 6 | Input sanitization, LLM guardrails | Dev | 2026-02-28 |
| R-006 | PERF | Voice synthesis latency >500ms | 3 | 2 | 6 | Voice pipeline optimization | Dev | 2026-03-15 |
| R-007 | RELI | Social arbiter race conditions under high load | 2 | 3 | 6 | Concurrency testing, locking | Dev | 2026-03-01 |
| R-008 | DATA | Memory corruption during decay process | 2 | 3 | 6 | Data validation, integrity checks | Dev | 2026-02-28 |

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |
| R-009 | TECH | Cross-user memory leakage in multi-tenant scenario | 2 | 2 | 4 | Isolation testing, code review | Dev |
| R-010 | PERF | Image generation timeout on complex prompts | 2 | 2 | 4 | Timeout handling, fallback | Dev |
| R-011 | RELI | WebSocket reconnection failures | 2 | 2 | 4 | Reconnection logic, exponential backoff | Dev |
| R-012 | TECH | Plugin loader crashes on malformed skills | 2 | 2 | 4 | Validation, error boundaries | Dev |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------- |
| R-013 | BUS | Avatar outfit caching inefficiencies | 1 | 2 | 2 | Monitor |
| R-014 | OPS | Log volume overwhelming storage | 1 | 1 | 1 | Monitor |
| R-015 | BUS | Non-English speech recognition accuracy | 1 | 2 | 2 | Monitor |
| R-016 | TECH | Visual provider rate limiting edge cases | 1 | 2 | 2 | Monitor |

### Risk Category Legend

- **TECH**: Technical/Architecture (flaws, integration, scalability)
- **SEC**: Security (access controls, auth, data exposure)
- **PERF**: Performance (SLA violations, degradation, resource limits)
- **DATA**: Data Integrity (loss, corruption, inconsistency)
- **BUS**: Business Impact (UX harm, logic errors, revenue)
- **OPS**: Operations (deployment, config, monitoring)
- **SCAL**: Scalability (concurrency, load handling, growth)

---

## Epic Coverage Analysis

### Epic 1: Core Chat (MVP) - DONE
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 1-1 Send text messages | Done | Unit + Integration | None |
| 1-2 Receive text responses | Done | Unit + Integration | None |
| 1-3 Agents initiate conversations | Done | Unit | Medium - No E2E |
| 1-4 Display agent avatars | Done | Unit | None |

**Gap Assessment:** Core functionality covered, but E2E coverage incomplete

### Epic 2: Memory (MVP) - DONE
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 2-1 Store new memories | Done | Unit + Integration | None |
| 2-2 Retrieve relevant memories | Done | Unit + Integration | None |
| 2-3 Night cycle consolidation | Done | Integration | Medium - No reliability tests |
| 2-4 Memory decay | Done | Unit | Medium - No E2E |
| 2-5 Memory reinforcement | Done | Unit | Medium - No E2E |
| 2-6 Subjective memory | Done | Unit | None |
| 2-7 Query memory log | Done | Unit | None |

**Gap Assessment:** Reliability tests needed for consolidation (R-004)

### Epic 3: Social Arbiter (MVP) - DONE
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 3-0 Social arbiter API | Done | API Tests | None |
| 3-1 Determine which agent responds | Done | Unit + API | None |
| 3-2 Interest-based scoring | Done | Unit | None |
| 3-3 Emotional context evaluation | Done | Unit | None |
| 3-4 Named agent priority | Done | Unit | None |
| 3-5 Turn-taking management | Done | Unit | None |
| 3-6 Suppress low-priority responses | Done | Unit | None |

**Gap Assessment:** Concurrency tests needed for race conditions (R-007)

### Epic 4: Inter-Agent (MVP) - DONE
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 4-1 Agent-to-agent direct messages | Done | Unit + Integration | None |
| 4-2 Agent broadcast multiple | Done | Unit | Medium - No E2E |
| 4-3 Agent broadcast all | Done | Unit | Medium - No E2E |
| 4-4 Whisper channel | Done | Unit | None |
| 4-5 Event subscriptions | Done | Unit | None |

**Gap Assessment:** E2E tests for multi-agent scenarios

### Epic 5: Voice (Growth) - DONE
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 5-1 Microphone input | Done | Unit | Medium - No E2E |
| 5-2 Synthesized voice output | Done | Unit | None |
| 5-3 Dedicated base voice | Done | Unit | None |
| 5-4 Voice modulation | Done | Unit | None |
| 5-5 Prosody intonation | Done | Unit | None |

**Gap Assessment:** Performance tests needed for latency (R-006)

### Epic 6: Multi-User & Social Grid (Growth) - DONE
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 6-0 Memory isolation | Done | Integration | None |
| 6-1 Voice recognition | Done | Unit | Medium - No E2E |
| 6-2 Per-user memory | Done | Integration | None |
| 6-3 Emotional history tracking | Done | Unit | None |
| 6-4 Agent-to-agent relationships | Done | Unit | None |
| 6-5 Agent-to-user relationships | Done | Unit | None |
| 6-6 Tone varies quality constant | Done | Unit | None |
| 6-7 Evolving social grid | Done | Unit | None |

**Gap Assessment:** Multi-user isolation testing needed (R-009)

### Epic 7: Administration (Growth) - DONE
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 7-0 RBAC security fix | Done | Integration | None |
| 7-1 View token consumption | Done | API Tests | None |
| 7-2 Enable/disable agents | Done | Unit | None |
| 7-3 Configure agent parameters | Done | Unit | None |
| 7-4 Add new agents | Done | Unit | None |
| 7-5 Configure LLM providers | Done | Unit | None |

**Gap Assessment:** Security E2E tests needed

### Epic 8: Visual (Growth) - DONE
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 8-1 Image generation | Done | Unit + API | None |
| 8-2 Multi-provider support | Done | Unit | None |
| 8-3 Switchable providers API | Done | Unit | None |
| 8-4 Customizable outfits | Done | Unit | None |
| 8-5 Asset caching | Done | Unit | None |

**Gap Assessment:** Caching performance tests needed

### Epic 9: Spatial Presence (Growth) - DONE
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 9-0 Spatial API | Done | API Tests | None |
| 9-1 Room assignment | Done | Unit | None |
| 9-2 Location tracking | Done | Unit | None |
| 9-3 Mobile location | Done | Unit | None |
| 9-4 Exterior space | Done | Unit | None |
| 9-5 World themes | Done | Unit | None |

**Gap Assessment:** Location tracking performance tests

### Epic 10: Proactivity (Vision) - BACKLOG
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 10-1 Event subscriptions | Backlog | None | Full coverage needed |
| 10-2 Hardware events | Backlog | None | Full coverage needed |
| 10-3 Calendar events | Backlog | None | Full coverage needed |
| 10-4 System stimulus entropy | Backlog | None | Full coverage needed |
| 10-5 Night mode | Done | None | None |

**Gap Assessment:** Test design to be created when Epic starts

### Epic 11: Skills & Hotplug (Vision) - BACKLOG
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 11-1 Skills separation | Backlog | None | Full coverage needed |
| 11-2 Modular skill packages | Backlog | None | Full coverage needed |
| 11-3 Hotplug | Backlog | None | Full coverage needed |
| 11-4 Enable/disable skills | Backlog | None | Full coverage needed |

**Gap Assessment:** Test design to be created when Epic starts

### Epic 13: Deep Cognitive Memory - DONE
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 13-1 Graphe subjectif | Done | Unit | None |
| 13-2 L'algorithme d'oubli (semantic decay) | Done | Unit + Integration | None |
| 13-3 Subjective retrieval | Done | Unit | None |
| 13-4 Conflict synthesis | Done | Unit | None |
| 13-5 Restore sleep orchestration | Done | Integration | None |
| 13-6 Transient state management | Done | Unit | None |

**Gap Assessment:** Data integrity tests for decay (R-008)

### Epic 14: Sensory Layer - DONE
| Story | Status | Test Coverage | Gap |
| ----- | ------ |--------------|-----|
| 14 (all stories) | Done | Limited | Full coverage needed |

**Gap Assessment:** Significant gap - limited tests exist

---

## Test Coverage Plan

### P0 (Critical) - Run on every commit

**Criteria**: Blocks core journey + High risk (≥6) + No workaround

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Memory leak detection in long sessions | Performance | R-002 | 5 | Dev | Heap snapshots, 100+ turn conversations |
| Message latency under load | Performance | R-001 | 8 | Dev | 50+ concurrent users |
| Database connection pool limits | Scalability | R-003 | 4 | Dev | Connection exhaustion testing |
| Night cycle silent failures | Reliability | R-004 | 3 | Dev | Monitoring, alerting verification |
| Agent memory injection prevention | Security | R-005 | 6 | Dev | Prompt injection tests |

**Total P0**: 26 tests, ~30-40 hours

### P1 (High) - Run on PR to main

**Criteria**: Important features + Medium risk (3-4) + Common workflows

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Voice synthesis latency | Performance | R-006 | 4 | Dev | <500ms target |
| Social arbiter race conditions | Reliability | R-007 | 6 | Dev | Concurrency testing |
| Memory decay integrity | Data | R-008 | 4 | Dev | Corruption detection |
| Multi-user memory isolation | Security | R-009 | 5 | Dev | Cross-tenant tests |
| Image generation timeouts | Performance | R-010 | 4 | Dev | Timeout handling |
| WebSocket reconnection | Reliability | R-011 | 4 | Dev | Reconnection logic |
| Plugin loader validation | Tech | R-012 | 3 | Dev | Error boundaries |

**Total P1**: 30 tests, ~25-35 hours

### P2 (Medium) - Run nightly/weekly

**Criteria**: Secondary features + Low risk (1-2) + Edge cases

| Requirement | Test Level | Test Count | Owner | Notes |
| ----------- | ---------- | ---------- | ----- | ----- |
| Avatar caching efficiency | Performance | 3 | Dev | Cache hit rates |
| Non-English speech recognition | Quality | 4 | Dev | Multi-language |
| Visual provider rate limiting | Performance | 3 | Dev | Rate limit edge cases |
| Log volume management | Ops | 2 | Dev | Storage thresholds |

**Total P2**: 12 tests, ~8-12 hours

### P3 (Low) - Run on-demand

**Criteria**: Nice-to-have + Exploratory + Performance benchmarks

| Requirement | Test Level | Test Count | Owner | Notes |
| ----------- | ---------- | ---------- | ----- | ----- |
| Exploratory UI/UX testing | E2E | 4 | QA | User flows |
| Benchmark suite | Performance | 6 | Dev | Performance baselines |
| Chaos engineering | Reliability | 4 | Dev | Failure injection |

**Total P3**: 14 tests, ~7-10 hours

---

## Execution Order

### Smoke Tests (<5 min)

**Purpose**: Fast feedback, catch build-breaking issues

- [ ] Agent creation basic flow (30s)
- [ ] Memory storage/retrieval (45s)
- [ ] Social arbiter basic routing (30s)
- [ ] WebSocket connection (30s)

**Total**: 4 scenarios

### P0 Tests (<15 min)

**Purpose**: Critical path validation

- [ ] Memory leak detection suite (5 min)
- [ ] Message latency under load (5 min)
- [ ] Security: prompt injection tests (3 min)
- [ ] Night cycle monitoring (2 min)

**Total**: 26 scenarios

### P1 Tests (<45 min)

**Purpose**: Important feature coverage

- [ ] Voice latency suite
- [ ] Concurrency tests
- [ ] Multi-user isolation

**Total**: 30 scenarios

### P2/P3 Tests (<60 min)

**Purpose**: Full coverage, benchmarks

- [ ] Performance benchmarks
- [ ] Chaos engineering
- [ ] Exploratory tests

**Total**: 26 scenarios

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
| -------- | ----- | ---------- | ----------- | ----- |
| P0 | 26 | 1.5 | 30-40 | Performance, security focus |
| P1 | 30 | 1.0 | 25-35 | Standard coverage |
| P2 | 12 | 0.5 | 6-12 | Simple scenarios |
| P3 | 14 | 0.25 | 3-5 | Exploratory |
| **Total** | **82** | **-** | **70-100** | **~3-4 weeks** |

### Prerequisites

**Test Data:**

- `ConversationFixture` - Long-running conversation factory (100+ turns)
- `MultiUserFixture` - Concurrent user simulation (50+ users)
- `MemoryStateFixture` - Memory state for decay testing

**Tooling:**

- `k6` or `locust` for load testing
- `memory_profiler` for leak detection
- `pytest-timeout` for latency testing
- `chaos mesh` or manual fault injection

**Environment:**

- Staging environment with production-like load
- Load testing infrastructure
- APM/monitoring access (Datadog/New Relic)

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths**: ≥80%
- **Security scenarios**: 100%
- **Business logic**: ≥70%
- **Edge cases**: ≥50%
- **Performance scenarios**: ≥60% (currently ~10%)
- **Scalability scenarios**: ≥50% (currently ~0%)
- **Reliability scenarios**: ≥70% (currently ~50%)

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] Security tests (SEC category) pass 100%
- [ ] Performance targets met (PERF category)
- [ ] Memory leak tests pass (R-002)
- [ ] Load tests pass (R-001, R-003)

---

## Mitigation Plans

### R-001: Message latency >2s under load (Score: 9)

**Mitigation Strategy:** Implement load testing suite with k6/locust, establish latency SLAs, optimize caching layer
**Owner:** Dev Team
**Timeline:** 2026-03-15
**Status:** Planned
**Verification:** Load tests show <500ms p95 latency with 50 concurrent users

### R-002: Memory leak in long-running conversations (Score: 9)

**Mitigation Strategy:** Implement memory profiling in CI, add heap snapshot comparisons, fix identified leaks
**Owner:** Dev Team
**Timeline:** 2026-03-01
**Status:** Planned
**Verification:** 24-hour conversation test shows <100MB growth

### R-003: Database connection pool exhaustion (Score: 6)

**Mitigation Strategy:** Configure connection pooling, add rate limiting, implement circuit breakers
**Owner:** Dev Team
**Timeline:** 2026-03-15
**Status:** Planned
**Verification:** Load test with 100+ concurrent users passes

### R-004: Night cycle consolidation fails silently (Score: 6)

**Mitigation Strategy:** Add monitoring alerts, implement retry logic, add data validation
**Owner:** Dev Team
**Timeline:** 2026-02-28
**Status:** Planned
**Verification:** Night cycle tests verify all consolidation steps complete

### R-005: Agent memory injection via prompt (Score: 6)

**Mitigation Strategy:** Implement input sanitization, add LLM guardrails, security review
**Owner:** Dev Team
**Timeline:** 2026-02-28
**Status:** Planned
**Verification:** Prompt injection test suite passes 100%

---

## Assumptions and Dependencies

### Assumptions

1. Staging environment can replicate production load
2. Team has access to APM/monitoring tools
3. k6 or locust can be integrated into CI pipeline
4. Performance testing infrastructure available

### Dependencies

1. Load testing tools (k6/locust) - Required by 2026-03-01
2. Monitoring/alerting for night cycle - Required by 2026-02-28
3. Security review for prompt injection - Required by 2026-02-28

### Risks to Plan

- **Risk**: Limited expertise in performance testing
  - **Impact**: Delays in closing performance gaps
  - **Contingency**: External consultant or training

---

## Follow-on Workflows (Manual)

- Run `*atdd` to generate failing P0 tests (separate workflow)
- Run `*automate` for broader coverage once implementation exists
- Run performance test design workflow for detailed load testing plan

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: _____________ Date: _____________
- [ ] Tech Lead: _____________ Date: _____________
- [ ] QA Lead: _____________ Date: _____________

**Comments:**

---

## Interworking & Regression

| Service/Component | Impact | Regression Scope |
| ----------------- | ------ | ---------------- |
| **Memory Service** | Core - all epics depend | test_memory.py, test_graph_memory.py |
| **Social Arbiter** | Epic 3, 6 - routing | test_social_arbiter.py |
| **Voice Pipeline** | Epic 5 - latency sensitive | test_voice_recognition.py |
| **Visual Service** | Epic 8 - external provider | test_visual_provider.py |
| **Spatial API** | Epic 9 - location tracking | test_location_tracking.py |

---

## Appendix

### Current Test Files by Epic

| Epic | Unit Tests | Integration Tests | E2E Tests | API Tests |
| ---- | ---------- | ----------------- | --------- | --------- |
| 1 | 4 | 2 | 0 | 1 |
| 2 | 8 | 3 | 0 | 1 |
| 3 | 12 | 4 | 0 | 2 |
| 4 | 6 | 2 | 0 | 1 |
| 5 | 8 | 2 | 0 | 1 |
| 6 | 10 | 4 | 0 | 1 |
| 7 | 8 | 3 | 0 | 2 |
| 8 | 8 | 2 | 1 | 2 |
| 9 | 8 | 3 | 0 | 2 |
| 10 | 0 | 0 | 0 | 0 |
| 11 | 0 | 0 | 0 | 0 |
| 13 | 8 | 4 | 0 | 1 |
| 14 | 2 | 1 | 0 | 0 |

### Coverage Summary by Category

| Category | Current Coverage | Target Coverage | Gap |
| -------- | ---------------- | --------------- | ----|
| Functional | 60% | 80% | 20% |
| Performance | 10% | 60% | 50% |
| Scalability | 0% | 50% | 50% |
| Reliability | 50% | 70% | 20% |
| Security | 40% | 100% | 60% |

### Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection
- `test-priorities-matrix.md` - P0-P3 prioritization

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `_bmad/tea/testarch/test-design`
**Version**: 4.0 (BMad v6)
