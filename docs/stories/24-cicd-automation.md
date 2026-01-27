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

**Status:** In Progress
**Epic:** 24 - CI/CD Pipeline

## Story
**As a** User,
**I want** the latest validated code to be automatically deployed,
**so that** I can enjoy new features without manual intervention.

## Acceptance Criteria
1. **Docker Build:**
    - CI must verify that `docker compose build` succeeds for all services.
2. **Deploy Script:**
    - Implement `scripts/deploy.sh` to update the local/target environment.
3. **Post-Deploy Health:**
    - The deployment is only considered successful if the `BRAIN` status (heartbeat) returns within 30 seconds.

## Tasks
- [ ] Implement Docker build validation in CI.
- [ ] Create `scripts/deploy.sh`.
- [ ] Implement post-deploy health check script.
