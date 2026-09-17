---
title: Regional Visual Language Layer + Cross-Archetype Style Regression Fix
ingested: 2026-09-14
wiki_pages: [architecture/skill-and-runtime, constraints/anime-style-and-identity, roadmap/current]
---

# anime-character-director — Regional Visual Language Layer + Cross-Archetype Style Regression Fix

继续修改当前 `anime-character-director` Skill。

这次不是修某一张图，也不是继续跑 Character Archetype Generalization Benchmark。

当前 benchmark 已经暴露出一个系统级问题：

# 当前 Global Rendering Style 不足以约束真正的目标审美

现有：

`CONTEMPORARY_COMMERCIAL_GACHA_ANIME`

可以一定程度防止：

- photorealism
- western realism
- graphic poster
- fashion editorial
- concept-art drift

但在跨 archetype 后仍然大面积出现：

- western anime-inspired character art
- western fantasy character concept
- 欧美式面部骨相
- 欧美 fantasy RPG 服装语言
- superhero / warrior concept language
- character-sheet presentation
- 泛东方 fantasy NPC
- 同一套腰封 / 披肩 / 垂布 / 金边 / 长靴反复出现

因此现在必须正式增加：

# REGIONAL VISUAL LANGUAGE LAYER

---

# 一、先理解这次失败

Character Archetype Generalization Benchmark 当前 6 个样本存在以下系统性问题：

## P0 — Regional Style Drift

大量结果虽然 technically anime，

但第一眼是：

`Western anime-inspired fantasy illustration`

而不是：

`modern East-Asian commercial gacha character art`

新增 Failure Type：

`WESTERN_ANIME_STYLE_DRIFT`

以及：

`WESTERN_FANTASY_CONCEPT_DRIFT`

---

## P0 — Outfit Family Collapse

六个不同角色大量收敛到：

- wrapped tunic
- sash
- long hanging cloth
- cloak
- gold trims
- ornamental belt
- fantasy boots
- cream / green / burgundy / gold
- generic East-meets-West fantasy RPG

新增：

`GENERIC_FANTASY_RPG_DRIFT`

`OUTFIT_FAMILY_COLLAPSE`

---

## P1 — Character Sheet Presentation Collapse

部分图像像：

- concept sheet
- costume concept
- character design board
- flat presentation illustration

而不是：

真正商业二游 playable-character illustration。

新增：

`CHARACTER_SHEET_PRESENTATION_DRIFT`

---

## P1 — Archetype Shortcut Replacement

当前系统虽然能避开一些明确写死的旧模板，

但会换一个新模板继续 shortcut。

例如：

`young flirtatious male`
→ desert prince / rogue

`mature male`
→ giant muscular fantasy warrior

`androgynous woman`
→ pseudo-oriental uniform woman

`strong woman`
→ amazon / bodybuilder fantasy warrior

说明：

仅靠 negative prompt 阻止具体模板不够。

需要约束：

# 底层视觉母语

---

# 二、新 Style Architecture

将现有风格体系正式拆成三层：

## Layer 1 — Global Rendering Medium

默认：

`CONTEMPORARY_COMMERCIAL_GACHA_ANIME`

回答：

> 这是不是现代商业二游的 2D anime rendering？

---

## Layer 2 — Regional Visual Language

新增：

`RegionalVisualLanguage`

默认：

# `EAST_ASIAN_CONTEMPORARY_GACHA`

回答：

> 它使用的是哪套商业动漫角色设计与绘制视觉母语？

---

## Layer 3 — Character Visual Style

已有：

`Character Visual Style`

例如：

- elegant
- street
- sporty
- glamorous
- sensual
- quiet
- gothic
- strange
- minimal
- fantasy

回答：

> 这个具体角色自己的视觉性格是什么？

---

# 三、优先级

明确优先级：

1. Explicit User Style Override
2. Global Rendering Medium
3. Regional Visual Language
4. Character Visual Style
5. Character Identity Variables
6. Implementation Variables

即：

Character Visual Style 不允许覆盖 Regional Visual Language。

例如：

`western cowboy-inspired clothing`

可以作为 Character Visual Style / costume inspiration，

