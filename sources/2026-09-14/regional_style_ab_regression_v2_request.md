---
title: Character Archetype Regional Style A/B Regression v2 Request
ingested: 2026-09-14
wiki_pages:
  - wiki/experiments/regional-style-ab-regression-v2.md
  - wiki/experiments/benchmark-status.md
  - wiki/roadmap/current.md
---

# anime-character-director — Character Archetype Regional Style A/B Regression v2

继续当前 `anime-character-director` 项目。

当前状态：

`REGIONAL_STYLE_LAYER_IMPLEMENTED_PENDING_HUMAN_REVIEW`

Human Review 结论：

# Regional Visual Language Layer APPROVED FOR REGRESSION TEST

允许进入下一阶段：

# Character Archetype Regional Style A/B Regression v2

本轮目标不是继续开发 Skill。

本轮要验证：

> 新加入的 `EAST_ASIAN_CONTEMPORARY_GACHA`
> Regional Visual Language Layer，
> 是否真正改变实际生成图片，
> 而不是只让 schema / prompt / tests 看起来正确。

---

# 一、首先确认 Test Discovery

在任何 `$imagegen` 调用之前：

检查当前仓库 pytest discovery。

需要确认：

- 实际发现多少 test files
- 实际发现多少 tests
- 是否存在多个 tests 目录
- 是否因为工作目录 / pytest config 导致部分历史测试未发现
- 是否存在此前阶段测试文件但本轮 full pytest 没有执行

因为历史开发阶段曾出现：

- 48 tests
- 31 Lower-Body related tests
- 32 Regional runtime tests
- 当前报告 full pytest 37 tests

这不一定是 bug，

但必须解释。

输出：

`test_discovery_audit.md`

记录：

- pytest rootdir
- config file
- collected tests
- skipped tests
- relevant test directories
- 是否存在未被收集的历史测试

如果只是 suite 重组 / fixtures 合并：

记录即可。

如果发现关键 regression tests 实际没有被发现：

先修 test discovery，

再开始 benchmark。

不要为了凑数字重复测试。

---

# 二、Benchmark 核心原则

这是：

# A/B REGRESSION

A：

旧版 Skill 生成的六张失败图片。

状态：

`NEGATIVE_REGRESSION_FIXTURES`

B：

升级 Regional Visual Language 后，

使用：

# 完全相同的六个高层角色输入

重新从零生成的新图片。

禁止为了让新版更容易 PASS：

- 修改角色输入
- 改人物性格
- 改 benchmark archetype
- 加额外人类美术指导
- 手动指定发色
- 手动指定服装
- 手动指定体型
- 手动指定背景
- 偷偷加入具体游戏名
- 针对旧图逐张写 corrective prompt

唯一应该产生系统性变化的主要因素：

# Skill 本身已经升级。

---

# 三、禁止旧图作为 Image Reference

旧六图只能用于：

- human-labeled negative fixture
- post-generation comparison
- drift taxonomy
- A/B report

严禁：

- image-to-image
- reference image
- style reference
- visual conditioning

新图必须：

# FROM SCRATCH

---

# 四、Global / Regional / Character 三层必须真正进入 Generation

每次生成前保存：

`style_resolution.json`

至少包含：

## Global Rendering Medium

`CONTEMPORARY_COMMERCIAL_GACHA_ANIME`

## Regional Visual Language

`EAST_ASIAN_CONTEMPORARY_GACHA`

source：

`benchmark_delegation`
或当前 benchmark 正确 provenance。

## Character Visual Style

由每个 Case 独立决定。

同时记录：

PromptCompiler 最终三个 section。

---

# 五、Prompt Injection Audit

每个 Case 生成前检查 compiled prompt：

必须存在：

## GLOBAL RENDERING MEDIUM

## REGIONAL VISUAL LANGUAGE

## CHARACTER VISUAL STYLE

Regional section 必须真正包含：

