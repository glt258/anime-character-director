# Anime Character Director

**A Codex-native Skill for human-guided 2D anime gacha character design and art direction.**

**From generic AI anime characters to identity-driven contemporary gacha character design.**

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

### Anime 2D Hard Gate

Preserves unmistakable 2D anime abstraction and avoids photorealism, semi-realistic drift, and 3D-render aesthetics.

### Human-Guided Creative Expansion

Interactive CREATE expands 4–6 Character Directions by defaulting to five, then presents 4–6 Art Directions by defaulting to four. It pauses at both Human selection checkpoints and does not silently choose taste.

### Front-Facing Character Standee

The main body stays frontal for standard character illustration. Dynamism comes from arms, hair, cloth, weapons, VFX, and secondary silhouettes instead of rotating the torso into an unreadable 3/4 pose.

### Contemporary Gacha Design Principle

Identity comes before pagegame luxury: macro shapes, head identity, costume architecture, detail islands, controlled color architecture, material hierarchy, and one primary iconic anchor. Adult sensuality remains available without using ornament stacking as a rarity signal.

### Structural Fantasy Design

Abilities enter silhouette, body, costume, negative space, and shape language instead of becoming only glow, crystals, shards, or generic VFX.

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

```text
$anime-character-director

Design an original adult female anime gacha character.

I want:
- urban fantasy
- dangerous but elegant
- strong player appeal

Use interactive mode.
Do not choose the final direction for me.
```

The Skill stops after Character Explore until Human selection. After selection it stops again after Art Explore. Only the approved/mixed direction proceeds to Final Visual Direction and, when the host supports it, the existing local Runtime → PromptCompiler → built-in `$imagegen` path.

## Runtime and boundaries

This package is the reusable Codex Skill layer. It bundles the human-readable Anime Style Constitution and its machine-readable style policy, but does not bundle the benchmark project's Python Runtime, planning schemas, tests, caches, private artifacts, external Agent, server, LLM API wrapper, image API, or ComfyUI pipeline. A host project may provide a local Runtime preflight; the Skill's creative behavior remains usable without copying the entire benchmark repository.

S1 Anime 2D Hard Gate remains the only current visual hard gate. The Commercial Gacha Profile is vocabulary and possibility expansion, not a second gate. After generation, present the image and stop for Human Review; do not automatically redesign, regenerate, optimize, or score commercial appeal.

## Image generation

Anime Character Director is designed to work with Codex built-in `$imagegen`. It does not require an external image API, ComfyUI, or an external Agent server. `$imagegen` is the renderer, not the Character Designer; character design happens before image generation.

## Current Status

Implemented: Anime 2D Hard Gate guidance; Human-guided Character and Art Direction expansion; Human selection and mixing; Front-Facing Character Standee guidance; Contemporary Gacha Design Principle; Macro-first design; Detail Islands; Color Architecture; Material Hierarchy; Structural Fantasy Design; One Primary Iconic Anchor; optional auto planning mode; and Codex built-in `$imagegen` integration.

The Commercial Gacha Visual Profile is creative vocabulary only, not a hard Gate 2.

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
├─ docs/
│  └─ ANIME_STYLE_CONTRACT.md
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