但如果 Regional Visual Language 仍然锁定：

`EAST_ASIAN_CONTEMPORARY_GACHA`

最终画面仍然应当使用现代东亚二游的角色设计与 anime abstraction。

---

# 四、非常重要：Regional Style ≠ Character Ethnicity

必须写入 Style Constitution：

# REGIONAL VISUAL LANGUAGE IS NOT CHARACTER ETHNICITY

`EAST_ASIAN_CONTEMPORARY_GACHA`

描述的是：

- illustration grammar
- anime abstraction
- character design grammar
- rendering hierarchy
- commercial presentation conventions

不是：

- 人种
- 国籍
- 肤色
- 世界观地区

因此它绝对不能自动：

- 把所有角色画成东亚人
- 把所有角色变白皮肤
- 强制黑发
- 强制中式 / 日式 / 韩式服装
- 强制东方建筑
- 强制东亚职业

允许：

- dark skin
- tan skin
- fantasy ethnicity
- western-looking fictional world
- African-inspired character concept
- European fantasy setting
- desert character
- aquatic species
- beast traits

但：

最终二次元角色设计与 rendering grammar 仍然符合目标商业二游视觉语言。

---

# 五、RegionalVisualLanguage 数据模型

在 domain/model 层增加正式类型。

建议类似：

`RegionalVisualLanguage`

至少支持：

- `EAST_ASIAN_CONTEMPORARY_GACHA`
- `WESTERN_ANIME_INSPIRED`
- `REGION_NEUTRAL_ANIME`
- `CUSTOM`

不要为了这次测试做死代码。

默认：

`EAST_ASIAN_CONTEMPORARY_GACHA`

除非：

用户明确提出其他地域视觉语言。

---

# 六、用户覆盖规则

Explicit User Request 优先。

例如用户说：

- “我要欧美 anime-inspired”
- “做成美漫融合日漫”
- “我就是想要 western fantasy anime”
- “不要东亚二游风”

允许覆盖。

记录：

`regional_visual_language_source = explicit_user_override`

如果用户没有指定：

默认：

`EAST_ASIAN_CONTEMPORARY_GACHA`

记录：

`regional_visual_language_source = default_style_policy`

不能要求用户每次手动指定。

---

# 七、EAST_ASIAN_CONTEMPORARY_GACHA 定义

不要写成几个空泛标签。

必须在：

`ANIME_STYLE_CONTRACT`

和实际 PromptCompiler policy 中给出可以执行的视觉语言定义。

---

# 八、Face Abstraction

默认目标：

# anime-first facial construction

需要倾向：

- simplified facial planes
- restrained nose definition
- restrained lips
- clean anime jaw/chin construction
- stylized eye geometry
- controlled cheek volume
- graphic-readable facial silhouette
- anime abstraction before realistic anatomy

避免：

- deep-set western eyes
- heavy brow ridge
- strongly projected nose bridge
- realistic nostril definition
- realistic full lips
- strongly sculpted cheekbones
- western superhero jaw
- realistic facial planes
- semi-realistic portrait anatomy

但：

# 不允许变成“所有角色娃娃脸”。

成熟男性仍然可以：

- 方一些的 jaw
- 更深的眉线
- 更成熟的眼型

只是仍然保持：

anime abstraction。

---

# 九、Male Face 不得欧美化

这是本轮特别严重的问题。

对于成年男性：

不要通过：

- huge jaw
- heavy brow
- hyper-defined nose
- realistic facial anatomy
- giant trapezius
- superhero proportions

表达“男性”。

应该允许：

- elegant male
- slender male
- broad male
- mature male
- rough male

但全部仍然：

# East-Asian commercial gacha anime male visual grammar

不要：

“男性 = Western comic anatomy”。

---

# 十、Female Face 同样限制

女性角色不要滑向：

- western fashion illustration
- semi-realistic fantasy woman
- realistic nose + lips
- heavily sculpted cheekbones

保持：

anime facial abstraction。

但：

成年女性仍然必须能够表现：

- maturity
- sensuality
- authority
- strength

不能因此全部：

幼态化。

---

# 十一、Body Rendering Grammar

Regional Visual Language 需要控制的不只是脸。

