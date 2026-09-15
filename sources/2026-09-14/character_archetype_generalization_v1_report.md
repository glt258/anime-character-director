---
title: Character Archetype Generalization Benchmark v1 Report
ingested: 2026-09-14
wiki_pages: [wiki/experiments/character-archetype-generalization-v1.md, wiki/experiments/benchmark-status.md, wiki/roadmap/current.md]
---

# Character Archetype Generalization Benchmark v1 报告

## Overall Result

**PASS_WITH_FINDINGS（6/6 archetype 成立）**。

六例都保持了 `CONTEMPORARY_COMMERCIAL_GACHA_ANIME` 的现代商业二游立绘读感；最终六例均满足 `NO CROSSED LEGS`，其中 Case C 的首发交叉腿读感通过 1 次局部 repair 修复。按 benchmark 判据，6/6 高于 PASS 所需的 5/6。Case D 没有明显幼态化，Case E 没有退化成 generic catgirl，因此没有重大失败升级。

当前停止状态：**`GENERATED_PENDING_HUMAN_REVIEW`**。这份报告是 AI 视觉检查和实际台账，不替代人工审美验收。

## 本轮范围与流程

本轮只测 CHARACTER DESIGN GENERALIZATION，不改旧 A / C / E / F / H，不改核心 Skill，不开发 UI、Quick Mode、Interaction Orchestrator 或新状态机。

每例按独立流程执行：Character Explore → Character Planning → Art Direction → Visual Preference Proposal → `benchmark_ai_delegation` 锁定 → Identity Pass → Design Review → PromptCompiler → `$imagegen` → Actual Image Review → Gacha Style Gate → Anatomy QA → Archetype-Specific Gate → Feature Ledger。Case B–F 在规划阶段读取此前实际生成结果的 ledger，未一次性预写六个最终 prompt。

Global Rendering Style 在六例中统一为 `CONTEMPORARY_COMMERCIAL_GACHA_ANIME`；Character Visual Style 只改变角色内部的造型语言。六例均使用全身、前向、双腿独立可读的 standee 约束。

## Case A — Young Adult Male / Social Trickster

- Final image: `cases/case-A-young-male/generation/generated-v1.png`
- Art Direction: `Saffron Signal`；铜色卷发 crest、萨弗朗无袖 wrap、钴蓝不对称肩披、奶油色分片下装。
- 实际读取：young adult male；medium athletic-balanced frame；medium-broad shoulders；moderate waist；balanced legs；arms subtle-to-moderate muscle；balanced male chest。
- Hair / eyes: warm copper with pale mint underlock / amber hazel。
- Outfit / Character Visual Style: saffron wrap top, cobalt shoulder drape, cream wide split trousers, flat ankle boots / playful kinetic festival tailoring。
- Fanservice: Light，来自手臂、颈部、腰部和自信表情，不是 shirtless/open-shirt。
- Gates: Gacha `PASS`；Anatomy `PASS`；Archetype Bias `PASS`；Genericness `LOW`；Want-to-Pull `9/10`。
- 结论：轻佻没有直接映射成 host/playboy；生成器给出了具体的铜发、明亮配色、斜向肩披和社交手势。

## Case B — Mature Adult Male / Pressure

- Final image: `cases/case-B-mature-male/generation/generated-v1.png`
- Art Direction: `Still Meridian`；灰金色低 ridge、石色宽肩 yoke、深紫 wrap、oxblood sash。
- 实际读取：mature adult male，late 30s–early 40s；large broad muscular frame；broad shoulders；powerful legs；moderate waist；developed chest。
- Hair / eyes: pale ash blond / olive gray。
- Outfit / Character Visual Style: sleeveless stone yoke over-tunic, plum wrap, oxblood sash, broad boots / quiet monumental tailoring。
- Fanservice: Moderate，来自肩、手臂、胸口控制式开口和腰部包裹。
- Gates: Gacha `PASS`；Anatomy `PASS`；Archetype Bias `PASS`；Genericness `LOW`；Want-to-Pull `8/10`。
- 结论：压力主要来自成熟脸、宽肩、强臂、扎根姿态和克制，不是黑发西装、军装、雪茄、疤痕或 mafia。

## Case C — Androgynous Adult Female

