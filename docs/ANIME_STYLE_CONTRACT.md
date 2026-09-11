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