默认身体表现：

- anime-proportioned
- elegant line rhythm
- stylized but anatomically coherent
- readable silhouette
- controlled muscle definition
- character-design-first proportions

避免：

- superhero anatomy
- western comic massing
- bodybuilding exaggeration
- realistic muscle separation
- huge trapezius by default
- giant forearms
- hyper-realistic thigh anatomy

力量角色：

# strength ≠ western superhero anatomy

---

# 十二、Outfit Design Grammar

这是这次最严重的坍缩之一。

不要再认为：

“fantasy + gacha”

就等于：

- sash
- robe
- cape
- hanging cloth
- gold trims
- boots
- ornamental belt

新增：

# Outfit Family Diversity Constraint

PromptCompiler / Final Design 阶段必须知道：

二游角色可以来自非常多 outfit family：

- contemporary fantasy
- street
- elegant
- utility
- ceremonial
- casual-fantasy
- asymmetrical fashion
- performance-inspired
- soft sculptural
- sporty fantasy
- body-framing fashion
- layered urban
- minimal premium
- experimental silhouette

但：

不能因为 fictional world 就默认：

`generic fantasy robe`.

---

# 十三、禁止“泛东方幻想”偷懒

特别新增 anti-pattern：

`PSEUDO_ORIENTAL_FANTASY_DEFAULT`

包括频繁组合：

- Mandarin-like collar
- crossed front
- sash
- hanging tassel
- gold trim
- long skirt panels
- robe-like coat
- floral ornaments
- jade / teal / cream palette

这些元素：

不是禁止。

但如果用户没要求，

不能因为：

`East Asian regional visual language`

就自动塞入：

“东方服装”。

再次强调：

# East Asian visual language ≠ East Asian costume.

---

# 十四、Material Language

现代商业二游立绘需要：

- controlled material separation
- intentional fabric hierarchy
- polished anime shading
- clear specular hierarchy
- readable hard/soft material contrast
- premium but stylized finish

避免：

- western painterly fantasy rendering
- watercolor concept art
- rough concept brushwork
- realistic leather-heavy concept art
- overly matte costume-sheet rendering

---

# 十五、Lighting

默认倾向：

- polished anime game lighting
- controlled rim light
- readable face lighting
- skin kept visually clean
- character-first lighting hierarchy

避免：

- cinematic western concept-art chiaroscuro
- realistic dramatic portrait lighting
- muddy fantasy atmosphere
- overly volumetric western game key-art lighting

---

# 十六、Presentation Language

新增：

# COMMERCIAL_GACHA_PRESENTATION

区别：

`角色设定稿`

和：

`商业二游角色立绘`

默认需要：

- character is the unmistakable focal point
- premium playable-character presentation
- polished final illustration
- strong face readability
- intentional silhouette
- clear hierarchy
- finished promotional-quality rendering

不要自动：

- white concept sheet
- flat model sheet
- giant graphic circle
- geometric presentation board
- character design portfolio page

---

# 十七、背景规则

背景不是：

“证明这是二游”的工具。

避免反复：

- giant circles
- abstract rings
- generic fantasy palace
- white concept board

背景可以：

- environmental
- abstract
- minimal
- architectural
- atmospheric

但必须服务角色。

新增重复检测：

`BACKGROUND_PRESENTATION_COLLAPSE`

---

# 十八、新增 RegionalStyleCritic

实现独立 critic：

建议名称：

`RegionalStyleCritic`

职责：

基于 actual image 判断：

## regional_visual_language_match

- STRONG
- ACCEPTABLE
- WEAK
- FAIL

## east_asian_gacha_read

1–10

## western_anime_drift

NONE / LOW / MEDIUM / HIGH

## western_concept_art_drift

NONE / LOW / MEDIUM / HIGH

## facial_abstraction_match

## body_rendering_match

## costume_language_match

## presentation_match

## confidence

## result

---

# 十九、RegionalStyleCritic 必须基于实际图

绝对不能：

Prompt 中有：

`East Asian commercial gacha`

就 PASS。

需要检查实际图片。

---

# 二十、新 Drift Types

增加正式枚举 / 诊断：

`WESTERN_ANIME_STYLE_DRIFT`

