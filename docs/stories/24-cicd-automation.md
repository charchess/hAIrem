# Story 24.1: Secret Scanning & Static Analysis (CI Gates)

**Status:** Approved
**Epic:** 24 - CI/CD Pipeline

## Story
**As a** Security Officer,
**I want** each commit to be automatically scanned for secrets and code quality issues,
**so that** we don't leak API keys and maintain high coding standards.

## Acceptance Criteria
1. **Gitleaks Integration:**
    - Configure a CI job that runs `gitleaks detect` on the entire repository.
2. **Linting & Types:**
    - Configure CI jobs for `ruff check` and `mypy`.
3. **Blocking Gate:**
    - Any failure in scanning or linting must block the subsequent pipeline steps.

## Tasks
- [x] Create `.github/workflows/ci.yml` (or `scripts/ci_run.sh`).
- [x] Implement Gitleaks configuration.
- [x] Add Ruff and Mypy jobs.

---

# Story 24.2: Automated Regression & E2E Validation

**Status:** Approved
**Epic:** 24 - CI/CD Pipeline

## Story
**As a** Developer,
**I want** my code changes to be validated against all unit tests and a real E2E scenario,
**so that** I can ensure my changes don't introduce regressions.

## Acceptance Criteria
1. **Pytest Suite:**
    - CI must run all 47 tests in `apps/h-core/tests/`.
2. **Master Regression:**
    - CI must execute `scripts/master_regression_v3.py`.
3. **Environment Isolation:**
    - Use a temporary Redis container during the CI run to ensure a clean state.

## Tasks
- [x] Set up CI environment with Redis service.
- [x] Add pytest execution step.
- [x] Add Master Regression execution step.

---

# Story 24.3: Build Integrity & Auto-Deployment

**Status:** Ready for Dev
**Epic:** 24 - CI/CD Pipeline

## Story
**As a** DevOps Engineer,
**I want** the latest validated code to be automatically deployed,
**so that** I can enjoy new features without manual intervention.

## Acceptance Criteria
1. **Docker Build Validation:**
    - CI (`scripts/ci_run.sh`) must verify that `docker compose build` succeeds for both `h-bridge` and `h-core`.
2. **Deployment Script:**
    - Create `scripts/deploy.sh` that performs a zero-downtime (or minimal downtime) update using `docker compose up -d`.
3. **Post-Deploy Health Check:**
    - The deployment is only considered successful if the `/api/agents` endpoint of `h-bridge` returns at least one agent and the `BRAIN` status (heartbeat) is "online" within 30 seconds.

## Tasks
- [x] **Docker CI Integration:** Add `docker compose build --quiet` to `scripts/ci_run.sh`.
- [x] **Deploy Script Implementation:** Create `scripts/deploy.sh` with logic to pull latest (if applicable), rebuild and restart containers.
- [x] **Health Check Tool:** Create `scripts/check_health.py` to poll the Bridge API and verify system readiness.
- [x] **Final Integration:** Update `.github/workflows/ci.yml` or the local CI runner to call the deployment script only if all previous tests pass.

## Dev Notes
- **Endpoints:** Use `GET /api/agents` on `h-bridge` (port 8000).
- **Health logic:** Look for component "brain" with status "online" in the system status messages relayed by the bridge.
- **Environment:** Ensure the script handles `${HA_TOKEN}` and other secrets appropriately via `.env` loading.

## Testing Scenarios
- Run `./scripts/ci_run.sh` and verify it fails if a Dockerfile has a syntax error.
- Run `./scripts/deploy.sh` and verify containers restart.
- Simulate a crash of H-Core and verify the health check script detects the "offline" brain.

## Dev Agent Record
### Agent Model Used
Gemini 2.5 Flash

### Debug Log References
- [2026-01-27] Phase 7 added to `scripts/ci_run.sh`.
- [2026-01-27] Created `scripts/deploy.sh` and `scripts/check_health.py`.
- [2026-01-27] Verified `/api/status` endpoint in `h-bridge` for "BRAIN" heartbeat.

### Completion Notes List
- Docker build validation integrated into CI quality gate.
- Automated deployment script handles container recreation and health validation.
- Health check verifies both agent discovery and core system heartbeat.

### File List
- `scripts/ci_run.sh`
- `scripts/deploy.sh`
- `scripts/check_health.py`
- `apps/h-bridge/src/main.py`
- `.github/workflows/ci.yml`

### Change Log
- Added Docker build integrity check to CI.
- Implemented `/api/status` in H-Bridge to expose component health.
- Added automated deployment and post-deployment health check logic.

### Status
Ready for Review

## QA Results (Story 24.3)

### Review Date: 2026-01-27

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

The implementation of Build Integrity and Auto-Deployment is robust and follows the requirements closely. 
- **CI Integration**: Phase 7 was successfully added to `scripts/ci_run.sh` providing build validation.
- **Deployment**: `scripts/deploy.sh` implements the requested minimal downtime strategy using Docker Compose.
- **Health Check**: `scripts/check_health.py` provides excellent post-deployment validation by checking both agent discovery and system heartbeat (BRAIN status).

### Refactoring Performed

- **File**: `scripts/check_health.py`
  - **Change**: Added environment variable support for `MAX_ATTEMPTS`, `SLEEP_INTERVAL`, and `TIMEOUT`.
  - **Why**: To improve flexibility in different environments (e.g., CI vs Production) where startup times might vary.
  - **How**: Used `os.getenv` with sensible defaults.

### Compliance Check

- Coding Standards: [✓] Shell and Python scripts follow project conventions.
- Project Structure: [✓] Scripts placed in `scripts/` directory as expected.
- Testing Strategy: [✓] Automated health check script acts as a smoke test for deployment.
- All ACs Met: [✓] Build validation, deployment script, and health check all functional.

### Improvements Checklist

- [x] Refactored health check script for better configurability.
- [x] Verified build integrity phase in CI script.
- [x] Validated health check against live local environment.
- [ ] Consider adding a rollback mechanism in `scripts/deploy.sh` if health check fails.
- [ ] Update `.gitleaksignore` to handle false positives in test files to prevent CI blocking.

### Security Review

Deployment script uses Docker Compose which correctly handles secrets via `.env`. No secrets are hardcoded in the scripts. `HA_TOKEN` is passed via environment variables in CI.

### Performance Considerations

Docker build validation uses `--quiet` to reduce log noise. Deployment uses `-d` for background execution. Health check is efficient with a 1-second poll interval.

### Files Modified During Review

- `scripts/check_health.py`

### Gate Status

Gate: PASS → docs/qa/gates/24.3-build-integrity-auto-deployment.yml
Risk profile: docs/qa/assessments/24.3-risk-20260127.md

### Recommended Status

[✓ Ready for Done]