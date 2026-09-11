# P5 Anatomy Integrity Report

1. **Anatomy Check position:** after generation and S1 Anime 2D Hard Gate, before normal Human Review.
2. **Mandatory after every generation:** YES.
3. **Hands and fingers checked:** YES — each visible hand is inspected for plausible thumb/finger structure, joints, orientation, wrist connection, and grip.
4. **Extra/missing/fused fingers blocking:** YES when clearly visible and anatomically defective.
5. **Wrists, arms, legs, and feet checked:** YES, including whole-body limb count and continuity.
6. **Can temporal echo bypass anatomy QA:** NO. Intended echo is separated from primary anatomy; malformed primary anatomy still fails.
7. **Is Anatomy Check an aesthetic Gate:** NO. It is technical generation QA.
8. **Is S1 independent:** YES. S1 remains the only visual style hard Gate and is not modified.
9. **Does FAIL allow Technical Repair:** YES, limited to anatomy and accidental duplicated anatomy.
10. **Must repair preserve Character Canon:** YES. Repair keeps Canon, Identity, approved costume, colors, anchor, and pose concept.
11. **Is repair loop limited:** YES, at most two automatic technical repair attempts, then stop with a report for Human Review.
12. **Targeted tests:** `tests/test_anatomy_integrity.py` covers the 23 requested cases in 22 test functions (34 assertions); existing generation/style boundary tests were updated to supply an explicit anatomy report.
13. **Image generated in this phase:** NO.

## Runtime implementation

The runtime now requires an injected `AnatomyCheck` after S1 passes. It stores a lightweight `AnatomyIntegrityReport` in `RunRecord`, transitions through `ANATOMY_CHECKED`, blocks missing reports, maps blocking defects to `ANATOMY_REJECTED`, and holds `UNCERTAIN` for explicit review. No image analyzer or external provider was added.

## Boundary

`Anatomy Integrity Check` is separate from S1: it answers “does the generated visible anatomy contain a clear technical defect?”, not “is the image 2D anime?” It does not judge beauty, appeal, identity, costume preference, composition preference, or commercial quality.

> A beautiful character with broken hands is not a finished character.
>
> Anatomy integrity is a technical requirement, not an aesthetic preference.
>
> Temporal effects may distort presentation, but they may not excuse malformed primary anatomy.
>
> Repair the anatomy. Preserve the identity.