- anime-first facial abstraction
- restrained realistic facial planes
- East-Asian contemporary commercial gacha grammar
- stylized anime anatomy
- commercial playable-character presentation
- non-western-superhero body grammar
- non-western-fantasy-concept rendering guidance

但不要只是：

`east asian anime style`

这种 tag。

---

# 六、Lower-Body Patch 同时保持启用

这也是第一次验证：

Regional Layer
+
Lower-Body Diversity Patch

是否能同时工作。

Regional Style 不允许把所有角色重新拉回：

- trousers + boots
- long skirt + boots
- fully covered legs

Lower-body design 继续正常参与：

- exposure
- legwear
- stockings
- tights
- leg accessories
- barefoot
- sandals
- open footwear
- unusual footwear

但不要为了展示新功能：

强行给六个人各塞一种。

仍然：

# CHARACTER FIT FIRST

---

# 七、本轮绝对不要 Cherry-Pick

每个 Case：

# EXACTLY ONE FIRST-PASS IMAGE

不要：

- batch 4 images
- 选最好的一张
- 自动重抽
- 自动 repair
- regenerate until pass

即使图片失败：

也保留。

本轮测：

# FIRST-PASS SYSTEM RELIABILITY

只有以下情况可以重新调用生成：

- API / backend technical failure
- 文件损坏
- 生成完全中断
- 没有返回有效图片

美术失败：

# 不允许重抽。

---

# 八、六个 Case 输入保持原样

---

# CASE A — Young Adult Male / Social Trickster

输入：

> 设计一个年轻成年男性二游可玩角色。
> 明确是成年人。
> 性格外向、轻佻、嘴很快、擅长和人打交道。
> 有一点让人不完全放心的魅力，但不是反派。
> 不预设职业。
> 不预设发色、服装或武器。
> 所有视觉变量由 AI 决定。

旧版主要失败模式：

- Western anime male
- desert rogue / prince shortcut
- western facial construction
- generic fantasy RPG outfit

注意：

这些只是：

# POST-HOC COMPARISON LABELS

不要把这些旧失败描述注入新 Character Design prompt。

否则 A/B 不公平。

---

# CASE B — Mature Adult Male / Pressure

输入：

> 设计一个成熟成年男性二游可玩角色。
> 沉稳，有明显压迫感。
> 不需要冷酷。
> 不预设职业。
> 不要求西装。
> 不要求黑发。
> 不要求军人。
> 所有视觉变量由 AI 决定。

旧失败：

- western fantasy brute
- giant muscular male
- superhero-like body mass
- silver-haired warrior shortcut

同样：

不要把这些描述注入新设计 prompt。

只用于最终比较。

---

# CASE C — Androgynous Adult Female

输入：

> 设计一个成年女性角色。
> 整体气质帅气、中性、干练。
> 保持明确成年女性身份。
> 不要求短发。
> 不要求 techwear。
> 不要求平胸。
> 不要求裤装。
> 所有视觉变量由 AI 决定。

旧失败：

- androgyny weak
- pseudo-oriental costume
- character-sheet presentation
- western-ish rendering

---

# CASE D — Petite Adult Female

输入：

> 设计一个明确成年女性角色。
> 身材娇小、体型紧凑。
> 明确不是儿童、不是未成年少女。
> 不预设性格。
> 不预设服装。
> 所有视觉变量由 AI 决定。

继续执行：

`ADULT_MATURITY_GATE`

Regional Style 不能：

为了 anime 化，

把成年人画成未成年少女。

---

# CASE E — Partial Beast Adult

输入：

> 设计一个成年可玩角色。
> 人形主体。
> 只有少量兽化特征。
> 可以包括耳朵、尾巴、瞳孔、局部皮肤或其他小型非人特征。
> 不能 furry。
> 不能全身兽化。
> 不预设具体动物。
> 不预设性别表达强弱。
> 所有视觉变量由 AI 决定。

旧版局部成功：

没有直接 generic catgirl 化。

但整体失败：

- concept-art feel
- insufficient commercial gacha presentation
- weak biological integration

不要因此强制避开 aquatic。

