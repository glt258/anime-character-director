# GAME STYLE PROMPT DIFF REPORT v2

## 固定 fixture

五次生成固定以下内容；只允许 rendering specialization 改变人物主体的画法：

- Character：`adult woman; pink shoulder-length hair; teal eyes; petite build; white and navy short jacket; black shorts; flat ankle boots; no stockings; human; stable open stance`
- Background：`simple neutral commercial character showcase background, light neutral architectural panels, subtle depth, no game-specific landmarks, no fantasy city, no futuristic skyline, no faction symbols, no environmental storytelling, background secondary`
- Lighting：`neutral soft directional studio-like daylight, stable key direction, moderate overall contrast`
- Camera/pose：同一 full-body character showcase framing 与 stable open stance。

## 五段 prompt contract

1. `CHARACTER IDENTITY`：五模式完全相同。
2. `GLOBAL RENDERING MEDIUM`：五模式完全相同。
3. `RENDERING SPECIALIZATION`：仅注入 profile 的 technical HOW rules；game name 只作为 metadata/debug `game_specialization`，不作为视觉规则。
4. `BACKGROUND SPECIFICATION`：五模式完全相同，且禁止 game-specific landmarks、symbols、environmental storytelling。
5. `POSE / CAMERA / NEGATIVE CONSTRAINTS`：五模式完全相同。

## Rendering specialization diff

| Mode | 专属人物主体 HOW delta |
|---|---|
| Genshin | firm contours；controlled crisp/soft interior separators；clean primary shadow blocks；restrained secondary gradients；high-frequency form detail。 |
| ZZZ | softened contours；dissolved interior separators；continuous tonal modeling；continuous gradients；moderate frequency with quiet intervals。 |
| WuWa | alternating contour and edge strategies；variable primary shadows；recurring gradient-vs-shadow alternatives；visible high-frequency secondary clusters。 |
| NTE | multiple recurring edge/shadow strategies；high surface frequency gated by localized grouping，保持 subtle 而非强行制造差异。 |

完整 imagegen prompt 归档：

- [Global prompt](prompts/global.imagegen_prompt.txt)
- [Genshin prompt](prompts/genshin.imagegen_prompt.txt)
- [ZZZ prompt](prompts/zzz.imagegen_prompt.txt)
- [WuWa prompt](prompts/wuthering.imagegen_prompt.txt)
- [NTE prompt](prompts/nte.imagegen_prompt.txt)

## Validity boundary

先验证 character preservation，再验证 rendering difference。若差异主要来自背景、构图、服装、身体或人物内容，不能计入 `CLEAR_CHARACTER_RENDERING_DIFFERENCE`。本轮结果为 `CHARACTER_PRESERVATION=PASS`、`CLEAR=3/4`、`STYLE_DIFFERENCE_VALIDITY_GATE=PASS`。
