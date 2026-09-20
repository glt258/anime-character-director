# GAME STYLE HUMAN ACCEPTANCE v1 RESULT

日期：2026-09-20  
验收运行副本：`C:\Users\30931\.codex\skills\anime-character-director`  
D 开发仓库：`D:\anime-character-director-release`  
验收基线：`c632e13befc2069886ea63ca33880584568532a5`  
结论：`GAME_STYLE_HUMAN_ACCEPTANCE = FAIL`  
发布准备：`READY_FOR_RELEASE_REVIEW = NO`

本轮没有修改运行时代码、版本号、tag、release、research dataset 或 profile。五张图由内置 `imagegen` 生成；runtime 证据和实际生图 prompt 已一并归档。

## Workflow

| Case | 结果 | 证据 / 失败分类 |
|---|---|---|
| HA-GS-01 Global Default | PASS | `GENERATION_READY`；`game_style_id = null`；global contract 为 `CONTEMPORARY_COMMERCIAL_GACHA_ANIME` |
| HA-GS-02 Genshin | PASS | `GENERATION_READY`；`game_style_id = genshin_impact`；仅投影 rendering rules |
| HA-GS-03 Zenless Zone Zero | PASS | `GENERATION_READY`；`game_style_id = zenless_zone_zero`；未加入 faction/logo 等角色内容 |
| HA-GS-04 WuWa → BACK → NTE | FAIL | `BACK_FAILURE`：BACK 后自定义 Visual Preference 被清空；只选择 NTE 时仍为 `AWAITING_VISUAL_PREFERENCES`，`game_style_id = null` |
| HA-GS-05 User Prompt Supremacy | PASS | ZZZ projection 保留 `body_style` / `age_presentation`；用户 `soft_low_contrast` 覆盖 `rendering_shading_soft_dominant` |
| HA-GS-06 Unsupported Game | FAIL | `FALLBACK_FAILURE`：HSR 产生 fallback message，但最终 `BLOCKED`，错误为 `EXPLICIT_CONSTRAINT_COVERAGE_FAILED`，没有正常继续到 `GENERATION_READY` |
| HA-GS-07 Old Checkpoint | PASS | 缺失字段迁移为 `game_style_id = null`；audit event 为 `GAME_STYLE_DEFAULT_MIGRATION` |

## Five-way A/B

五个独立 USER_DECIDE custom-direction run 均到 `GENERATION_READY`，explicit coverage 均为 `PASS`，`design_dna = {}`。五组角色块使用同一 hash：`5758921afd5c...e4fd96e58`，说明结构化 Gate 中角色内容未因 Game Style 切换而变化。

| 模式 | `game_style_id` | Character preservation | Rendering difference | Anatomy / pose | 图片 |
|---|---|---|---|---|---|
| A Global | `null` | PASS | 基线 | PASS | [A-global.png](images/A-global.png) |
| B Genshin | `genshin_impact` | PASS | SUBTLE_DIFFERENCE：更清晰的主边缘、高频材质细节、混合明暗 | PASS | [B-genshin.png](images/B-genshin.png) |
| C ZZZ | `zenless_zone_zero` | PASS | SUBTLE_DIFFERENCE：更软边缘、连续渐变、中等局部细节 | PASS | [C-zzz.png](images/C-zzz.png) |
| D WuWa | `wuthering_waves` | PASS | SUBTLE_DIFFERENCE：高细节密度、半硬边缘、混合阴影与大气深度 | PASS | [D-wuthering.png](images/D-wuthering.png) |
| E NTE | `neverness_to_everness` | PASS | SUBTLE_DIFFERENCE：软边缘、软明暗、高但受控的细节组织 | PASS | [E-nte.png](images/E-nte.png) |

人工检查结果：五张图均保持粉色肩长发、青绿色眼睛、白/深蓝短夹克、黑色短裤、平底踝靴、无丝袜、无明显非人特征和分腿站姿。双手、四肢、手腕连接、脚部和鞋子均可读，未见交叉腿或明显肢体数量错误。

图像仍出现相同的非核心装饰细节（发饰、项链、服装挂件）以及不同的现代建筑背景；这些没有跨 Game Style 改写角色核心字段，但应在后续人工迭代中作为 `MINOR_DEVIATION` 观察项保留。

### Prompt / checkpoint evidence

- [Global runtime prompt](prompts/global.runtime_prompt.txt) / [imagegen prompt](prompts/global.imagegen_prompt.txt)
- [Genshin runtime prompt](prompts/genshin.runtime_prompt.txt) / [imagegen prompt](prompts/genshin.imagegen_prompt.txt)
- [ZZZ runtime prompt](prompts/zzz.runtime_prompt.txt) / [imagegen prompt](prompts/zzz.imagegen_prompt.txt)
- [WuWa runtime prompt](prompts/wuthering.runtime_prompt.txt) / [imagegen prompt](prompts/wuthering.imagegen_prompt.txt)
- [NTE runtime prompt](prompts/nte.runtime_prompt.txt) / [imagegen prompt](prompts/nte.imagegen_prompt.txt)
- [WuWa → BACK workflow prompt](prompts/user_decide_back_switch.runtime_prompt.txt)
- [Structured workflow summary](workflow_summary.json)

## User Prompt Supremacy

结果：`USER_PROMPT_SUPREMACY = PASS`。

直接 projection 证据：

- 用户的 `body_style = petite` 和 `age_presentation = youthful` 保持不变；
- ZZZ 的 `rendering_shading_soft_dominant` 被列入 `overridden_claim_ids`；
- 用户 `shading_strategy = soft_low_contrast` 没有被 Game Style 覆盖；
- 图像 prompt 明确使用 character lock，再叠加 rendering-only HOW rules。

## Blockers and failure classification

1. `BACK_FAILURE`：BACK 会清掉 `human_custom` 的视觉字段。对于本轮自定义固定角色，重新只选 Game Style 不会自动恢复角色字段；需要再次填写整个 Visual Preference Gate 才能生成最终 NTE。
2. `FALLBACK_FAILURE` / `CHECKPOINT_FAILURE`：不支持的 HSR 请求虽产生默认风格 fallback message，但在 explicit coverage gate 被阻塞，不能按要求继续正常设计流程。
3. `CHARACTER_DRIFT` / `USER_PROMPT_OVERRIDDEN` 观察项：自然语言 extractor 将“不要兽耳”中的“兽耳”误判为正向 `fox_ears`；本轮因此使用结构化 Visual Preference Gate 完成固定角色验收，未在 C 盘修复。

以上问题只记录，不在本轮修改 C 或 D 运行时代码。应在后续 D-side 修复周期中分别补充回归测试，再同步 C 并重新验收。

## Overall

```text
WORKFLOW_ACCEPTANCE   = FAIL
VISUAL_STYLE_ACCEPTANCE = PASS (all four game profiles show credible SUBTLE_DIFFERENCE)
CHARACTER_PRESERVATION = PASS for structured five-way A/B
USER_PROMPT_SUPREMACY = PASS
ANATOMY_ACCEPTANCE     = PASS for the five reviewed images
GAME_STYLE_HUMAN_ACCEPTANCE = FAIL
READY_FOR_RELEASE_REVIEW = NO
```

本轮停止于验收报告，不发布、不打 tag、不提交 release。
