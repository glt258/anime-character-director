# Design Ownership Policy

## Principle

AI expands the design space, explains trade-offs, and implements the selected direction. It does not silently own the user's aesthetic preferences. Any variable that materially changes who the character is must be proposed visibly and explicitly selected, mixed, customised, or delegated by the Human before Final Design.

## Variable ownership

`USER_OWNED_IDENTITY_VARIABLES` are blocking identity choices:

`hair_color`, `hair_style_family`, `outfit_direction`, `dominant_palette`, `major_accessories`, `body_markings`, `nonhuman_trait_level`, and `background_direction`.

`AI_PROPOSED_OPTIONAL_VARIABLES` are visible, overridable proposals: footwear family, legwear, exposure strategy, legwear family, leg accessory family, foot visibility, gloves, eye color, makeup intensity, nail design, weapon/tool family, pose family, expression family, visible skin level, secondary accessories, asymmetry level, hairstyle ornament, tattoo placement, tail shape/length, ear/horn shape, and material emphasis. They do not block the gate when the Human has no preference.

`AI_IMPLEMENTATION_VARIABLES` are professional execution work: silhouette balance, shape language, negative space, edge language, clothing construction, seams, closures, material hierarchy, fabric behavior, anchor hierarchy, detail density, visual rhythm, color proportion, prop construction, functional plausibility, narrative visualization, foreground/background separation, pose weight, hand gestures, anatomy-safe implementation, line/cel shading, and PromptCompiler formatting.

## Hard rules

- The Visual Preference Sheet must show a recommendation, reasons, alternatives, diversity risk, custom input, and explicit AI delegation for every identity variable.
- `none` is always a valid candidate for `major_accessories` and `body_markings`.
- A demi-human or supernatural premise does not determine trait intensity; expose Level 0–3 and Custom.
- Hair color is not inferred from personality labels. Without an explicit user request, black, near-black, blue-black, charcoal-black, and very dark navy may be candidates, but not the AI's locked recommendation. The runtime rejects such a recommendation.
- Optional proposals are labelled `Current AI Proposal`, `Alternative Suggestions`, and `User Override Allowed`.

## Human Audit Policy

Before `VISUAL_PREFERENCES_LOCKED`, the runtime records each identity variable's selection and source: `user`, `mix`, `custom`, or explicit `ai_delegate`. A recommendation with no recorded source is an implicit decision and blocks Final Design. The audit is stored with the JSON artifact and summarized in the report.

## Runtime boundary

The real gate is implemented by `runtime/visual_preference_runtime.py`. Art Direction selection opens `AWAITING_VISUAL_PREFERENCE_SELECTION`; only explicit decisions or explicit delegation can reach `VISUAL_PREFERENCES_LOCKED`; Final Design and Generation Ready reject earlier states. This is a creative-ownership gate, not an aesthetic quality score or automatic novelty filter.