让新版重新自主决定。

---

# CASE F — Strong Adult Female

输入：

> 设计一个成年女性可玩角色。
> 她身体力量很强。
> 有明显可靠感和力量感。
> 允许有明显女性曲线。
> 不要求运动员。
> 不要求肌肉女。
> 不要求胖。
> 不要求制服。
> 所有视觉变量由 AI 决定。

注意：

这是：

# Character Archetype Benchmark Case F

不是之前 Visual Aesthetic Benchmark 中已经 `HUMAN_ACCEPTED` 的：

`F — Warm Gravity`

两个 F 完全不同。

严禁混用 artifact、设计或图片。

---

# 九、Case F Body Proportion

继续使用当前 Body Proportion decomposition。

至少记录：

- frame
- height_read
- shoulder_width
- bust_prominence
- waist_definition
- hip_width
- back_strength
- thigh_build
- calf_proportion
- muscle_visibility
- leg_length

目标：

真正测试 Regional Layer 是否能避免：

`strong female -> western Amazon / bodybuilder`

---

# 十、设计阶段不要读取旧图具体视觉特征

设计 A–F 新角色时：

不要让 Character Designer 读取：

- old hair color
- old outfit
- old palette
- old pose
- old background

否则不是重新泛化。

旧 fixture 只能进入：

# AFTER NEW IMAGE GENERATED

的 A/B comparison。

---

# 十一、生成目录

新建：

`D:/benchmark/outputs/character_archetype_regional_ab_v2_20260914/`

结构：

- `case-A-young-male/`
- `case-B-mature-male/`
- `case-C-androgynous-female/`
- `case-D-petite-adult-female/`
- `case-E-partial-beast-adult/`
- `case-F-strong-adult-female/`
- `comparison/`
- `regional_ab_report.md`
- `regional_style_gallery.md`

---

# 十二、每个 Case 保存

至少：

- `character_input.json`
- `character_plan.json`
- `art_direction.json`
- `visual_preferences.json`
- `final_design.json`
- `body_proportion.json`
- `style_resolution.json`
- `compiled_prompt.json`
- `prompt_audit.json`
- `generated-v1.png`
- `actual_visual_features.json`
- `regional_style_review.json`
- `global_gacha_review.json`
- `archetype_review.json`
- `lower_body_review.json`
- `anatomy_review.json`
- `genericness_review.json`

---

# 十三、Actual Image Review

所有评价必须看：

# ACTUAL IMAGE

不能因为：

Prompt 中存在 East-Asian style

就判：

Regional PASS。

---

# 十四、Regional Style Review

每张必须实际判断：

## Face

- anime-first abstraction?
- nose restraint?
- lip restraint?
- jaw/chin anime grammar?
- eye construction?
- maturity preserved?

## Body

- anime proportion?
- superhero massing?
- western comic anatomy?
- muscle treatment?
- silhouette?

## Outfit

- modern commercial gacha design?
- generic western RPG?
- pseudo-oriental fantasy?
- character-specific?

## Material

- anime commercial polish?
- western painterly concept rendering?
- muddy material?

## Presentation

- playable character?
- final commercial illustration?
- character sheet?
- concept board?
- portfolio art?

---

# 十五、Regional Drift 分类

检查：

- `WESTERN_ANIME_STYLE_DRIFT`
- `WESTERN_FANTASY_CONCEPT_DRIFT`
- `WESTERN_SUPERHERO_ANATOMY_DRIFT`
- `GENERIC_FANTASY_RPG_DRIFT`
- `PSEUDO_ORIENTAL_FANTASY_DEFAULT`
- `CHARACTER_SHEET_PRESENTATION_DRIFT`
- `REGIONAL_STYLE_INFANTILIZATION`

结果必须基于图片。

---

# 十六、关键 Human-Level Question

每张都必须回答：

> 如果完全不看 prompt、不看报告、不看角色设定，
> 只看图片，
> 它第一眼是否像一款中日韩/国产现代商业二游里的可玩角色？

结果：

