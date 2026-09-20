# GAME STYLE BUGFIX REGRESSION v2

## BACK_FAILURE

### Root cause

`BACK` 只回到了交互 checkpoint，没有统一清除由 delegated/default selection 产生的 visual preference、旧 game-style projection、compiled prompt、final design 与 novelty artifact。因此后续替换 style 时可能读到旧 WuWa/NTE/Genshin rules。

### Regression coverage

- `test_back_game_style_invalidates_old_projection`
- `test_back_wuwa_to_nte_has_no_stale_rules`
- `test_checkpoint_game_style_replacement`

修复后：human-owned selections 保留；delegated/default selections 被清除；派生 artifacts 失效并记录 `game_style_projection_invalidated`。

## FALLBACK_FAILURE

### Root cause

unsupported style request 被当作 hard explicit constraint 写入，但 runtime 没有对应 renderer；`ExplicitConstraintCoverageGate` 因此在 fallback 前失败。

### Regression coverage

- `test_unsupported_hsr_falls_back_global`
- `test_unsupported_style_not_mapped_to_genshin`
- `test_fallback_keeps_requested_style_metadata`

修复后：unsupported request 的 metadata 和 `UNSUPPORTED_GAME_STYLE` reason 保留；不注入伪造 rendering rule；最终 prompt 使用 Global rendering contract。

## User supremacy regression

- `test_user_conflict_drops_style_rule`
- `test_user_conflict_adapts_style_rule`
- `test_user_rendering_override_preserved`
- `test_no_body_style_drift`
- `test_no_clothing_drift`
- `test_no_footwear_drift`
- `test_no_hair_drift`
- `test_no_eye_drift`
- `test_no_sexiness_drift`
- `test_no_nonhuman_drift`

## Automated result

| Scope | Result |
|---|---:|
| Game Style + v2 | 74 passed |
| checkpoint/BACK + preference | 38 passed |
| workflow/regression | 69 passed |
| compileall | PASS |
| git diff --check | PASS |

没有运行完整 pytest；没有 tag、release 或 version bump。
