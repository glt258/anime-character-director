---
title: Coverage / Legwear / Footwear / Lower-Body Diversity
ingested: 2026-09-14
wiki_pages: [architecture/regional-visual-language, constraints/anime-style-and-identity, roadmap/current]
---

# ADDITIONAL PATCH — Coverage / Legwear / Footwear / Lower-Body Diversity

在当前 Regional Visual Language 修改之外，再处理一个系统级问题：

# CONSERVATIVE COVERAGE CONVERGENCE

当前 `anime-character-director` 存在明显倾向：

无论角色：

- 男性
- 女性
- 年轻成年
- 成熟成年
- 老年
- 强壮
- 娇小
- 性感
- 中性
- 活泼
- 安静

最终都容易收敛到：

- 长裤
- 长裙
- 普通短靴
- 普通长靴
- 普通皮鞋
- 大面积完全覆盖腿部
- 很少设计脚部
- 很少设计腿部附件
- 很少使用袜类 / 裸足 / 开放式鞋履

这不是用户要求。

新增 Failure Type：

`CONSERVATIVE_COVERAGE_COLLAPSE`

`LEGWEAR_FAMILY_COLLAPSE`

`FOOTWEAR_FAMILY_COLLAPSE`

---

# 一、核心原则

不要：

# anti-fanservice -> anti-exposure

也不要：

# anti-black-stockings-template -> never-use-stockings

正确原则：

# LOWER BODY IS A REAL CHARACTER DESIGN SPACE

腿部、脚部、鞋履和覆盖方式都应该参与：

- silhouette
- personality
- movement
- sensuality
- elegance
- fantasy
- identity

而不是只负责“把身体盖住”。

---

# 二、新增 Lower-Body Visual Variables

正式增加：

## Skin Exposure Strategy

候选包括：

- fully covered
- mostly covered
- partial thigh exposure
- knee / calf exposure
- full-leg exposure
- asymmetrical exposure
- side-leg exposure
- ankle / foot emphasis

这不是固定枚举限制，
而是设计语义。

---

## Legwear Family

允许：

- none
- sheer tights
- opaque tights
- patterned tights
- thigh-high stockings
- knee-high stockings
- over-knee socks
- fitted leggings
- fantasy leg wraps
- asymmetric legwear
- one-leg stocking / one-leg exposed
- integrated bodysuit leg section
- loose lower-leg fabric

不要默认：

`none`

也不要默认：

`black stockings`

---

# 三、Stockings / Tights 正式合法化

对于明确成年角色：

丝袜 / 连裤袜 / 长筒袜完全可以作为正常视觉设计工具。

允许：

- black
- white
- gray
- colored
- translucent
- patterned
- gradient
- fantasy-material
- asymmetric

但必须避免：

`adult sexy woman -> automatic black sheer stockings`

丝袜应由：

- outfit
- palette
- silhouette
- character style
- fanservice strategy

决定。

---

# 四、Leg Accessories

新增：

`leg_accessory_family`

候选：

- none
- thigh ring
- leg strap
- garter-like decorative band
- knee ornament
- calf strap
- ankle ornament
- chain detail
- fabric tie
- asymmetrical leg accessory
- integrated armor / hard accent

注意：

成年人可以将：

- thigh ring
- garter-like structure
- leg strap

作为性感或视觉分割设计。

但不要：

每个性感女性都自动腿环。

---

# 五、Footwear Family 扩展

当前鞋履过于集中在：

- boots
- low heels
- leather shoes

扩展正式设计空间：

- barefoot
- barefoot with ankle / instep ornament
- toe-loop footwear
- open sandals
- fantasy sandals
- high sandals
- low sandals
- flats
- loafers
- pumps
- low heels
- high heels
- platform shoes
- sneakers
- soft boots
- ankle boots
- tall boots
- open-toe boots
- split-toe / tabi-inspired fantasy footwear
- foot-wrap construction
- partial footwear
- asymmetrical footwear

不要把：

`barefoot`

视为：

“没设计鞋子”。

裸足本身可以是：

# deliberate footwear decision

---

# 六、Barefoot Design

如果选择：

`barefoot`

仍然需要设计：

- ankle
- instep
- toe visibility
- optional anklet
- optional foot ornament
- optional fabric / strap transition

确保：

裸足是完整造型的一部分。

不是：

“ImageGen 忘了鞋”。

---

# 七、男女都适用

不要只给女性使用丰富腿部设计。

男性也可以使用：

- sandals
- barefoot
- shin wraps
- calf straps
- cropped trousers
- asymmetric trousers
- exposed lower legs
- fitted legwear
- decorative ankle structures
- open footwear

避免：

`male -> pants + boots`

固定模板。

---

# 八、年龄规则

必须区分：

## Adult Characters

成年人允许自由探索：

- stockings
- thigh-highs
- leg rings
- thigh straps
- bare thighs
- barefoot
- heels
- sensual lower-body framing

只要符合角色与用户意图。