- STRONG YES
- YES
- BORDERLINE
- NO

这个字段命名：

`blind_regional_gacha_read`

这是本轮最重要指标之一。

---

# 十七、不要用具体游戏名称作为判据

不要写：

“因为像某某游戏所以 PASS”。

判断的是：

# Regional Visual Language

而不是：

IP imitation。

---

# 十八、Outfit Family Review

六张完成后检查：

是否仍然大量重复：

- robe
- sash
- hanging cloth
- ornamental belt
- gold trim
- fantasy boots
- cloak

如果：

六张看起来仍像同一 RPG 阵营，

即使 Regional Face 改善：

整体仍然不能判 Strong PASS。

---

# 十九、Background Review

检查：

是否继续：

- giant circles
- giant rings
- generic fantasy platforms
- decorative concept-board backgrounds

如果多个 Case 重复：

记录：

`BACKGROUND_PRESENTATION_COLLAPSE`

---

# 二十、Lower-Body Actual Review

实际记录：

- thigh exposure
- knee exposure
- calf exposure
- ankle exposure
- foot exposure
- legwear family
- leg accessories
- footwear
- barefoot
- open toe

目标不是：

“越露越好”。

目标是：

# 不再无意识全部保守化。

---

# 二十一、Male Review

A / B 分别检查：

## A

年轻男性是否仍然：

anime-commercial，

而不是：

western rogue / Disney-like fantasy male / comic hero。

## B

成熟男性是否：

成熟但 anime-first。

避免：

- brute
- superhero
- western rugged portrait
- teenage pretty boy regression

B 必须同时：

# MATURE
# EAST-ASIAN GACHA
# NOT INFANTILIZED

---

# 二十二、Androgynous Review

C 检查：

是否真正：

androgynous / handsome / sharp

而不是：

- generic feminine beauty
- techwear shortcut
- masculinized male face

---

# 二十三、Petite Adult Review

D：

继续：

`ADULT_MATURITY_GATE`

如果第一眼像未成年：

FAIL。

哪怕 Regional Style 很正确也：

FAIL。

---

# 二十四、Partial Beast Review

E：

检查：

- human dominance
- trait integration
- nonhuman trait count
- biological coherence
- generic kemonomimi risk
- commercial gacha read

Regional Style 不允许：

把所有兽化角色重新变成：

标准萌系猫耳角色。

---

# 二十五、Strong Female Review

F：

重点：

- strength readable?
- female adult identity?
- body proportions?
- waist?
- shoulders?
- thighs?
- muscle abstraction?
- superhero anatomy?

如果再次：

巨臂 + 巨腿 + 欧美 Amazon

记录：

`WESTERN_SUPERHERO_ANATOMY_DRIFT`

---

# 二十六、Pose Review

继续硬规则：

# NO CROSSED LEGS

但新增观察：

如果六张又全部：

`open-legged neutral standing pose`

记录：

`SAFE_STANCE_COLLAPSE`

这轮不要立即开发这个规则，

先测量。

---

# 二十七、Face Diversity

六张完成后比较：

- face length
- jaw
- chin
- eye size
- eye tilt
- brow
- nose abstraction
- mouth
- age read
- gender presentation

目标：

Regional Style 不等于：

# SAME EAST-ASIAN GACHA FACE

如果所有人只是换头发：

记录：

`REGIONAL_SAME_FACE_COLLAPSE`

暂时作为 benchmark finding，

不要本轮边跑边继续改 Skill。

---

# 二十八、A/B Comparison

只有所有新图生成完成后，

才读取对应旧 negative fixture。

逐 Case 对比：

## OLD

- regional read
- face grammar
- body grammar
- outfit grammar
- presentation
- background
- genericness

## NEW

同样字段。

然后输出：

- STRONGLY_IMPROVED
- IMPROVED
- NO_MEANINGFUL_CHANGE
- REGRESSED

---

# 二十九、不要只说“新版更好看”

必须说明：

到底改善在：

