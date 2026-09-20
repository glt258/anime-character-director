# Style Reference Contract v1

Local character-art references are optional visual evidence, not a new source
of character identity. They may shape rendering, facial and hair treatment,
body presentation, silhouette language, costume structure, ornament density,
material handling, color organization, and overall visual packaging in space
the user did not lock.

The ownership order is immutable:

```text
Explicit User Constraint > Reference-derived Style Preference > AI Choice
```

Therefore a reference cannot replace an explicitly requested hair length,
body type, footwear, legwear, palette, pose, background, or non-human-feature
constraint. A strong game tendency must be adapted, weakened, or dropped when
it conflicts with the current user request.

The system must not deliberately clone a reference character's exact face,
hairstyle, costume, emblem, accessory combination, or identity. The selected
set exists to expose a game's visual language rather than to reproduce one
character.

The runtime resolves references once, compiles this policy into the prompt,
and emits a backend-neutral `CompiledImageRequest`. When the local bundle is
missing or invalid, the request contains no reference paths and remains the
original YAML-only/text-only flow.