`WESTERN_FANTASY_CONCEPT_DRIFT`

`WESTERN_SUPERHERO_ANATOMY_DRIFT`

`PSEUDO_ORIENTAL_FANTASY_DEFAULT`

`GENERIC_FANTASY_RPG_DRIFT`

`CHARACTER_SHEET_PRESENTATION_DRIFT`

`OUTFIT_FAMILY_COLLAPSE`

`BACKGROUND_PRESENTATION_COLLAPSE`

不要把所有错误都塞进：

`GACHA_STYLE_DRIFT`

需要可诊断。

---

# 二十一、扩展现有 GachaStyleCritic

现有：

`GachaStyleCritic`

不要删除。

改成：

## Stage A — Global Rendering Style

它是不是：

商业 anime / gacha？

## Stage B — Regional Visual Language

调用：

`RegionalStyleCritic`

它是不是目标 Regional Visual Language？

最终 Style Gate：

Global PASS
AND
Regional PASS

才能：

`STYLE_VALID`

---

# 二十二、Style Gate Result

建议：

`StyleGateResult`

包含：

- global_rendering_result
- regional_visual_language_result
- character_visual_style_result
- detected_drift_types
- overall_result

只要：

Global = PASS

但：

Regional = FAIL

最终仍然：

# FAIL

这正是当前 benchmark 的情况。

---

# 二十三、PromptCompiler 必须真正注入 Regional Layer

不要只修改 docs。

PromptCompiler 需要明确编译：

## Rendering Foundation

`CONTEMPORARY_COMMERCIAL_GACHA_ANIME`

## Regional Visual Language

`EAST_ASIAN_CONTEMPORARY_GACHA`

## Character Visual Style

case-specific style

顺序固定。

---

# 二十四、PromptCompiler 不要只塞关键词

不要仅：

`east asian anime gacha style`

这种 tag soup。

应该编译成结构化 natural-language constraints。

例如表达：

- anime-first facial abstraction
- restrained realistic facial planes
- modern East-Asian commercial gacha illustration grammar
- polished playable-character rendering
- stylized anatomy rather than western superhero anatomy
- premium game-character material rendering
- character-design-first outfit construction
- avoid western fantasy concept-art aesthetics
- avoid semi-realistic western anime-inspired facial construction

具体文本可以由 compiler 模板组织，

不要硬编码一整段到业务逻辑。

---

# 二十五、Negative Constraints

默认 Regional Style negative constraints 增加：

- western comic anatomy
- western superhero proportions
- western fantasy character concept art
- semi-realistic western anime illustration
- realistic facial planes
- heavy brow ridge
- strongly projected realistic nose
- realistic full-lip portrait styling
- painterly fantasy concept rendering

但：

negative 只是辅助。

主约束仍然必须是：

positive regional style contract。

---

# 二十六、Outfit Family Ledger

扩展当前 Visual Diversity Ledger。

记录实际图：

- outfit_family
- neckline_family
- upper_body_structure
- lower_body_structure
- outer_layer_family
- waist_structure
- hanging_cloth_presence
- cape_presence
- sash_presence
- major_trim_language
- footwear_family

用于检测：

# 多角色服装语法坍缩

---

# 二十七、Outfit Family Collapse Detection

例如连续 4–6 个角色都出现：

- sash
- long hanging cloth
- gold trim
- fantasy boots
- robe-like structure

即使颜色不同，

也应：

`OUTFIT_FAMILY_COLLAPSE = HIGH`

注意：

这是 penalty / diagnostic，

不是硬禁止。

用户明确要求同阵营制服时：

允许重复。

---

# 二十八、Archetype Shortcut 检测升级

以前我们主要查：

具体模板。

现在增加：

# semantic shortcut family

例如：

mature man
→ western fantasy brute

strong woman
→ amazon warrior

partial beast
→ aquatic elegant woman

不能只查：

有没有黑发西装。

需要判断：

“模型是不是又找了另一个 cliché 来代替角色设计”。

---

# 二十九、Regional Visual Language 不能压死多样性

非常重要。

不要因为新增地域约束：

最后所有人都变成：

- 白皮
- 小脸
- 尖下巴
- 巨眼
- 细胳膊
- 少女体型