## Minor / Clearly Juvenile Characters

不要使用：

- fetishized thigh garters
- sexualized stocking framing
- erotic leg emphasis

普通：

- socks
- tights
- sandals
- barefoot
- sneakers

可以正常使用，

但保持年龄合适。

这条属于 age-appropriateness，

不是重新回到保守主义。

---

# 九、Fanservice 与 Lower Body 分离

不要把：

`Fanservice Level`

直接决定：

`Lower Body Coverage`

例如：

Strong Fanservice 不一定：

- bare legs

可以：

- full tights
- body-hugging legwear
- waist / back / chest emphasis

Moderate 也可以：

- bare legs
- open footwear

两者是不同变量。

---

# 十、Lower-Body Design Gate

Final Design 增加专项：

`LowerBodyDesignReview`

检查：

- exposure_strategy
- legwear_family
- leg_accessory_family
- footwear_family
- visual_reason
- relationship_to_character_style
- relationship_to_pose
- repetition_risk

如果结果只是：

`generic pants + generic boots`

而没有角色设计理由，

应提高 genericness risk。

---

# 十一、Visual Diversity Ledger 扩展

记录 actual-image features：

- thigh_exposure
- knee_exposure
- calf_exposure
- ankle_exposure
- foot_exposure
- legwear_family
- stocking_color_family
- stocking_opacity
- leg_accessory_family
- footwear_family
- heel_height
- open_toe
- barefoot
- asymmetrical_lower_body

用于发现：

多角色全部：

`pants + boots`

或：

`bare legs + heels`

这种新坍缩。

---

# 十二、新的 Diversity Penalty

最近多个角色如果连续出现：

- trousers + boots
- long skirt + boots
- bare legs + low heels
- black stockings + heels

提高 repetition penalty。

注意：

# PENALTY, NOT BAN

用户明确喜欢某组合时必须允许。

---

# 十三、PromptCompiler

PromptCompiler 必须真正编译：

- lower-body exposure
- legwear
- leg accessories
- footwear
- foot visibility

不要只编译：

`full-body`

否则 ImageGen 会自己填默认鞋履。

例如设计已选择：

`white opaque tights + barefoot toe-loop foot structure`

PromptCompiler 必须明确保留。

不能偷偷简化成：

`white leggings and sandals`

---

# 十四、Visual Grounding QA

Actual Image 必须检查：

例如 Final Design：

`barefoot`

实际生成成：

boots

则：

`FOOTWEAR_GROUNDING_FAIL`

Final Design：

`white tights`

实际变：

bare legs

则：

`LEGWEAR_GROUNDING_FAIL`

Final Design：

`thigh ring`

实际缺失：

记录 anchor miss。

---

# 十五、Anti-Template Examples

禁止硬映射：

`sexy woman`
→ black stockings + high heels

`strong woman`
→ boots

`quiet woman`
→ loafers

`male`
→ trousers + boots

`fantasy`
→ leather boots

`petite adult`
→ knee socks

`aquatic`
→ barefoot

`elegant`
→ heels

这些都只能是候选。

---

# 十六、测试

至少增加：

## Test A

成年性感女性没有指定鞋履：

AI 可以提出 stockings / bare legs / barefoot / sandals / heels 等多个方向，
不得自动锁黑丝高跟。

## Test B

成年男性角色：
不得默认 trousers + boots。

## Test C

明确用户要求白色紧身裤袜 + 裸足：
PromptCompiler 必须完整保留。

## Test D

明确用户要求 thigh ring：
不得被“保守化”过滤。

## Test E

Strong fanservice：
不要求裸腿。

## Test F

None fanservice：
仍然允许普通裸足 / 凉鞋 / 短裤等非性化露肤。

## Test G

Minor：
不得因 diversity 机制自动引入 sexualized thigh accessories。

## Test H

Visual Ledger：
能检测连续多个 pants + boots。

---

# 十七、Style Constitution 新增原则

加入：

> Modesty is not the default solution to character design.

> Lower-body exposure, hosiery, leg accessories, open footwear, and barefoot designs are valid character-design tools.

> Anti-template rules must prevent repetitive sexualization patterns, not suppress sexual, sensual, stylish, or unconventional design choices for adult characters.

> Footwear and legwear are identity variables, not afterthoughts.

---

# 十八、这轮仍然不要生图

本次继续：

# MODIFY SKILL ONLY

不要调用 `$imagegen`。

完成：

- models
- policy
- compiler
- critic
- diversity ledger
- schema
- tests
- docs

然后和 Regional Visual Language 修改一起跑完整 regression suite。

最终汇报时额外增加：

1. Coverage bias 如何修复
2. 新 Lower-Body variables
3. Stockings / tights 支持
4. Leg accessories 支持
5. Barefoot 支持
6. Male lower-body diversity
7. Adult vs minor age-appropriate handling
8. PromptCompiler 如何防止鞋履/袜类丢失
9. LowerBodyDesignReview
10. 新增测试及结果

不要生成图片。
