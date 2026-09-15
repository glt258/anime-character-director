# Anime Style Constitution

状态：Phase 0 / system invariant  
适用范围：高品质原创 2D 二次元商业游戏角色设计 Agent 全链路

## 1. 不可覆盖的系统目标

本系统只产出高品质、原创、2D、二次元、面向商业游戏的角色设计；其 canonical runtime core 是 `high-quality original 2D anime commercial game character design`。这里的“二次元”不是可选关键词，而是全局 hard constraint 和 system invariant：

- 所有 Agent、Skill、提示词、Schema、验证器和后续 UI 都必须服从本宪章。
- 用户 brief、风格强度、角色设定和下游参数不得覆盖 `anime_2d = true`、`2D anime abstraction` 或原创性要求。
- 本系统不针对、复制、复刻或近似任何具体已有角色、画师、游戏作品或可识别的个人风格。
- 本 Phase 只建立约束，不生成图片，不运行 benchmark，不做角色设计实验。

机器可读的 runtime single source of truth 位于 `config/anime_style_policy.yaml`。本 Markdown 是人类可读的 Constitution；运行时代码必须读取 YAML，不得在 Python 中复制另一套核心风格文本。YAML 与本宪章语义不一致时，必须修复 policy/document 对齐，不能放宽 hard constraint。

## 2. 优先级

约束从高到低排列；低优先级输入与高优先级约束冲突时，必须拒绝冲突部分并保留可用部分：

1. Anime Style Constitution（本文件）
2. `schemas/character_design.schema.json` 中的 system invariants
3. `skills/anime-character-imagegen/SKILL.md` 的 prompt assembly 与 generation validation
4. `prompts/character_designer_system.md` 与 `prompts/visual_critic_system.md`
5. 用户可配置的角色设计字段

任何下游 Agent 都不得把本宪章降级为普通 prompt 文本、建议项或可编辑的 `style` 参数。

## 2A. HARD NO-CROSSED-LEGS INVARIANT

`NO_CROSSED_LEGS_HARD_INVARIANT = true` is a global generation invariant for normal two-legged humanoid anatomy. No user prompt, Visual Preference, Character Visual Style, Regional Style, Fanservice, or Pose Style may override it. The `LegSeparationContract` requires separate thighs, knees, calves, ankles, and feet, no centerline crossing, no leg-occlusion crossing, and readable negative space. `LegSeparationGate` runs on actual-image evidence; `FAIL` and `UNCERTAIN` block candidate promotion. See `runtime/leg_separation_runtime.py` and `schemas/regional_style.schema.json`.

### 2B. POSE INTENT PRESERVATION

`PoseIntentContract` is a separate semantic contract. It records the requested intent, resolved safe family, required body-language signals, minimum visible signals, width/depth/asymmetry/energy/torso/arm/head requirements, and forbidden shortcuts. `PoseIntentGate` evaluates actual-image evidence; it does not infer success from prompt text. `POSE_VALID` requires both a passing `LegSeparationGate` and a `STRONG` or `ACCEPTABLE` `PoseIntentGate` result. A semantic miss remains `POSE_INTENT_FAIL`, not an anatomy failure.

The intent layer preserves elegant posture and asymmetry, sensual body confidence beyond clothing, relaxed asymmetry, low-energy signals, genuinely narrow stance, and genuine forward-foot depth. It cannot weaken the no-crossed-legs invariant. Pose-intent-only repair may change body language, stance width, foot depth, torso, shoulders, arms, head, and energy, then must rerun the leg gate. `PoseDiversityLedger` reports non-blocking safe-pose homogenization.

## 3. 核心视觉定义

### S1 Unmistakably Anime 2D hard gate

S1 只判断一个问题：最终图片是否明确、无歧义地属于 2D anime character illustration。它不是关键词检查，也不评价商业性、角色吸引力、服装质量、原创性或 NPC 风险。

必须同时满足：

