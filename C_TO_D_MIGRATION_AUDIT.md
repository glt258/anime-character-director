# C-to-D Migration Audit

Generated: 2026-09-20 (Asia/Shanghai)

## Repository discovery

| Field | C installed copy | D development repository |
|---|---|---|
| Path | `C:\\Users\\30931\\.codex\\skills\\anime-character-director` | `D:\\anime-character-director-release` |
| Role | Installed/runtime copy | Development source of truth |
| Remote | `https://github.com/glt258/anime-character-director.git` | `https://github.com/glt258/anime-character-director.git` |
| Branch | `main` | `main` |
| Final HEAD | `892da61af1a489a3977d04ea149433f75b049968` | `892da61af1a489a3977d04ea149433f75b049968` |

The remotes are identical. Before migration, D was at
`6c2cd1e9dfa2a2ebe5b128752eab2a532a5d2120`; that commit was the common base
and C was 15 linear commits ahead. D had no local modifications, additions, or
deletions. C had eight tracked modifications and ten untracked development
files.

## Divergence and classification

The 15 committed C-only commits were fast-forwarded into D. Their historical
diff covered 126 paths (`26,639` insertions and `171` deletions), including the
runtime, schemas, tests, documentation, examples, and reviewed assets already
present in C. No merge conflict occurred.

The pre-migration C working-tree changes were classified as follows:

### SOURCE_CHANGE / CONFIG_CHANGE

- `runtime/interaction_runtime.py`
- `runtime/natural_language_interaction.py`
- `runtime/regional_style_runtime.py`
- `runtime/visual_context_firewall.py`
- `runtime/visual_preference_runtime.py`
- `runtime/workflow_runner.py`
- `schemas/visual_preference_sheet.schema.json`
- `runtime/game_style_runtime.py`
- `references/game_styles/registry.yaml`
- `references/game_styles/genshin_impact.yaml`
- `references/game_styles/neverness_to_everness.yaml`
- `references/game_styles/wuthering_waves.yaml`
- `references/game_styles/zenless_zone_zero.yaml`

### TEST_CHANGE

- `tests/test_game_style_runtime.py`

### DOCUMENTATION_CHANGE

- `SKILL.md`
- `GAME_STYLE_HUMAN_ACCEPTANCE_V1.md`
- `GAME_STYLE_PROMPT_DIFF_REPORT.md`
- `references/game_styles/README.md`

### Deleted / unknown / runtime-only C working-tree files

None. C contained ignored runtime artifacts (`.pytest_cache`, `runtime/__pycache__`,
and `tests/__pycache__`); none were migrated. The research repository
`D:\\anime-lora-lab` was not copied or made a runtime dependency.

## Migration actions

1. Verified both Git roots, remotes, branches, HEADs, status, logs, and the
   common base before copying anything.
2. Fetched `origin/main` in D and fast-forwarded D from `6c2cd1e` to
   `892da61`, preserving the existing C commit history without creating a new
   commit.
3. Applied the eight tracked C working-tree changes with a binary Git patch and
   `--3way`; all applied cleanly.
4. Applied each of the ten C untracked development files as an individual Git
   patch; all applied cleanly.
5. Added the D-only repository policy and development guard:
   `AGENTS.md`, `scripts/repository_guard.py`, and
   `tests/test_repository_guard.py`.
6. Added explicit USER PROMPT SUPREMACY acceptance documentation and a
   regression test. The D acceptance script now rejects an installed
   `.codex\\skills\\` repository before creating development artifacts.

## Game Style and USER PROMPT SUPREMACY

The reviewed registry, four packaged profiles, resolver/projector, prompt
integration, Visual Preference Gate migration, workflow/checkpoint/BACK
handling, fallback behavior, provenance, and targeted tests are present in D.
The runtime consumes only the lightweight packaged profiles; raw research
images, observations, inventories, and evidence JSON remain in
`D:\\anime-lora-lab`.

The formal D policy now states that explicit user semantic and visual
instructions outrank Game Style. It covers both character content and
rendering properties, including the petite/youthful-versus-mature-profile and
soft-low-contrast-lighting-versus-stronger-profile examples.

## Verification

- `py -3` AST parse of 11 changed Python files: passed.
- `git diff --check` and `git diff --cached --check`: passed.
- `py -3 -m pytest -p no:cacheprovider tests/test_game_style_runtime.py tests/test_repository_guard.py -q`: **47 passed**.
- Targeted style, interaction, preference, workflow, Game Style, and guard
  tests (`tests/test_regional_style_runtime.py`,
  `tests/test_interaction_runtime.py`,
  `tests/test_visual_preference_runtime.py`,
  `tests/test_workflow_runner.py`,
  `tests/test_explicit_user_constraint_contract.py`,
  `tests/test_game_style_runtime.py`,
  `tests/test_repository_guard.py`): **158 passed**.
- Every pre-migration C development path exists in D. With line-ending
  normalization ignored, the only intentional semantic differences between
  those C paths and D are the added USER PROMPT SUPREMACY acceptance scenario
  and its regression test.

## Final state

- `C development files detected`: 18 working-tree paths, all present in D.
- `Migrated files`: all 18 C development paths plus the D policy/guard files.
- `Merged conflicts`: 0.
- `Skipped runtime-only files`: C ignored caches and Python bytecode only.
- `Unmigrated development changes`: 0.
- D is cleanly reviewable and ready to commit; no commit was created by this
  migration.
- GitHub push: **NO**.
- Release/tag: **NO**.
- C changes were not deleted or reset; C remains an installed copy with its
  original uncommitted changes preserved for the later post-push resync.

## Rollback

Before commit, revert only the staged D paths or restore D from the prior
`6c2cd1e9dfa2a2ebe5b128752eab2a532a5d2120` commit after preserving this audit.
Do not clean or reset the C copy; its original worktree changes are the
migration source and remain available for comparison.