- Final image: `cases/case-C-androgynous-female/generation/repair-v1.png`
- Art Direction: `Violet Line`；长紫色分段辫、奶油长线 vest、plum 内层、teal 纵向 sash、褶裥 wrap skirt。
- 实际读取：adult female with androgynous/neutral styling；medium curvy-balanced frame；wide adult hips；moderate bust。
- Hair / eyes: deep violet braid with apricot underlayer / pale gold。
- Outfit / Character Visual Style: tailored cream/plum top, pleated wrap skirt, square-toe flats / tailored botanical modernism。
- Fanservice: Moderate，来自成年胸、腰、髋和大腿的干净框定。
- 首发与 repair：`generated-v1` 的膝踝下肢产生交叉腿读感，触发硬约束；`repair-v1` 只调整下肢为并列独立站姿，保留脸、发辫、裙装、配色和主锚点。
- Gates: Gacha `PASS`；Anatomy `PASS_AFTER_REPAIR`；Archetype `PASS_AFTER_REPAIR`；Genericness `LOW`；Want-to-Pull `8/10`。
- 结论：androgynous 没有塌成短黑发、平胸、techwear、cargo pants 或男性脸；这是“中性线条 + 明确成年女性身份”。

## Case D — Petite Adult Female

- Final image: `cases/case-D-petite-adult-female/generation/generated-v1.png`
- Art Direction: `Compact Meridian`；桃杏肩长波浪、象牙长线 vest、深 teal midi、rust 斜向 wrap、宽腰带。
- 实际读取：clearly adult female，late 20s；small compact curvy frame；narrow-medium adult shoulders；moderate waist and bust；adult hips and limbs。
- Hair / eyes: peach-apricot waves / clear blue。
- Outfit / Character Visual Style: ivory long vest, fitted teal midi dress, rust wrap, flat ankle boots / compact warm modern elegance。
- Fanservice: Moderate，来自成年胸、腰、髋、侧腿开口和裸臂。
- `ADULT_MATURITY_GATE`: **PASS**。face、torso、shoulders、pelvis/hips、limbs、pose、outfit、expression 全部读取为成人；第一眼没有 child/minor/loli/schoolgirl coding。
- Gates: Gacha `PASS`；Anatomy `PASS`；Archetype `PASS`；Genericness `LOW`；Want-to-Pull `9/10`。
- 结论：petite 通过的是成人比例和服装结构，不是把头、眼睛、躯干做成儿童比例。实际画面比计划更高挑，但成熟度没有失败。

## Case E — Partial Beast Adult

- Final image: `cases/case-E-partial-beast-adult/generation/generated-v1.png`
- Art Direction: `Brackish Signal`；海玻璃薄荷中发、耳后鳍状 ridge、珊瑚半透明 membrane、深绿 tunic、靛蓝 cropped trousers。
- 实际读取：adult feminine-neutral human-dominant character；medium athletic-balanced frame；human face/body dominate。
- Hair / eyes: sea-glass mint / warm amber；水平瞳孔与 throat gill lines 不够强，记为不可充分验证。
- Outfit / Character Visual Style: deep-green fitted tunic, coral membrane sash, indigo cropped trousers, flat wrapped shoes / quiet tidal geometry。
- Fanservice: Light，来自人形肩臂和贴身躯干，不是黑丝或 fetish kemonomimi。
- Partial Beast Gate: Human Dominance `PASS`；Trait Count `PASS`，2 个主要可见类别；Trait Integration `PASS`；Template Risk `LOW`。结果 `PASS_WITH_FINDINGS`，因为膜状结构比计划更大。
- Gates: Gacha `PASS`；Anatomy `PASS`；Genericness `LOW`；Want-to-Pull `9/10`。
- 结论：没有 catgirl、foxgirl、wolfgirl、ears+tail+stockings、furry 或全身兽化；非人特征成为头部—肩部—动作的一条整合结构线。

## Case F — Strong Adult Female

- Final image: `cases/case-F-strong-adult-female/generation/generated-v1.png`
- Art Direction: `Load-Bearing Bloom`；奶油柠檬发、祖母绿贴身躯干、象牙肩背结构、琥珀腰带、rust 髋部 wrap。
- 实际读取：adult female，early 30s；medium-large curvy power frame；broad shoulders；strong waist；wide hips；powerful thighs；moderate-powerful calves；long legs；prominent proportionate bust。
- Body Proportion breakdown: bust `prominent`；waist `strong`；shoulders `broad proportional`；back `strong`；hips `wide`；thighs `powerful/full`；calves `moderate-powerful`；muscle `moderate-to-strong`；overall frame `balanced curvy power frame`；leg length `long proportionate`。
- Hair / eyes: cream-lemon blonde / deep green。
- Outfit / Character Visual Style: emerald fitted torso, ivory shoulder/back panel, amber belt, rust hip wrap, sturdy flat shoes / graceful load-bearing elegance。
- Fanservice: Moderate，来自 prominent bust、strong waist-to-hip contrast、裸臂和长腿，而非 lingerie、黑丝或高跟。
- Strong Female Body Gate: `PASS_WITH_NOTES`；没有 fat-by-default、bodybuilder、athlete uniform 或 generic huge body collapse；但肩、手臂、大腿和 cape-like panel 比计划更强。
- Gates: Gacha `PASS`；Anatomy `PASS`；Genericness `LOW`；Want-to-Pull `9/10`。
- 结论：上一阶段的 Body Proportion 思路有效，强壮来自肩背、核心、腰髋、大腿、姿态和服装张力的分布，而不是整体横向放大。

