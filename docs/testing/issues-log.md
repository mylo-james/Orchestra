# Testing Issues Log

Date: 2025-08-25

Purpose: Track discrepancies between docs and reality, current test failures, and concrete fixes aligned with our testing guides and PRD to avoid circular work.

## Coverage and Suite Status

- Observed via `make coverage`:
  - Total tests collected: 1494
  - Failures: 6 (all in `tests/unit/temporal/activities/test_learning.py`)
  - Total coverage: 84.58% (fails gate `--cov-fail-under=90`)
  - Lowest-covered file: `orchestra/temporal/workflows/knowledge_sharing.py` at 19%

## Documentation Mismatches (Update Needed)

1) Temporal Workflow Testing Guide (`docs/testing/temporal-workflow-testing-guide.md`)
   - Previously listed outdated stats and legacy module paths.
   - Fixed: Updated module paths to `orchestra/temporal/...` and added run-path stub guidance; removed outdated hard numbers.

2) Coverage Considerations had stale numbers.
   - Fixed: Clarified policy (90% gate) and removed stale snapshot numbers.

3) Story 2.3 file paths (`docs/stories/2.3.cross-persona-knowledge-sharing.md`)
   - Fixed: Corrected file locations to `orchestra/temporal/...` and current test paths.

## Test Failures and Root Causes

File: `tests/unit/temporal/activities/test_learning.py`

1) Floating point strict-equality assertions
   - Failures:
     - `test_calculate_outcome_confidence_success` expecting `1.0` got `0.9999999999999999`.
     - `test_calculate_outcome_confidence_error` expecting `0.9` got `0.8999999999999999`.
   - Root cause: `_calculate_outcome_confidence` sums floats; result subject to FP rounding.
   - Fix (code): Round/clamp in helper: `return min(1.0, round(base_confidence, 10))`.
   - Alternative (tests): Use `pytest.approx`. Per docs “test behavior, avoid brittle exact float checks,” prefer code-side rounding for determinism.

2) Model validation vs helper validation
   - Failure: `test_validate_outcome_event_invalid` constructs `OutcomeEvent` with `confidence_score=1.5` and expects `_validate_outcome_event(...) is False`, but dataclass `__post_init__` raises `ValueError` first.
   - Root cause: Strong invariants in `orchestra/models/learning.py` (expected per docs Model Tests) conflict with test’s expectation to “soft-fail”.
   - Fix (tests): Expect `with pytest.raises(ValueError)` for invalid construction. Keep model invariants.

3) Helper return shape mismatch
   - Failure: `test_calculate_performance_metrics_success` expects `result["persona_id"]` and `result["project_id"]` from `_calculate_performance_metrics(...)`.
   - Root cause: Helper currently returns only `{"success", "metrics", "measurement_period_days"}`.
   - Fix (code): Include `persona_id` and `project_id` in that helper’s return dict to match tests and improve downstream ergonomics.

4) Helper signature mismatch
   - Failure: `test_analyze_performance_trends_success` calls `_analyze_performance_trends("dev", "test-project", historical_data)` but implementation signature is `(metrics: List[Dict], period_days: int)`.
   - Root cause: Divergence between expected usage (persona/history) and current implementation (metrics/period).
   - Fix (code): Make `_analyze_performance_trends` accept both call styles by type-detecting inputs; when called with `(persona_id, project_id, historical_data)` return a dict including `persona_id`, `project_id`, and derived trend metrics. Preserve current usage from `performance_metrics_activity`.

5) Weighted effectiveness calculation
   - Failure: `test_calculate_overall_effectiveness_success` expects ~0.162 but got ~0.054.
   - Root cause: `_calculate_overall_effectiveness` computes weighted values (weights sum to 1.0) but then divides by `len(metrics)`, undercounting by ~3x.
   - Fix (code): Return `sum(weighted_values)` (do not divide by N) since weights already encode averaging.

## Alignment With Testing Guides

- Our workflow tests appropriately mock activities (Approach 1). Some additional shallow tests that import and lightly exercise `orchestra/temporal/workflows/knowledge_sharing.py` with patched `workflow.execute_activity/execute_child_workflow` can safely raise coverage without invoking Temporal runtime, consistent with the guide.
- For floating point assertions, the Testing Strategy recommends avoiding brittle equals; deterministic rounding in helpers is preferred to keep tests simple and stable.
- For model validation, the Model Tests example demonstrates raising on invalid construction, which we will follow by updating the failing test accordingly.

## Action Plan (Ordered)

1) Fix helpers in `orchestra/temporal/activities/learning.py`:
   - `_calculate_outcome_confidence`: round/clamp for deterministic outputs.
   - `_calculate_overall_effectiveness`: remove extra division (use sum of weighted values).
   - `_calculate_performance_metrics`: include `persona_id` and `project_id` in return.
   - `_analyze_performance_trends`: support both `(persona_id, project_id, historical_data)` and `(metrics, period_days)`; include persona/project fields when provided.

2) Update tests in `tests/unit/temporal/activities/test_learning.py`:
   - Change invalid `OutcomeEvent` case to expect `ValueError` during construction (keeps strong invariants).
   - Optionally switch strict float equality to `pytest.approx` (if helper rounding not preferred).

3) Raise coverage for `orchestra/temporal/workflows/knowledge_sharing.py` (currently 19%) to 80%+ by adding unit tests that:
   - Import workflow classes and call `run()` with `workflow.execute_activity/execute_child_workflow` patched to AsyncMocks.
   - Exercise main branches (export vs import, targeting path present vs absent, propagation success vs no transferable patterns, validation with and without rollback).
   - Assert returned dict shapes and key business-rule checks (e.g., warning when `processing_time_ms > 500`).

4) Update docs:
   - Fix outdated numbers in the Temporal guide and align Story 2.3 file locations.

## Expected Outcome

- 6 failing tests pass.
- Overall coverage returns to ≥90%.
- `knowledge_sharing.py` workflow file ≥80% coverage via unit approach without Temporal runtime.

## Good vs Bad Testing Patterns (Patterns Log)

### Good Patterns
- Mock activities directly and assert business outcomes (fast, stable, PRD-aligned).
- Stub the `workflow` module in workflow tests to exercise `run()` branches without Temporal event loop.
- Deterministic handling of floating point results in helpers (round/clamp) to avoid brittle equality.
- Enforce strong model invariants in dataclasses and test invalid construction via `pytest.raises`.
- Validate error paths and rollback branches alongside success paths.
- Keep tests focused on acceptance criteria and observable behavior (not implementation details).

### Bad Patterns
- Instantiating workflow classes and calling `run()` without a Temporal runtime (causes `_NotInWorkflowEventLoopError`).
- Using legacy module paths in tests/docs (e.g., `orchestra.workflows...` instead of `orchestra.temporal...`).
- Strict float equality checks where small FP artifacts are expected; prefer rounding or `pytest.approx`.
- Bypassing dataclass invariants by constructing invalid objects then asserting later validation (should raise on init).
- Over-measuring Temporal internals; focus on business logic rather than infrastructure behavior in unit tests.
