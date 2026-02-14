# Story Emergency.1: Fix Background Data-testid

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a QA engineer,
I want the background element to have a proper data-testid attribute,
so that our E2E tests can reliably locate and validate the background component.

## Acceptance Criteria

1. Given the application loads, the background element should have data-testid="background"
2. Given the E2E test runs, it should be able to locate the background using [data-testid="background"]
3. Given the background is found, it should pass all visibility and content validation tests
4. Given the fix is implemented, all background-related E2E tests should pass

## Tasks / Subtasks

- [x] Add data-testid="background" to the primary background layer element (AC: 1)
  - [x] Locate the background element in the HTML structure
  - [x] Add the data-testid attribute to the correct element
  - [x] Verify the element is the one used by the test expectations
- [x] Validate the fix resolves the E2E test failures (AC: 2, 3, 4)
  - [x] Run the E2E test suite to confirm background tests pass
  - [x] Verify background visibility and content validation work
  - [x] Ensure no regressions in other UI components

## Dev Notes

### Technical Context
This is an emergency fix to address critical UI validation failures. The E2E test suite expects `[data-testid="background"]` but the current implementation only has `id="layer-bg"` and `class="layer"`.

### Current Implementation Analysis
- **File Location**: `/apps/h-bridge/static/index.html` line 25
- **Current Element**: `<div id="layer-bg" class="layer"></div>`
- **Test Expectation**: `[data-testid="background"]` (from `/tests/e2e/ui-validations.spec.ts` line 22 & 37)
- **Test Fallback**: The test also accepts `.background` or `.layer-background` but prefers the data-testid

### Architecture Compliance
- **UI Layer**: This is part of the Z-0 Background layer in "The Stage" UI architecture
- **Testing Strategy**: Aligns with the E2E testing approach using data-testid attributes for reliable element selection
- **Component Structure**: Part of the layer-based rendering system (Z-0: Background, Z-10: Agents, Z-20: Data, Z-30: Dialogue)

### Implementation Requirements
1. **Minimal Change**: Add the data-testid attribute without breaking existing functionality
2. **Test Compatibility**: Ensure the element works with both the new data-testid and existing id/class selectors
3. **Performance**: No performance impact - this is a simple attribute addition
4. **Backward Compatibility**: Keep existing id="layer-bg" for any JavaScript that might reference it

### File Structure Notes
- **Target File**: `apps/h-bridge/static/index.html`
- **Line Number**: 25 (primary background layer)
- **Element Context**: 
  ```html
  <!-- Z-0: Background -->
  <div id="layer-bg" class="layer"></div>
  <div id="layer-bg-next" class="layer" style="opacity: 0;"></div>
  ```

### Testing Standards
- **E2E Framework**: Playwright
- **Test Location**: `/tests/e2e/ui-validations.spec.ts`
- **Test Methods**: Uses `page.locator('[data-testid="background"]')` for element selection
- **Validation Criteria**: Element visibility, content presence (background image or color)

### Risk Assessment
- **Low Risk**: Simple attribute addition, no functional changes
- **Test Coverage**: Well-covered by existing E2E test suite
- **Rollback**: Easy to remove if issues arise

### References
- [Source: tests/e2e/ui-validations.spec.ts#Background Tests] - Test expectations and validation logic
- [Source: apps/h-bridge/static/index.html#The Stage Structure] - Current HTML implementation
- [Source: _bmad-output/planning-artifacts/architecture.md#UI Architecture] - Layer-based UI architecture
- [Source: docs/a2ui-spec-v2.md#The Stage] - UI design specifications for "The Living Stage"

## Dev Agent Record

### Agent Model Used

big-pickle (opencode/big-pickle)

### Debug Log References

- E2E Test Failure: Background element not found with data-testid="background"
- Current Implementation: Uses id="layer-bg" instead of data-testid
- Test Location: tests/e2e/ui-validations.spec.ts lines 22, 29, 37

### Completion Notes List

- Identified the exact HTML element needing modification
- Confirmed test expectations and current implementation mismatch
- Verified this is a simple attribute addition with low risk
- Ensured backward compatibility by keeping existing id attribute
- Successfully added data-testid="background" to the layer-bg element
- Verified E2E test for background presence now passes
- Created unit tests to validate the HTML structure
- Confirmed no duplicate data-testid attributes exist

### File List

- `apps/h-bridge/static/index.html` - Primary file modified
- `tests/e2e/ui-validations.spec.ts` - Test file that validates the fix
- `tests/unit/test_background_data_testid.py` - Unit tests created for validation

## Change Log

**2026-02-11 - Background Data-testid Fix Implementation**
- Added `data-testid="background"` attribute to the primary background layer element
- Verified E2E test compatibility - background presence test now passes
- Created comprehensive unit tests to validate HTML structure
- Maintained backward compatibility with existing id="layer-bg" attribute
- No performance impact - simple attribute addition
- Ready for code review