## Cross-Case Generalization Review

### Gender Generalization

通过。A/B 的男性脸部和年龄结构成立；C 保持明确成年女性身份而没有变成男性脸；D/F 的女性身份由脸、身体和服装共同成立；E 的 gender presentation 保持 feminine-neutral，且人形主体没有被兽化覆盖。

### Age / Maturity

通过并有清晰层次：A young adult、B mature adult、C/D/E late-20s adult、F early-30s adult。D 是重点通过项：没有 oversized child head、huge childlike eyes、juvenile face、schoolgirl coding 或 childish pose。

### Body Build Generalization

通过。A medium balanced、B large muscular、C medium curvy、D small compact、E medium athletic human-dominant、F medium-large curvy power，不是同一身体模板换衣服。

### Face Diversity

通过并有发现。六张图在 jaw、chin、brow、eye size/tilt、face length 和 maturity 上可区分；未发现 `SAME_FACE_ACROSS_GENDER`。A/B 的眼眉与脸长差异尤其明显，C/D/F 也没有只靠换发型。

### Outfit / Color / Pose Generalization

通过。男性没有全部西装，女性没有全部裙装；A/B/C/D/E/F 的服装家族、材质和锚点不同。色彩没有回到单一黑/深蓝/黑红；姿势以正面 standee 为共同资产约束，但手势、重量、裙/披肩/膜状运动不同。C 证明 ImageGen 仍有交叉腿倾向，已通过一次 repair 处理。

### Fanservice Generalization

通过。A Light、B Moderate、C Moderate、D Moderate、E Light、F Moderate；男性没有被自动设为 None，且没有所有角色都用 shirtless/open-shirt 作为唯一性感路径。

### Gacha Read

六例 `Gacha Style Gate = PASS`。没有 fashion editorial、graphic poster、western concept art、sports anime sheet、minimalist editorial、semi-realistic fantasy 或 3D drift。

## 最大 AI Archetype Shortcut

本轮没有出现六个指定的高风险 archetype shortcut。最接近的默认偏好是：

1. ImageGen 对标准立绘仍有“腿靠近或交叉”的姿势偏好，C 首发触发；
2. 对高价值角色会扩大肩部/披肩/膜状结构，E/F 出现 scale drift；
3. 强壮男性和女性都容易向更明显的肌肉/肩部强调靠拢。

这些首先归为 ImageGen / sampling findings，不自动写成新 Skill 规则。

## Skill Problem vs ImageGen Problem vs Benchmark Design Problem

### Skill Problem

本轮没有确认的核心 Skill 问题。现有 Skill 的 Global Rendering Style、Design Ownership、NO CROSSED LEGS、Identity/Face Control、ADULT_MATURITY_GATE、Partial Beast Gate 和 Body Proportion 语言足以承载本轮流程；所有 identity variables 都成功记录 `benchmark_ai_delegation`，PromptCompiler 没有发现违反既有治理的情况。

### ImageGen Problem

- C 首发下肢交叉读感，已用唯一一次局部 repair 修复；
- E 非人膜状结构超过计划尺度，喉线/水平瞳孔不明显；
- F 肌肉、肩部和 cape-like panel 比计划强；
- D 纵向画面比计划更高挑，虽然成人成熟度通过。

### Benchmark Design Problem

- 每个 archetype 只生成一张图，能测默认倾向但不能估计生成方差；
- AI delegation 把审美选择故意交给模型，Want-to-Pull 和风格偏好仍需 Human Review；
- E 的 partial trait scale 需要人工判断“仍属少量特征”的容忍边界。

## Repairs

- Case C：1 次；范围仅为 lower-body stance；原图保留，repair-v1 作为最终图。
- Case A/B/D/E/F：0 次。

## Human Review Focus

建议人工优先看：B 的肌肉/压迫感是否超过 desired pressure，E 的膜状非人结构是否仍算 partial，F 的身体力量与女性曲线平衡，及 A–F 的脸部是否达到实际产品所需的差异度。

## Files

- Gallery: `character_archetype_generalization_gallery.md`
- Ledger: `archetype_feature_ledger.json`
- Summary: `comparison/benchmark_summary.json`
- Face review: `comparison/face_diversity_review.json`
- Body review: `comparison/body_diversity_review.json`
- Failure taxonomy: `comparison/failure_taxonomy.json`
- Per-case planning, PromptCompiler, identity, runtime handoff and QA: `cases/`

## Final State

**`GENERATED_PENDING_HUMAN_REVIEW`**。等待人工验收；Human Review 前不继续修改核心 Skill。