- `face_abstraction`：面部保留 anime facial abstraction，鼻口为简化的 anime 处理，而非真实面部解剖。
- `hair_language`：头发以清晰的 2D anime hair grouping / graphic masses 组织。
- `skin_rendering`：皮肤是插画化、非摄影式表面，不以毛孔、真实皮肤纹理或真人质感为主导。
- `two_dimensional_rendering`：整体是明确的 2D illustrated rendering，不是 3D character render、cel-shaded 3D 或现实主义绘画。
- `overall_anime_read`：第一眼整体 anime read 明确，无需猜测媒介或风格来源。

任何一个检查失败、整体读感失败、证据不足或判断不确定，都必须 `FAIL`。`LOW` confidence 永远不能通过；半写实、3D anime render、写实肖像和 painterly realism 均属于失败。成熟角色、男性角色、窄眼或非幼态脸只要仍满足上述视觉语法，均可通过。

机器可读报告必须符合 `schemas/anime_style_gate.schema.json`，并记录 `gate_version: "2"`。该报告由 Codex 的视觉判断提供，运行时只验证结构和执行结果，不得用 Python 关键词推断图片风格。

Policy 的 canonical failure tokens 包括：`photoreal`、`semi_real`、`realistic_facial_anatomy`、`realistic_skin_rendering`、`3d_render`、`cel_shaded_3d`、`painterly_realism`、`western_realistic_concept_art`。

“Anime abstraction” 指以明确的二次元视觉语法进行设计：

- 以设计化的线稿、色块、形状语言、选择性细节和可读的轮廓承载信息。
- 面部、身体、服装、武器、材质、光照和表情都可以高度精致，但必须保持整体的动画化、插画化和设计化抽象。
- 商业级品质来自构图、轮廓识别度、配色层级、服装逻辑、材质区分、角色叙事和渲染完成度，不来自现实世界复制。
- `rendering_intensity` 只能改变细节密度、光影层次和表面完成度，不能改变抽象层级。

## 4. 禁止的风格升级

任何 Agent 都不得为了以下目标提高人物写实程度：

- 成熟感
- 人脸差异
- 身体差异
- 年龄差异
- 材质表现

这些差异必须全部在 anime abstraction 内实现。例如，可以使用眼型、眉形、脸部轮廓、发型、姿态、服装结构、比例化轮廓、色彩、图案、符号、边缘处理和非写实材质语言；不得使用皮肤毛孔、真实摄影皮肤、写实解剖、真实镜头景深或照片级面部建模来补偿。

“成熟”可以是角色设定、气质、姿态、服装、表情和叙事语义；它不是 photorealism 的授权理由。年龄和身体差异同样只能通过设计化比例、轮廓和造型表达。

## 5. 全局硬性拒绝条件

出现以下任一主导审美，输出即为无效，不得进入 Character Design 评分：

- photorealism
- semi-realism
- realistic portrait aesthetics
- western realistic concept art
- 3D-render aesthetics
- realistic facial anatomy
- realistic skin rendering
- cel-shaded 3D
- painterly realism

同样拒绝任何以真人照片、特定现实人物、具体已有角色、具体画师或具体作品为目标的复制性要求。部分区域的写实纹理也不能破坏整体二次元抽象；若写实表现成为主导，仍必须拒绝。

## 6. 允许的用户变化

用户可以改变以下内容，前提是它们仍服务于同一核心目标：

- `character archetype`
- `outfit`
- `silhouette`
- `color`
- `faction`
- `weapon`
- `personality`
- `rendering intensity`

用户也可以要求不同年龄带、成熟气质、脸部差异、身体差异或材质重点，但这些要求必须由 Designer 翻译为二次元设计变量。用户不能把角色改为写实风格，不能把核心 `style` 改成任意自由文本。

## 7. 管线强制执行

### Character Designer

Designer 负责把用户 brief 翻译成 Schema 允许的角色变量，并生成不可变的 `system_invariants` 与 `style.core`。它必须拒绝或改写任何要求写实化的表达，不能把冲突要求原样传给 ImageGen。

