# GAME STYLE WEAKNESS DIAGNOSIS

版本：`GAME_STYLE_STRENGTHENING_V2`
日期：2026-09-20
范围：`D:\anime-character-director-release` 的 v1 运行时、四个 packaged profile、PromptCompiler 与 v1 人工验收产物。
基线：`c632e13befc2069886ea63ca33880584568532a5`

## 结论

v1 的失败不是“图像模型偶然画得不明显”，而是投影契约在进入图像模型前已经把差异压缩成少量抽象、相互重叠的 HOW 句子。四个 profile 的规则数量为 Genshin 4、ZZZ 4、WuWa 4、NTE 3；规则主要集中在 `edge_treatment`、`shading`、`detail_density`、`texture_detail`，缺少可落到角色脸、发丝、皮肤、服装材质、内轮廓和局部明暗组织的结构化渲染槽位。v1 图片中可见的差异因此主要落在背景和整体气氛，而不是角色主体。

本报告先于 v2 代码修改保存。v1 报告 `qa/game_style_human_acceptance_v1/GAME_STYLE_HUMAN_ACCEPTANCE_V1_RESULT.md` 保持原样，v1 的 `SUBTLE_DIFFERENCE` 不再作为 v2 的有效通过标准。

## 十项原因诊断

### 1. 现在的 rendering rules 是否太少？

是。四个 profile 的有效投影只有 3–4 条，且不是互相独立的角色渲染控制量：`edge_treatment` 与 `shading` 是宽泛风格标签，`detail_density` 与 `texture_detail` 也容易在同一批表面上重复。投影虽然满足 v1 的数量预算，却没有覆盖足够多的角色主体区域。v2 需要把规则变成固定槽位，并限制为每个 profile 5–8 条 core、0–2 条 supporting、总数不超过 10 条。

### 2. 是否大量规则只是 abstract language？

是。当前文本如“Visual detail density is distributed...”和“Value construction combines...”描述的是统计倾向，不规定在哪些角色表面、以什么顺序、用什么可观察的画法执行。抽象标签可以保留为 provenance/debug，但必须编译成 `LINE_CONTOUR`、`PRIMARY_SHADOW`、`SECONDARY_GRADIENT`、`SKIN_RENDERING`、`HAIR_RENDERING` 等技术槽位；没有可靠证据的槽位要明确写成 `no reliable discriminator`，不能用想象补齐。

### 3. Compiler 中 game style 是否位于较弱位置？

是。当前 PromptCompiler 把 game rules 放在 `## OPTIONAL GAME RENDERING STYLE`，并且只输出一串 `instructions`；游戏名和自然语言描述容易被模型当作弱元数据。v2 应输出明确的 `Rendering specialization:` 技术段，游戏 ID 只进入 metadata/debug trace；差异段要位于角色身份与全局渲染契约之后、负面约束与 QA 约束之前，并声明只作用于角色的画法 HOW。

### 4. 是否被 global style contract 同质化？

部分是。全局 `CONTEMPORARY_COMMERCIAL_GACHA_ANIME` 是必要质量底线，但当前 profiles 又普遍排除相同的 color/depth baseline，最后只剩相近的边缘、阴影、细节词。编译器没有把“质量底线”和“游戏增量”分成可审计的两个段落，也没有阻止 global contract 复制 game delta。v2 必须保留 global contract 的可读性与商业二游约束，但不得把它扩写成具体游戏的边缘、阴影、细节规则。

### 5. 是否在投影阶段被压缩？

是。`project_game_style()` 当前只从两个 YAML 列表抽取文本，按少数 claim token 做冲突删除；它没有槽位、强度、对比句或“无可靠区分”状态。尤其 NTE 的柔性特征被压缩为 3 条 supporting 的“allow multiple...”句子，几乎不给图像模型任何执行方向。v2 投影要保留槽位、`absolute_instruction`、`contrastive_instruction`、`confidence`、`strength`、`source_claim_ids` 以及 applied/adapted/dropped trace。

