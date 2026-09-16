# anime-character-director

`A Codex Skill for designing and generating production-oriented commercial anime/gacha game characters.`

**v1.0.0 — `ANIME_CHARACTER_DIRECTOR_V1_0_0 = RELEASED`**

Anime Character Director turns one character request into a coherent commercial 2D anime-game character design and, after the design is resolved, a Codex built-in `$imagegen` result with technical quality checks. The default mode is `AI_DECIDE`.

## Three Creation Modes

### QUICK

Fast automatic design and generation with the fewest interactions.

### AI_DECIDE

Full design reasoning with AI selecting the visual direction automatically. This is the default mode.

### USER_DECIDE

Human-led design through Codex native selection UI. The user chooses or customizes the high-impact directions; the same workflow continues automatically after each choice.

All three modes preserve the contemporary commercial gacha anime style contract, explicit constraints, front-facing standee readability, and post-generation quality audit.

## Visual Evolution

The same project evolved through several distinct design failures and corrections. These examples show why Anime Character Director is more than a prompt expander.

<table>
<tr>
<td align="center"><b>01 · Baseline</b></td>
<td align="center"><b>02 · Player Appeal V1</b></td>
<td align="center"><b>03 · Creative V2</b></td>
<td align="center"><b>04 · Current</b></td>
</tr>
<tr>
<td><img src="assets/evolution-01-baseline.png" alt="Baseline: occupation-first generic anime character" width="240"></td>
<td><img src="assets/evolution-02-player-appeal-v1.png" alt="Player appeal V1: premium but generic gacha character" width="240"></td>
<td><img src="assets/evolution-03-pagegame-drift.png" alt="Creative V2: original premise with pagegame drift" width="240"></td>
<td><img src="assets/evolution-04-current.png" alt="Current: front-facing contemporary gacha standee" width="240"></td>
</tr>
<tr>
<td valign="top"><b>Generic convergence</b><br>Occupation-first design.<br>White-hair + techwear template.<br>Low character fantasy.</td>
<td valign="top"><b>Player appeal introduced</b><br>Stronger body framing and premium presence.<br>Still generic sci-fi gacha.</td>
<td valign="top"><b>Creativity unlocked</b><br>Original character premise.<br>But pagegame/MMORPG drift and twisted pose remain.</td>
<td valign="top"><b>Structure-driven design</b><br>Front-facing standee.<br>Cleaner contemporary gacha language.<br>Structural fantasy design.</td>
</tr>
</table>

> **Each failure became a design rule.**
>
> Anime Character Director was built by repeatedly identifying why a technically good anime image still failed as a memorable gacha character.

> The goal is not to maximize detail.
> The goal is to maximize identity.

## What changed?

### 01 → 02: Player appeal

The early system overvalued profession, plausibility and functional clothing.

The first major correction was simple:

**A playable gacha character is not an NPC wearing expensive equipment.**

Player fantasy, attraction, silhouette and emotional appeal became first-class design concerns.

### 02 → 03: Creative freedom

The next problem was AI conservatism.

The system was good at producing coherent characters, but coherence was suppressing imagination.

The philosophy changed to:

> **Codex expands. Human selects.**

AI explores unusual possibilities. Human judgment decides which direction deserves to survive.

This produced much stronger character premises, including the “future selves hunting the present self” concept.

### 03 → 04: Art-direction discipline

Creative concepts alone were not enough.

The third version exposed two new problems:

- browser-game / MMORPG visual drift
- cinematic 3/4 twisted poses

The Skill therefore added:

- Front-Facing Standee Principle
- Contemporary Gacha Design Principle
- Macro-first design
- Detail Islands
- Color / Material Architecture
- Structural Fantasy Design
- One Primary Iconic Anchor

The result is cleaner, more readable, more character-specific, and closer to contemporary anime gacha standee design.

Current iteration significantly improves:

- frontal readability
- contemporary gacha language
- controlled detail density
- structural fantasy expression

Identity refinement remains an active area of development. We are still researching stronger head identity, costume-specific identity, and deeper integration of fantasy mechanics into the body / outfit.

## What problem it solves

Modern image models can render polished anime illustrations, but character design often converges toward generic anime faces, repeated white-hair/techwear templates, browser-game or MMORPG visual language, ornament density instead of identity, cinematic 3/4 poses instead of readable standees, and safe predictable concepts.

Anime Character Director adds a design layer before image generation. It is not a prompt expander. It guides possibility expansion, Character Direction exploration, Human selection, Art Direction exploration, Human mix/selection, contemporary gacha visual language, front-facing standee composition, and anime 2D style preservation.

## Codex expands. Human selects.

```text
User Idea
    ↓
5 Character Directions
    ↓
Human Select / Mix
    ↓
Character Planning
    ↓
4 Art Directions
    ↓
    Human Select / Mix
    ↓
    Visual Preference Sheet
    ↓
    Human Select / Mix / Custom / Delegate
    ↓
    Human Audit + Visual Preferences Locked
    ↓
    Final Visual Direction
    ↓
$imagegen
    ↓
S1 Anime 2D Hard Gate
    ↓
Human Review
```