### ImageGen Skill

Skill 负责在每次生成前自动插入 mandatory anime style prefix 与 anti-realism constraints，并在生成后执行 validation。前缀、负向约束和校验规则不是用户可删除的 prompt 片段。

### Visual Critic

Critic 的第一步永远是 STYLE GATE。只有通过 STYLE GATE，才允许评价角色设计质量；STYLE GATE 失败必须直接 REJECT，并停止后续角色评分。

## 8. 最低通过标准

输出必须同时满足：

1. 具有高品质商业 2D 游戏角色设计的完成度和可读性。
2. 整体视觉明确属于二次元 anime abstraction。
3. 角色是原创概念，不针对具体既有角色或画师。
4. 人脸、身体、年龄、成熟度和材质差异均以二次元设计语法实现。
5. 未出现被禁止的主导审美，且已通过 STYLE GATE。

任一条件失败，输出只能标记为 `REJECT` 或 `REVISION_REQUIRED`，不得以“角色设计分数高”抵消风格失败。

## 9. Global Rendering Style 与 Gacha Style Gate

S1 Anime 2D Gate 与 Gacha Rendering Style Gate 是两个独立判断：S1 只确认二次元 2D 媒介；Gacha Gate 判断图片是否读作现代商业二游可玩角色立绘。因而一张图可以 S1 `PASS`，但因 editorial、character sheet、poster 或 concept-art 漂移而在 Gacha Gate `FAIL`。

默认 Global Rendering Style 为 `CONTEMPORARY_COMMERCIAL_GACHA_ANIME`，由 Policy 和 PromptCompiler 注入。它约束面部精修、材质区分、光影层级、渲染密度、焦点层级和商业角色卡面/standee presentation；它不限制角色内部的 Character Visual Style 多样性。

只有用户明确提出其他渲染媒介时才允许 override，并记录 `global_rendering_style_source: explicit_user_preference`。角色的 `minimalist`、`geometric`、`sporty` 或 `editorial` 只改变设计语言，不自动改成极简时装插画、平面海报或运动番设定图。

## 10. Regional Visual Language

“Anime” is a medium family, not a sufficient commercial style definition. “Commercial gacha” alone does not guarantee the intended regional visual language. The style architecture is:

1. `Global Rendering Style` — rendering medium and finish, default `CONTEMPORARY_COMMERCIAL_GACHA_ANIME`.
2. `Regional Visual Language` — commercial illustration grammar, default `EAST_ASIAN_CONTEMPORARY_GACHA`.
3. `Character Visual Style` — the character's own language, such as elegant, street, sporty, gothic, sensual, quiet, or strange.

Priority is explicit user style override → Global Rendering Style → Regional Visual Language → Character Visual Style → identity and implementation. Character Visual Style cannot replace the regional layer. The default regional layer is compiled as structured positive constraints: anime-first facial abstraction, restrained facial planes, modern East-Asian commercial gacha illustration grammar, stylized anatomically coherent bodies, character-design-first outfit construction, premium material separation, polished anime game lighting, and finished playable-character presentation.

Regional visual language is not character ethnicity. It governs illustration grammar, anime abstraction, rendering hierarchy, design grammar, and commercial presentation—not ethnicity, nationality, skin tone, occupation, world setting, or costume culture. Dark-skinned, tan, fantasy-ethnicity, European-fantasy, desert, aquatic, sci-fi, and beast-trait characters remain valid. East-Asian visual language must not silently become hanfu, kimono, qipao, sash, tassel, robe, or pseudo-oriental fantasy costume.

The regional layer protects diversity: mature men may remain elegant, slender, broad, rough, or older-looking without western superhero anatomy; mature women may remain mature, sensual, authoritative, or strong without infantile facial construction. Strong women express strength through shoulders, back, core, thighs, posture, stance, and outfit tension; `strength` is not a license for superhero or bodybuilder massing.

