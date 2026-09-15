# Interaction Demo Fixtures

These deterministic text-only fixtures exercise the v1 interaction contract. They are recipes rather than generated image assets; no fixture calls `$imagegen`.

- `quick.json`: short input resolves directly to `GENERATION_READY`.
- `ai_decide.json`: full exploration is resolved by `delegated_ai`.
- `user_decide.json`: Character `SELECT`, Art `MIX`, then Visual Preference overrides plus `USE_ALL_RECOMMENDED` resume one session.

Gate ids are filled by the runtime at execution time. The event payloads are stable and can be replayed against the persisted `session.json`.