这也是失败。

需要允许：

## 男性

- slender
- athletic
- broad
- mature
- older-looking adult

## 女性

- slender
- curvy
- strong
- petite adult
- tall
- mature

## 肤色

- pale
- fair
- tan
- dark

## 世界观

- contemporary
- sci-fi
- fantasy
- urban
- desert
- aquatic
- gothic

Regional Visual Language 只控制：

# artistic grammar

不是角色模板。

---

# 三十、成熟角色不能幼态化

新增 regression：

`REGIONAL_STYLE_INFANTILIZATION`

如果为了摆脱欧美骨相，

模型把：

成熟男性 / 成熟女性

全部画成：

少年 / 少女脸，

FAIL。

---

# 三十一、Male Commercial Gacha Gate

新增专项检查。

男性角色实际图判断：

- anime male face fidelity
- mature-read when required
- not western superhero
- not female-face-with-male-body
- playable gacha read
- head identity

---

# 三十二、Strong Female Gate

保留之前经验。

强壮女性：

不要：

- fat by default
- bodybuilder by default
- amazon warrior by default
- western comic heroine anatomy

力量感可以来自：

- shoulder line
- back
- core
- thighs
- posture
- stance
- outfit tension

Body proportion 继续拆字段。

---

# 三十三、将本轮 6 图加入 Negative Regression Fixtures

Character Archetype Generalization Benchmark 的当前六张结果：

全部作为：

# NEGATIVE REGRESSION FIXTURES

不要当 positive exemplar。

根据实际图分别标注可能问题：

- WESTERN_ANIME_STYLE_DRIFT
- GENERIC_FANTASY_RPG_DRIFT
- OUTFIT_FAMILY_COLLAPSE
- CHARACTER_SHEET_PRESENTATION_DRIFT
- WESTERN_SUPERHERO_ANATOMY_DRIFT
- ARCHETYPE_SHORTCUT

其中：

Partial Beast 的“没有直接 catgirl 化”

可以记录为：

`LOCAL_POSITIVE_BEHAVIOR`

但整张仍不是 positive style reference。

---

# 三十四、不要把图片直接塞入未来 ImageGen

这些失败图片：

只用于：

- critic regression
- metadata
- human-labeled failure fixture

不要作为 future generation image reference。

避免污染。

---

# 三十五、新增测试

至少增加以下测试。

## Test 1 — Default Regional Style

用户没有指定 regional style：

应自动：

`EAST_ASIAN_CONTEMPORARY_GACHA`

---

## Test 2 — Explicit Override

用户明确：

“欧美 anime-inspired”

必须允许：

regional override。

---

## Test 3 — Regional ≠ Ethnicity

设置：

dark-skinned adult character

Regional：

`EAST_ASIAN_CONTEMPORARY_GACHA`

不能自动把 skin tone 改白。

---

## Test 4 — Regional ≠ Costume

普通 modern character：

不能因为 East Asian regional style

自动加入：

- hanfu
- kimono
- qipao
- sash
- tassels

---

## Test 5 — Mature Male

不能因为目标是东亚二游：

自动少年化。

---

## Test 6 — Strong Female

不能：

western superhero anatomy。

---

## Test 7 — PromptCompiler

Regional style 必须出现在 compiled prompt bundle。

---

## Test 8 — Explicit User Style Priority

user override 必须覆盖 default regional style。

---

## Test 9 — Resume / Migration

旧 session 没有 regional_visual_language 字段时：

默认迁移到 policy default。

但必须标记：

`source = migrated_default`

不要伪造成 human selection。

---

## Test 10 — Prompt Audit

regional style 不得被 Character Visual Style 覆盖。

---

## Test 11 — Outfit Collapse

重复 outfit family 可被检测。

---

## Test 12 — Negative Fixture Classification

本轮至少选择数个失败 fixtures，

确保 critic fixture / deterministic metadata test 能输出预期：

`WESTERN_ANIME_STYLE_DRIFT`

或：

`GENERIC_FANTASY_RPG_DRIFT`

如果当前 critic 不是视觉模型，无法自动读取图片，

则使用 human-labeled fixture metadata 做 regression contract，

