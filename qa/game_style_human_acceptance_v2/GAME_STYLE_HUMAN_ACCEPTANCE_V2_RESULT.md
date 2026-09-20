# GAME STYLE HUMAN ACCEPTANCE v2

日期：2026-09-20
开发仓库：`D:\anime-character-director-release`
运行副本：`C:\Users\30931\.codex\skills\anime-character-director`
source commit：`4347a9c0741048c590f85d415340cd830ed9a30f`

## A. Weakness diagnosis

v1 的主要问题不是游戏名缺失，而是 runtime projection 的 rendering delta 太少、太抽象、位置太弱：规则没有稳定映射到人物主体，global contract 会稀释差异，背景/环境容易成为伪差异，投影器还会把可用 claim 过滤掉。另一个问题是 `BACK` 与 unsupported-style fallback 没有清理或降级旧投影状态。

完整诊断见 [GAME_STYLE_WEAKNESS_DIAGNOSIS.md](../game_style_v2/GAME_STYLE_WEAKNESS_DIAGNOSIS.md)。

## B. Bugfix

- `BACK_FAILURE` 根因：返回时只回退交互状态，未统一清理 delegated/default visual selections、compiled prompt、novelty 与旧 game-style projection，导致旧规则可能残留。
- `FALLBACK_FAILURE` 根因：unsupported style 被写成硬 explicit constraint，但没有可识别 renderer，先触发 coverage failure，无法回到 global rendering。
- 修复：统一 human-selection preservation/invalidation helper；unsupported style 保留 requested metadata 和 `UNSUPPORTED_GAME_STYLE` reason，但不伪装成已识别硬约束，最终回落 Global。

结果：`HA-GS-04 = PASS`；`HA-GS-06 = PASS`。

## C. Rendering Signature v2

每个 profile 声明 15 个 rendering slots，其中 5 个为有效 character-subject rules，0 个 support rules，另外 10 个明确标记 `no_reliable_discriminator`；有效规则总数为 5，符合 5–8 core、0–2 support、总数不超过 10 的投影预算。

| Profile | 有效 runtime rules | 覆盖的 active slots |
|---|---:|---|
| Genshin | 5 | `LINE_CONTOUR`, `INTERNAL_EDGE`, `PRIMARY_SHADOW`, `SECONDARY_GRADIENT`, `DETAIL_FREQUENCY` |
| ZZZ | 5 | `LINE_CONTOUR`, `INTERNAL_EDGE`, `PRIMARY_SHADOW`, `SECONDARY_GRADIENT`, `DETAIL_FREQUENCY` |
| WuWa | 5 | `LINE_CONTOUR`, `INTERNAL_EDGE`, `PRIMARY_SHADOW`, `SECONDARY_GRADIENT`, `DETAIL_FREQUENCY` |
| NTE | 5 | `LINE_CONTOUR`, `INTERNAL_EDGE`, `PRIMARY_SHADOW`, `SECONDARY_GRADIENT`, `DETAIL_FREQUENCY` |

规则全部是人物主体的 HOW；没有把人物身体、服装、鞋、发型、眼睛、性别气质或背景当成 style discriminator。技术审计见 [GAME_STYLE_RENDERING_SIGNATURE_V2_AUDIT.md](GAME_STYLE_RENDERING_SIGNATURE_V2_AUDIT.md)。

## D. Automated tests

- 新增 v2 tests：28 个；`tests/test_game_style_v2.py` 与既有 Game Style tests：`74 passed`。
- checkpoint/BACK、preference preservation：`38 passed`。
- workflow 与 targeted regression：`69 passed`。
- `py -3 -m py_compile runtime/game_style_runtime.py runtime/regional_style_runtime.py runtime/interaction_runtime.py tests/test_game_style_v2.py`：PASS。
- `py -3 -m compileall -q runtime tests`：PASS。
- `git diff --check`：PASS（v1 历史报告的 Markdown hard-break 空格未改动）。
- failures：0。

## E. Git

- D source of truth：实现已 commit 为 `4347a9c0741048c590f85d415340cd830ed9a30f`。
- `origin/main`：push PASS。
- C runtime：仅在 push 成功后通过 `fetch + merge --ff-only` 更新到同一 source commit；没有直接编辑 C 盘 skill 文件。
- 没有 tag、release 或 version bump。
- v1 验收报告、图片与 prompts 保留原样。

## F. Human Acceptance v2

| Gate | 结果 |
|---|---|
| HA-GS-04 BACK | PASS |
| HA-GS-06 unsupported fallback | PASS |
| CHARACTER_PRESERVATION | PASS |
| USER_PROMPT_SUPREMACY | PASS |
| BACKGROUND_CONTROL | PASS |
| POSE_CONTROL | PASS |
| ANATOMY | PASS |

五模式使用同一 character、pose、camera、neutral background 与 lighting intent。用户冲突测试中，game style 的强 contrast tendency 会被 `adapt / weaken / drop`，用户的 soft low-contrast shading 保持优先；`petite / youthful-looking fictional anime character`、`flat sneakers`、`no stockings` 也未被 game style 改写。

## G. Visual discrimination

依据人物主体 rendering，不依据背景变化：

| Mode | 相对 Global | 人物主体差异 |
|---|---|---|
| Genshin | `CLEAR` | 更 firm 的主体轮廓、清晰 shadow blocks、较高频的主体表面细节。 |
| ZZZ | `CLEAR` | 更多软化/溶解的 interior edges、连续 tonal gradients、较大的 quiet intervals。 |
| WuWa | `CLEAR` | 交替的 contour/edge/shadow treatment，以及可见的 secondary detail clusters。 |
| NTE | `SUBTLE` | 局部 edge/shadow 变量与分组细节存在，但主体差异仍接近 Global，不能记为 CLEAR。 |

五张验收图：

- [Global](images/A-global.png)
- [Genshin](images/B-genshin.png)
- [ZZZ](images/C-zzz.png)
- [WuWa](images/D-wuthering.png)
- [NTE](images/E-nte.png)

`CHARACTER_RENDERING_DIFFERENCE = 3/4 CLEAR`，达到 v2 gate；NTE 的 `SUBTLE` 已明确保留，没有偷偷强化 character content。独立 standalone Genshin 草图因背景/配件漂移被拒绝，未纳入验收。

## Final gate

`GAME_STYLE_HUMAN_ACCEPTANCE_V2 = PASS`
`READY_FOR_RELEASE_REVIEW = YES`

这表示可以进入 release review，不表示已执行 release。