### 6. 是否 image prompt 只强化了 background？

是，v1 人工产物显示五图均保持角色核心字段，但可见差异更多来自现代建筑/环境气氛；这不能算 Game Style 的主体渲染差异。v2 五向 fixture 必须锁死同一中性背景、同一光照意图、同一姿势与同一角色内容，并在 acceptance 中单独检查主体 crop；背景变化、姿势变化、服装变化、体型变化、发色变化不计分。

### 7. 各游戏现有 claims 是否映射不到具体 character rendering？

大部分是。研究 profile 的稳定 claim 主要覆盖 edge、shading、color structure、texture/detail、depth、shape hierarchy、surface organization；其中 color/depth 在多个游戏间重叠，不能直接当作独特游戏差异。可可靠映射的方向是角色表面上的轮廓、主阴影/次级渐变、细节频率与层级组织；`SKIN_RENDERING`、`HAIR_RENDERING`、`EYE_RENDERING`、`MATERIAL_SPECULAR`、`POST_PROCESSING` 等若没有 profile-specific 证据，应记录 `no reliable discriminator`，而不是编造游戏专属角色内容。

### 8. projector 是否过滤了真正的 style delta？

是。冲突过滤只按 `edge_treatment`、`shading_strategy`、`detail_density`、`texture_detail` 的 claim ID token 做整条删除；它无法区分同一槽位内可兼容的局部表达，也没有记录“适配”与“丢弃”的理由。v1 因此既可能保留过于泛化的句子，也可能在用户指定某个渲染属性时失去整组可用差异。v2 先处理用户约束，再对每条结构化规则给出 `applied`、`adapted`、`dropped` 与 `conflict_reason`。

### 9. 不同 profile 之间是否语义重叠严重？

是。Genshin、WuWa 和 NTE 都可能投影“高细节/层级组织/边缘与明暗变化”，ZZZ 与 NTE 又都可能投影“柔和/渐变/不固定”。在没有槽位对照句的情况下，模型收到的是同一组“干净线条、细节丰富、材质高光、柔和渐变”的近义改写。v2 将为每条规则保存相对于 Global 的 contrastive HOW 句，并增加去重测试，禁止只有 clean line、detailed shading、good materials、rich highlights 这类泛化词的 profile 通过。

### 10. v1 的 WEAK_PASS 为什么不能接受？

因为 v1 的“SUBTLE_DIFFERENCE”没有证明差异位于角色主体，也没有排除背景、气氛、后处理、构图或随机细节造成的假差异。v2 的有效标准是四个游戏 profile 中至少三个相对 Global 达到 `CLEAR_CHARACTER_RENDERING_DIFFERENCE`，同时 character preservation、pose、background、lighting、clothing/body/hair/eye 等锁定项全部通过。任一只在背景或全局氛围上不同的结果必须标记为 `STYLE_TOO_WEAK`，不能升级为通过。

## 证据边界与 v2 设计约束

- 证据来自研究仓库中已审核的四游戏 profile 及其 claim ID；runtime 只会打包轻量 profile，不会依赖研究仓库。
- 研究没有为所有 12 个结构化槽位提供独立、稳定、游戏唯一的证据；这些槽位必须允许 `no reliable discriminator`。
- Game Style 永远是 rendering HOW 增量，不得改变角色的 WHAT：身份、发色、发型、眼睛、体型、服装、鞋履、姿势、性感度、非人特征和背景选择。
- Global 是质量底线；v2 fixture 的背景与光照是外部锁定条件，不属于游戏差异来源。
- BACK 修复必须保留本轮 Human-owned selections，并在游戏切换时使旧 projection、compiled prompt 和 derived trace 全部失效，避免 WuWa 规则残留。
- Unsupported game style 必须保留用户原始请求与 fallback reason，但解析为全局渲染，不得映射成 Genshin，也不得被显式覆盖率 Gate 当作 null HARD 值阻断。
