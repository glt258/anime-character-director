# Reviewed Game Style Profiles

These files are packaged runtime inputs for the optional `game_rendering_style`
field. They are derived from the reviewed `game_style_profile_v1` and
`game_style_projection_v1` outputs; the research repository remains the full
evidence store and is not a runtime dependency.

Each profile contains:

- lightweight provenance: `profile_version`, `source_analysis_version`,
  `sample_manifest_version`, and `integration_review_version`;
- a canonical game ID and display name;
- `core_rendering_instructions` and
  `supporting_art_direction_instructions` bounded by `prompt_budget`;
- `claim_id` values used only for audit trace;
- `excluded_global_baseline_claim_ids` to prevent baseline duplication.

`runtime/game_style_runtime.py` is the only production reader. Callers use
`resolve_game_style()` and `project_game_style()` and never parse these YAML
files themselves.
