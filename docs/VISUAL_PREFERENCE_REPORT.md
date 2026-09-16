# Visual Preference Report Format

Art Direction selection produces two artifacts:

- `visual_preference_sheet.json` — machine-readable proposals, selections, lock state, audit, and transition history.
- `visual_preference_report.md` — Human-facing choices and reasons.

Each identity section contains:

```text
Recommended
Recommendation reason
Options: id, value, reason, diversity risk
User Override Allowed
AI Delegation Allowed
User Selection
Locked
```

The report must separate `AI ANALYSIS`, `AI RECOMMENDATION`, `HUMAN OPTIONS`, and `HUMAN DECISION`. A Human decision may be a single option, a Mix, Custom input, or explicit delegation to AI. Silence is not delegation.

Optional variables appear under `Current AI Proposal`, `Alternative Suggestions`, and `User Override Allowed`; they are not blocking gates. The report also includes a Human Audit section proving that every identity variable has an explicit decision source.

## Style layers

The machine-readable sheet may also carry `global_rendering_style`, `regional_visual_language`, `regional_visual_language_source`, and `regional_style_override_reason`. The default regional value is `EAST_ASIAN_CONTEMPORARY_GACHA` from policy; a user override is explicit, while an old sheet is migrated in memory with `migrated_default`. Regional visual language is illustration grammar, not ethnicity or costume.

Accepted regional provenance values are `default_style_policy`, `explicit_user_selection`, `explicit_user_override`, `benchmark_delegation`, and `migrated_default`. Migration audits preserve the old artifact version and effective value without rewriting historical JSON. Regional review artifacts also expose expected/perceived language, material and outfit matches, presentation drift, rationale, and detected drift types.

When selected by the Final Design, lower-body identity may be recorded under `lower_body_visual_variables`: exposure strategy, legwear family, leg accessory family, footwear family, foot visibility, reason, style/pose relationships, and repetition risk. Fanservice level does not fill these fields automatically. Actual-image differences are recorded by lower-body grounding review rather than silently simplified.