不要假装静态 Python 能理解图片。

---

# 三十六、Schema 更新

更新涉及 schema：

- CharacterDesign
- VisualPreference
- FinalDesign
- PromptBundle
- StylePolicy
- StyleReview
- VisualFeatureLedger

增加：

`regional_visual_language`

以及：

`regional_visual_language_source`

必要时：

`regional_style_override_reason`

---

# 三十七、Backward Compatibility

旧 artifact 不允许直接报废。

读取旧 Final Design 时：

如果没有：

`regional_visual_language`

使用：

current policy default

并记录 migration event。

不要修改旧 artifact 文件本身。

---

# 三十八、配置层

更新：

类似：

`config/anime_style_policy.yaml`

加入：

regional_visual_language:
  default: EAST_ASIAN_CONTEMPORARY_GACHA
  allow_user_override: true

并把：

positive guidance
negative drift types
critic thresholds

尽量放配置 / policy 层，

不要散落硬编码。

---

# 三十九、文档

更新至少：

`docs/ANIME_STYLE_CONTRACT.md`

`skills/anime-character-director/SKILL.md`

相关：

workflow / character-design-guide

写清楚：

# Rendering Style
# Regional Visual Language
# Character Visual Style

三个概念严格不同。

---

# 四十、ANIME_STYLE_CONTRACT 新增核心条款

建议明确写入：

> “Anime” is a medium family, not a sufficient commercial style definition.

以及：

> “Commercial gacha” alone does not guarantee the intended regional visual language.

以及：

> The default visual language is contemporary East-Asian commercial gacha character illustration unless the user explicitly requests another regional direction.

以及：

> Regional visual language governs artistic grammar, not character ethnicity, nationality, skin tone, occupation, or costume culture.

---

# 四十一、不要写具体游戏 imitation prompt

不要把 Style Contract 写成：

- “像绝区零”
- “像原神”
- “像崩铁”
- “像鸣潮”

可以用于我们内部分析设计原则，

但正式默认 contract 要使用：

generic visual descriptors。

目标：

不是复制某一款游戏，

而是：

# 稳定进入正确的现代东亚商业二游审美分布。

---

# 四十二、这轮不要重新生六张

本次任务：

# MODIFY SKILL FIRST

不要调用 `$imagegen`。

不要马上 rerun benchmark。

先完成：

- architecture
- models
- policy
- compiler
- critics
- schema
- migrations
- tests
- docs

---

# 四十三、测试要求

完成修改后：

运行所有相关 test suite。

至少：

- style tests
- schema tests
- prompt compiler tests
- governance tests
- migration tests
- diversity ledger tests
- regional style tests
- existing regression tests

不能只跑新测试。

---

# 四十四、不要破坏已有规则

必须保持：

- NO CROSSED LEGS
- hand anatomy QA
- Design Ownership
- Visual Preference Gate
- Human Override Priority
- anti-black-hair default convergence
- anti-profession literalization
- anti-template fanservice
- adult fanservice support
- Visual Grounding
- Design Direction Failure vs Rendering Failure
- Body Proportion decomposition
- Global Gacha Style Gate

Regional Style 是：

# 新增一层

不是替换旧系统。

---

# 四十五、完成后不要继续实验

最终只向我汇报：

1. 修改了哪些文件
2. 新的三层 Style Architecture
3. `RegionalVisualLanguage` 数据模型
4. 默认 regional style
5. 用户如何 override
6. PromptCompiler 如何注入
7. 新 RegionalStyleCritic
8. 新 drift types
9. Outfit Family Collapse 如何检测
10. 为什么 regional style 不会变成 ethnicity/costume lock
11. mature male 防幼态化如何处理
12. strong female 防 western superhero 化如何处理
13. 旧 session migration
14. 负样本如何登记
15. 新增测试数量
16. 全量测试结果
17. 是否存在 breaking change
18. Wiki / docs 更新位置
19. runtime / schema compatibility 状态
20. 下一步推荐的 regression benchmark 方案，但不要执行

完成后停止。

# 不调用 `$imagegen`
# 不生成图片
# 不重新跑六角色 benchmark
# 等待 Human Review