AI does not automatically decide taste. Human owns selection, rejection, mixing, aesthetics, and the question: “would I pull this character?”

## Human Mix

Mixing is a first-class workflow, not an exception. For example, a human may keep **B's silhouette**, take **D's head identity**, preserve **A's material language**, and introduce **C's fantasy intrusion**. The Skill treats that combination as the approved direction and carries it forward without silently normalizing it.

## Major design features

### Character Design

Design original adult 2D anime/gacha characters from premise, identity, silhouette, costume architecture, fantasy logic, and player-facing appeal.

### Human-Guided Creative Expansion

Interactive CREATE expands 4–6 Character Directions by defaulting to five, then presents 4–6 Art Directions by defaulting to four. It pauses at Human selection checkpoints and does not silently choose taste.

### Standee-First Art Direction

The default deliverable is a clear, recognizable, reusable character standee. Character identity comes before cinematic presentation; scene-heavy art is an explicit extension.

### Front-Facing Standee

The main body stays readable from the front for standard standees. Dynamism comes from arms, hair, cloth, weapons, effects, asymmetry, and controlled weight shifts rather than unreadable torso rotation.

### Contemporary Gacha Design

Identity comes before pagegame luxury: macro shapes, head identity, costume architecture, detail islands, controlled color architecture, material hierarchy, and one primary iconic anchor.

### Identity Pass

The lightweight Identity Pass turns a selected direction into a specific woman before generation and records what must remain recognizable.

### Character Canon

Human-approved Canon and a Master Reference anchor later visual variations without silently redesigning the character.

### Same-Character Standee

Canon-preserving portraits, half bodies, expressions, front/side/back references, and standee pose variants keep identity stable across presentations.

### Variants

Controlled hair, expression, pose, costume, legwear, footwear, color, silhouette, accessory, and fantasy-structure variations remain branchable and Human-selectable.

`standee_pose_variant` is the pose-focused subtype inside `variants`: four text-only standing-pose options come first, Human chooses or mixes, and only then is the selected standee generated.

### Anatomy Integrity

Post-generation technical QA separates visible anatomy failures from aesthetic preferences and keeps repairs bounded to anatomy.

### Human Authority

AI expands, compares, critiques, and recommends; Human selects, mixes, approves, rejects, and decides Canon.

### Optional Presentation Extensions

Promotional key art, combat art, ultimate art, story illustration, and cinematic compositions are supported only when explicitly requested. They are not additional modes or the default product scope.

## Installation

This repository is itself the Skill root. Clone or download it into the user-level Codex Skills directory; do not add an extra `skills/anime-character-director/` nesting layer.

### Git clone

```powershell
git clone https://github.com/glt258/anime-character-director.git "$HOME\.codex\skills\anime-character-director"
```

On Windows, use the user-level Skills directory, for example:

```powershell
git clone https://github.com/glt258/anime-character-director.git "%USERPROFILE%\.codex\skills\anime-character-director"
```

### Download ZIP

Download the repository ZIP, extract it, and place the extracted `anime-character-director` folder in the user-level Skills directory used by your Codex installation.

## Quick start

### QUICK example

```text
用 anime-character-director 的 QUICK 模式设计一个冷静的都市幻想少女角色，直接生成最终立绘。
```

### AI_DECIDE example

```text
用 anime-character-director 的 AI_DECIDE 模式设计一个外向的机械背景少女角色，让 AI 完成所有设计决策。
```

### USER_DECIDE example

```text
用 anime-character-director 的 USER_DECIDE 模式设计一个兽人女性角色，我想逐步选择角色设计方向。
```

USER_DECIDE 会自动出现 Codex 原生选择 UI；用户选择后，Skill 继续同一个持久化工作流。只有完整设计通过本地 Runtime 与 PromptCompiler 验证后，才进入 `$imagegen` 和质量审计。

## Runtime and boundaries

This package is the reusable Codex Skill layer. It bundles the human-readable Anime Style Constitution, machine-readable style policy, Visual Preference runtime gate, preference schema, report format, and focused tests. It does not bundle an external Agent, server, LLM API wrapper, image API, or ComfyUI pipeline. A host project may add a larger Runtime preflight around the bundled ownership gate.

The local runtime preserves the S1 Anime 2D, Regional Style, Lower-Body, Leg Separation, Pose Intent, and Playable Character Design contracts. Its handoff boundary is `GENERATION_READY`; the Codex Skill orchestration then invokes built-in `$imagegen`, runs the existing Style and Anatomy quality audit, and reports technical uncertainty without silently redesigning the character.

## Architecture

```text
Codex Skill
    ↓
Mode Router
    ├── QUICK
    ├── AI_DECIDE
    └── USER_DECIDE
           ↓
      Codex Native Interaction UI
    ↓
Character Design Runtime
    ↓
Constraint System → PromptCompiler
    ↓
Codex built-in $imagegen
    ↓
Style + Anatomy + Constraint Fidelity Audit
```

