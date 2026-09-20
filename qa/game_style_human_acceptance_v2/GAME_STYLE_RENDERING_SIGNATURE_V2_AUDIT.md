# GAME STYLE RENDERING SIGNATURE v2 AUDIT

## Schema audit

- Profile version：`game_style_profile_v2`
- Projection version：`game_style_projection_v2`
- Required slots：12；optional slots：3；每个 profile 共 15 个 slot declarations。
- Active core：每个 profile 5 个；support：0 个；total projected rules：5。
- Strength values：只使用 `strong`、`medium`、`subtle`。
- 每条有效 rule 都有 `slot`、`absolute_instruction`、`contrastive_instruction`、`confidence`、`strength`、`source_claim_ids`、`status`、`tier`。
- 10 个没有可靠区分度的 slots 显式标记 `no_reliable_discriminator`，没有用背景或人物内容填充预算。

## Per-profile audit

| Profile | Active slot count | Core/support/total | Subject HOW discriminator |
|---|---:|---:|---|
| Genshin | 5 / 15 declared | 5 / 0 / 5 | firm contour、clean shadow blocks、restrained gradient、high-frequency detail |
| ZZZ | 5 / 15 declared | 5 / 0 / 5 | softened edges、continuous tonal modeling、quiet detail intervals |
| WuWa | 5 / 15 declared | 5 / 0 / 5 | alternating edge/shadow strategies、visible detail clusters |
| NTE | 5 / 15 declared | 5 / 0 / 5 | controlled multiple strategies、localized grouping；保持 subtle |

## Projection audit

- 用户 preference 先于 game-style tendency。
- 冲突状态只允许 `applied`、`adapted`、`dropped`，并记录 `conflict_reason`。
- unsupported game style 保留 request metadata，回落 Global，不伪造为 Genshin 或其他已知 profile。
- `BACK` 与 game-style replacement 会使旧 projection、compiled prompt 与 novelty artifact 失效。
- Global contract 不重复 game-specific delta；game name 仅保留在 metadata/debug。

## Evidence boundary

本审计只把人物主体的 line/edge/shadow/gradient/detail frequency 视为 rendering evidence。背景、地标、阵营符号、环境叙事、身体、服装、鞋、发型、眼睛与性别气质均不作为 profile discriminator。
