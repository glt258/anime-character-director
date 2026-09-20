# Repository Development Location Policy

The D: drive Git repository at `D:\\anime-character-director-release` is the
only development source of truth for this project.

`C:\\Users\\30931\\.codex\\skills\\anime-character-director` is an installed
runtime copy only. Never implement permanent features, bug fixes, Skill
changes, profile changes, schema changes, tests, or documentation there.

Required lifecycle:

```text
D: development repository
  -> targeted tests and human acceptance
  -> git commit
  -> git push
  -> GitHub canonical repository
  -> C: installed copy git pull or reinstall
  -> installed-copy verification
```

If a problem is discovered while running the C: copy, reproduce and fix it in
the D: repository first. C: may receive a temporary diagnostic edit only when
it is absolutely required; that edit must be discarded or ported to D:
immediately and must never become the canonical implementation.

`D:\\anime-lora-lab` remains the research/evidence repository. Do not copy its
raw references, observations, inventories, or evidence JSON into this Skill;
only reviewed lightweight production profiles may be packaged here.

## USER PROMPT SUPREMACY

Priority order: `Explicit User Prompt > Game Style Profile > Global Style Defaults`.

Explicit user instructions have the highest semantic and visual priority.
Game Style Profile is a soft stylistic prior. If Game Style conflicts with an
explicit user request, the user request wins. The conflicting profile rule
must be adapted, weakened, partially applied, or dropped. Never modify the
user's requested character merely to make it more typical of the selected
game. This applies to character content and rendering properties.

Examples covered by the Game Style acceptance contract:

- A game reference may trend toward mature, fuller-bodied characters while
  the user requests a petite, youthful character; preserve the user request
  and inherit only compatible rendering language.
- The user may request soft, low-contrast lighting while a profile prefers
  stronger contrast; preserve the user's lighting request and drop the
  conflicting profile rule.

## Development Guard

Development, migration, release, and profile-update scripts must resolve the
Git repository root before mutating project files. If the root is below
`.codex\\skills\\`, the script must stop with an installed-copy warning. The
guard is development-only and must not be imported by normal Skill runtime
paths.

Do not use `git reset --hard`, `git clean -fd`, force-push, or release/tag
commands as part of migration without explicit confirmation and a verified
backup. This migration intentionally stops before commit, push, tag, and
release.
