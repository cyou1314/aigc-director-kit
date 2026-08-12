# CineThread Changelog

## [0.2.4] - 2026-08-12

- Added `validate-skill-integration` to cross-check a metadata adapter against a project workflow.
- Added stage ownership, output-contract, evidence-semantics, required-producer, and action-producer validation.
- Added high-confidence public-safety checks for credential fields and values, email addresses, and absolute local or network paths while keeping manual privacy review mandatory.
- Added regression tests, documentation, CI coverage, and one-command public verification coverage for the integrated handoff.

## [0.2.3] - 2026-08-12

- Added `aigc-director-local-skill-adapter`, a strict metadata-only contract for describing the interface between local Skills and CineThread.
- Added `validate-local-skill-adapter`, a sanitized example, schema, documentation, CI coverage, and one-command public verification coverage.
- Kept local Skill source, prompts, paths, assets, credentials, runtime execution, and media QC outside the public adapter boundary.

## [0.2.2] - 2026-08-12

- Added a package version field and safe JSON report export to `verify-examples`, plus `aigc-director-kit --version`.
- Added a structured Verified run feedback Issue Form and a 60-second trial guide for actual user testing.
- Changed CI to test an ordinary non-editable package installation and the installed CLI entrypoint.

## [0.2.1] - 2026-08-12

- Added `verify-examples`, a cross-platform, privacy-safe one-command verification report for every public example.
- Updated the Windows launcher, quick start, contribution guide, feedback template, and CI to use the new verification path.

## [0.2.0] - 2026-08-12

- Added the `aigc-director-skill-workflow` handoff contract and schema.
- Added `validate-workflow` for structural validation and deterministic action dry-runs.
- Added a sanitized multi-Skill workflow example, documentation, and regression tests.
- Added `aigc-director-prompt-pack` validation for global rules and shot-specific prompt deltas.
- Added `aigc-director-qc-report` validation that separates observed evidence from unverified claims.
- Added `aigc-director-runtime-handoff` and `build-runtime-handoff` for optional adapter consumption.
- Improved the Windows example runner with an explicit Python override and common install-path fallback.
- Rebranded the public project as CineThread while retaining the technical package and CLI identifiers.

## [0.1.4] - 2026-08-12

- Added two sanitized cases derived from real local previs forward tests.
- Added regression coverage for the public workflow case set.
- Added a transparent feedback template and maintainer-relationship boundary.

## [0.1.3] - 2026-08-12

- Added a sanitized one-take case derived from a real local previs plan.
- Added CI validation for the new case.

## [0.1.2] - 2026-08-12

- Added a Windows double-click launcher for the public examples.
- Added a no-install quick-start path that runs directly from `src`.
- Added English aliases to the example action catalog so the launcher works reliably across Windows console code pages.

## [0.1.1] - 2026-08-12

- Added a GitHub Actions matrix for Python 3.10–3.13.
- Added a sanitized, reproducible workflow case study.
- Clarified that cross-shot continuity warnings are emitted by `validate-plan`.

## [0.1.0] - 2026-08-12

- Added a standard-library shot-plan validator.
- Added cross-shot entry/exit handoff warnings.
- Added a license-neutral action catalog format and deterministic search.
- Added bounded Chinese/English action-request compilation.
- Added runnable examples and `unittest` coverage.