- face abstraction
- body proportions
- outfit language
- material rendering
- presentation
- lower-body diversity
- archetype fidelity

哪些维度。

---

# 三十、Benchmark Success Criteria

## Regional Layer STRONG PASS

至少：

5 / 6

达到：

`blind_regional_gacha_read = STRONG YES / YES`

并且：

没有 3 个以上 Case 出现 MEDIUM/HIGH：

`WESTERN_ANIME_STYLE_DRIFT`

---

## PASS

至少：

4 / 6

达到 YES，

剩余最多 2 个 BORDERLINE。

---

## PARTIAL

3 / 6。

---

## FAIL

<= 2 / 6。

另外：

即使 5/6 regional face 成功，

如果：

5–6 个角色又全部是同一种 fantasy outfit family，

最多：

`PASS_WITH_MAJOR_FINDING`

不能 Strong Pass。

---

# 三十一、Lower-Body Patch Secondary Acceptance

这不是主要评分，

但检查：

六图中是否仍然：

5–6 张都是：

`covered legs + boots`

如果是：

Lower-Body patch actual-generation generalization：

FAIL。

如果产生合理多样性：

PASS。

不要要求必须出现：

丝袜 / 腿环 / 裸足。

这是设计空间，

不是 quota。

---

# 三十二、不要自动开发新规则

生成和分析完成后：

# STOP

即使发现问题：

不要马上：

- 修改 Style Contract
- 改 critic
- 加新 enum
- 再生成 v3

先把真实结果给 Human Review。

---

# 三十三、Gallery

生成：

`regional_style_gallery.md`

每个 Case 展示：

- NEW IMAGE
- one-line identity
- Global Style result
- Regional Style result
- blind regional gacha read
- perceived age
- perceived gender presentation
- body read
- outfit family
- lower-body design
- archetype fidelity
- Genericness
- detected drift

不要在 Gallery 中混入旧图。

旧图放 A/B report。

---

# 三十四、A/B Report

生成：

`regional_ab_report.md`

需要包含：

## Executive Summary

Regional Layer 是否真正改善。

## Old Benchmark

为什么失败。

## New Benchmark

六个结果。

## Per-Case A/B

A–F。

## Cross-Case

- Regional consistency
- Face diversity
- Body diversity
- Outfit diversity
- Background diversity
- Lower-body diversity
- Archetype fidelity

## Remaining Systemic Biases

列出仍存在的模型默认偏置。

---

# 三十五、Human Review Package

为我准备一个非常简洁的 review summary：

每个 Case：

### A
- image path
- regional result
- top success
- top failure

依次到 F。

不要写一堆“测试通过”。

我要先：

# 看图。

---

# 三十六、本轮最终状态

全部生成、自动 QA、A/B comparison 完成后：

状态：

`REGIONAL_AB_GENERATED_PENDING_HUMAN_REVIEW`

然后停止。

---

# 三十七、最终只向我汇报

1. Test discovery audit 结果
2. 是否发现漏跑历史测试
3. A–F 六张新图路径
4. 每张 Global Gacha Gate
5. 每张 Regional Gate
6. 每张 `blind_regional_gacha_read`
7. 每张主要 Regional Drift
8. 每张 Archetype Fidelity
9. 每张实际 Body Read
10. 每张 Outfit Family
11. 每张 Lower-Body Design
12. 每张 Genericness
13. 男性角色是否仍欧美化
14. Mature Male 是否少年化
15. Androgynous Female 是否成立
16. Petite Adult 是否明确成年
17. Partial Beast 是否模板化
18. Strong Female 是否再次 Amazon/bodybuilder 化
19. Face Diversity
20. Outfit Diversity
21. Background Diversity
22. Lower-Body Diversity
23. 是否出现 SAFE_STANCE_COLLAPSE
24. 六案例旧→新 A/B 结论
25. Regional Layer Overall Result
26. 仍存在的最大系统问题
27. Gallery 路径
28. A/B Report 路径
29. 当前 runtime state

不要开始 v3。

等待 Human Review。
