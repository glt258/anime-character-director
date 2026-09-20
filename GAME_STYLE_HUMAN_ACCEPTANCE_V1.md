# GAME STYLE HUMAN ACCEPTANCE V1

These are text/UI acceptance scenarios. They do not call image generation and
do not change the released version.

## HA-GS-01 — Global default compatibility

- Start QUICK or AI_DECIDE without a game-style request.
- Confirm `game_style_id = null`.
- Confirm the global contract remains `CONTEMPORARY_COMMERCIAL_GACHA_ANIME`.
- Confirm no game-specific fragment appears.

## HA-GS-02 — Same character with Genshin

- Use a fixed character specification.
- Select `原神` / `Genshin Impact`.
- Confirm hair, eyes, body, clothing, palette, footwear, pose, and concept are unchanged.
- Confirm only the four reviewed rendering rules are added.

## HA-GS-03 — Same character with ZZZ

- Reuse the exact HA-GS-02 character specification.
- Select `绝区零` / `ZZZ`.
- Confirm the character block remains identical.
- Confirm the fragment uses softened-edge, gradient-dominant, medium-detail rendering language.

## HA-GS-04 — USER_DECIDE BACK from WuWa to NTE

- In USER_DECIDE, select `鸣潮` / `Wuthering Waves`.
- Continue to GENERATION_READY, then use BACK to reopen Visual Preference Gate.
- Change only `参考游戏画风` to `异环` / `NTE`.
- Confirm the character fields remain locked/preserved and the final fragment changes to NTE's three rules.

## HA-GS-05 — Explicit content preservation

- Request: `粉色长发 + 运动鞋 + 不穿丝袜 + 高性感等级`.
- Select any supported game style.
- Confirm no game profile changes hair, footwear, legwear, sexiness, body, clothing, palette, pose, or nonhuman traits.
- A conflicting explicit rendering property must weaken or drop the conflicting game rule.

## HA-GS-05A — USER PROMPT SUPREMACY for character content

- Use a game reference whose visual corpus trends toward mature, fuller-bodied
  characters.
- Explicitly request a petite, youthful character.
- Confirm the body and age presentation remain the user's values; only
  compatible rendering language may be inherited from the profile.

## HA-GS-05B — USER PROMPT SUPREMACY for rendering properties

- Explicitly request soft, low-contrast lighting.
- Select a profile that prefers stronger contrast or a stronger shading mode.
- Confirm the explicit lighting preference wins and the conflicting profile
  rule is removed, while non-conflicting rendering deltas remain available.

## HA-GS-06 — Unsupported game fallback

- Request `崩坏：星穹铁道` as a rendering reference.
- Confirm the UI explains that no verified Style Profile is available.
- Confirm the original request is retained for audit and the effective profile is `null`.
- Confirm the run does not crash and does not silently map to another game.

## HA-GS-07 — Legacy checkpoint resume

- Resume a checkpoint created before `game_style_id` existed.
- Confirm it migrates in memory to `null` without error.
- Confirm BACK/resume preserves the old character choices and uses the global rendering contract.

Acceptance evidence should include the persisted checkpoint, final PromptBundle,
debug trace, and the unchanged normalized character block hash.