`RegionalStyleCritic` reviews the actual image, not the prompt. It records regional match, East-Asian gacha read, western-anime drift, western-concept-art drift, facial abstraction, body rendering, costume language, presentation, confidence, and result. `GachaStyleCritic` keeps the Global stage and adds Regional stage B; `STYLE_VALID` requires Global PASS and Regional PASS-equivalent. New drift types include `WESTERN_ANIME_STYLE_DRIFT`, `WESTERN_FANTASY_CONCEPT_DRIFT`, `WESTERN_SUPERHERO_ANATOMY_DRIFT`, `PSEUDO_ORIENTAL_FANTASY_DEFAULT`, `GENERIC_FANTASY_RPG_DRIFT`, `CHARACTER_SHEET_PRESENTATION_DRIFT`, `OUTFIT_FAMILY_COLLAPSE`, `BACKGROUND_PRESENTATION_COLLAPSE`, and `REGIONAL_STYLE_INFANTILIZATION`.

`Outfit Family Ledger` records outfit family, neckline, upper/lower structure, outer layer, waist, hanging cloth, cape, sash, trim, footwear, exposure, and legwear. Repetition across four or more images is a non-blocking `OUTFIT_FAMILY_COLLAPSE` diagnostic unless the user explicitly requested a uniform. Background fields have a separate non-blocking `BACKGROUND_PRESENTATION_COLLAPSE` diagnostic. `GENERIC_FANTASY_RPG_DRIFT` and `ARCHETYPE_SHORTCUT_REPLACEMENT` identify cliché replacement without banning a justified character-specific design. The current six archetype images are negative regression fixtures and human-labeled evidence only; they are not positive exemplars and must not be passed as future image references.

The default is recorded as `regional_visual_language_source: default_style_policy`. An explicit user request such as “western anime-inspired” records `regional_visual_language_source: explicit_user_override` plus a reason. Old artifacts without the field migrate in memory to the current policy default with `source: migrated_default`; old files are not rewritten. Formal contracts use generic visual descriptors, not named-game or named-artist imitation.

Migration records the old artifact version, effective regional value, provenance, timestamp, and whether a later user override occurred. `explicit_user_selection` and `benchmark_delegation` are valid provenance states and are not silently rewritten as human overrides.

## 11. Lower-Body Visual Design Space

Modesty is not the default solution to character design. Lower-body exposure, hosiery, leg accessories, open footwear, and barefoot designs are valid character-design tools for silhouette, personality, movement, sensuality, elegance, fantasy, and identity. Anti-template rules prevent repetitive sexualization patterns; they must not suppress adult sensual, stylish, or unconventional choices.

The formal lower-body variables are `exposure_strategy`, `legwear_family`, `leg_accessory_family`, `footwear_family`, `foot_visibility`, `visual_reason`, `relationship_to_character_style`, `relationship_to_pose`, and `repetition_risk`. The vocabulary is open-ended; the listed families are design language, not a closed enum and not a demand for novelty.

Adult characters may use sheer/opaque/patterned/colored tights, thigh-highs, leg rings, straps, bare thighs, barefoot construction, sandals, flats, heels, sneakers, boots, asymmetry, or other coherent choices. Male characters receive the same design space and must not default to trousers plus boots. Clearly juvenile characters may use ordinary socks, tights, sandals, sneakers, or barefoot designs, but not fetishized garters, sexualized stocking framing, or erotic leg emphasis. Fanservice level and lower-body coverage are independent variables.

`LowerBodyDesignReview` checks the selected variables, design reasons, style/pose relationship, repetition risk, and genericness risk. A generic pants-plus-boots pair without a character-specific reason receives a risk note, not an automatic rejection. `Visual Grounding QA` compares Final Design with the actual image: barefoot rendered as boots is `FOOTWEAR_GROUNDING_FAIL`, selected legwear rendered as bare legs is `LEGWEAR_GROUNDING_FAIL`, and a missing leg accessory is `LOWER_BODY_ANCHOR_MISS`.