This is a Codex Skill, not an independent Agent, server, or external image API.

## Change Reporting Contract

Every development response states, briefly and in plain Chinese: **这次在干什么**, **为什么要改**, **这次具体改了什么**, **这次没动什么**, **检查结果**, **现在项目到哪了**, and **下一步**. Explain the effect before file names, and translate technical English on first use when useful. This keeps the Human informed about scope and state; it does not create a new runtime gate.

## Image generation

Anime Character Director is designed to work with Codex built-in `$imagegen`. It does not require an external image API, ComfyUI, or an external Agent server. `$imagegen` is the renderer, not the Character Designer; character design happens before image generation.

## Current Status

`ANIME_CHARACTER_DIRECTOR_V1 = RELEASE_READY`; the shipped version is `v1.0.0`. Style Contract, Character Design Runtime, Pose System, Persistent Interactive Workflow, Codex Native Interaction UI, Dynamic Candidate Generation, Explicit Constraint System, Compound Negation Parsing, PromptCompiler, and Generation Boundary are accepted for this release.

Pose System v1 is `ACCEPTED / FROZEN` for the current fast-generation production baseline. See [Pose System v1 Acceptance](docs/POSE_SYSTEM_V1_ACCEPTANCE.md). This is an accepted baseline, not a claim that every future pose problem is completely solved; detailed pose refinement remains post-v1 work.

Interaction System + Three Creation Modes v1 is `THREE_MODE_INTERACTION_SYSTEM_V1_ACCEPTED` / `ACCEPTED / FROZEN`. `QUICK`, `AI_DECIDE`, and `USER_DECIDE` share one persisted pipeline; the natural-language layer is `INTERACTION_NL_V1_ACCEPTED`; the runtime handoff stops at `GENERATION_READY` before Skill-level `$imagegen` execution. See [Three-Mode Interaction System v1 Acceptance](docs/THREE_MODE_INTERACTION_V1_ACCEPTANCE.md).

Generation Quality Benchmark v2 is `COMPLETE_WITH_REPLAYED_USER_DECIDE_DISCLOSURE`. Its results are internal release evidence, not required user knowledge. The four USER_DECIDE comparison rows use replayed previously recorded real-human selections under the frozen runtime; they are not four new live UI sessions. See [Benchmark v2 Summary](docs/BENCHMARK_V2_SUMMARY.md).

LoRA status is `LORA_NOT_PRIMARY_BOTTLENECK`. Step1000, diversity research, mode-collapse research, and broader benchmark expansion are post-v1 roadmap items, not release blockers.

Implemented: Standee-first product scope; Anime 2D Hard Gate guidance; three-mode Interaction System; Human-guided Character and Art Direction expansion; Human selection and mixing; Design Ownership Policy; Visual Preference Gate; Visual Preference Sheet and report; Visual Diversity Control; Human Audit Policy; Front-Facing Character Standee guidance; Contemporary Gacha Design Principle; Identity Pass; Character Canon; Same-Character Standee; controlled Variants including four-direction `standee_pose_variant` planning; Anatomy Integrity; Human Authority; Optional Presentation Extensions; Macro-first design; Detail Islands; Color Architecture; Material Hierarchy; Structural Fantasy Design; One Primary Iconic Anchor; plain-Chinese Change Reporting Contract; and Codex built-in `$imagegen` integration.

The historical Commercial Gacha Visual Profile remains vocabulary/reference material. The runtime Gacha Rendering Style Gate now has Global and Regional stages; both must pass before `STYLE_VALID`.

## Disclaimer

This project is an independent AI-assisted character-design tool. It is not affiliated with, endorsed by, or associated with HoYoverse, miHoYo, Zenless Zone Zero, or any other commercial game studio or title. The example images are AI-generated development examples. The Skill is intended for original character creation.

## Repository layout

```text
anime-character-director/
├─ SKILL.md
├─ README.md
├─ LICENSE
├─ agents/
│  └─ openai.yaml
├─ config/
│  └─ anime_style_policy.yaml
├─ schemas/
│  └─ visual_preference_sheet.schema.json
├─ runtime/
│  ├─ interaction_runtime.py
│  ├─ natural_language_interaction.py
│  └─ visual_preference_runtime.py
├─ docs/
│  ├─ ANIME_STYLE_CONTRACT.md
│  ├─ INTERACTION_SYSTEM.md
│  └─ THREE_MODE_INTERACTION_V1_ACCEPTANCE.md
├─ references/
│  ├─ character-design-guide.md
│  └─ workflow.md
├─ examples/
│  ├─ basic.md
│  └─ advanced.md
├─ assets/
│  ├─ evolution-01-baseline.png
│  ├─ evolution-02-player-appeal-v1.png
│  ├─ evolution-03-pagegame-drift.png
│  └─ evolution-04-current.png
└─ scripts/
   └─ README.md
```

## License

MIT. See [LICENSE](LICENSE).
