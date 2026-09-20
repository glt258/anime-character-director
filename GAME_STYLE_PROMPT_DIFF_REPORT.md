# GAME STYLE PROMPT DIFF REPORT

Status: `IMPLEMENTATION_VALIDATION`

This report uses one fixed character specification and compares the five
rendering modes. The normalized character block hash is constant across all
modes:

`bf719c5fde92181cb8fe9fc09df1c7929247764d439116582a90ae2ecdbe111e`

Fixed character block:

```text
adult woman with a compact signal pendant
hair: pink; hair style: long ponytail; eyes: teal; body style: petite
clothing: futuristic streetwear; palette: pink and graphite
footwear: sneakers; sexiness: high; pose: stable open stance; background: city dusk
```

## Mode comparison

| Mode | Character block | Global contract | Optional game fragment | Projected rule count |
|---|---|---|---|---:|
| Global default | unchanged | `CONTEMPORARY_COMMERCIAL_GACHA_ANIME` | none | 0 |
| Genshin Impact | unchanged | unchanged | detail clusters; surface frequency; semi-hard edges; hybrid value construction | 4 |
| Zenless Zone Zero | unchanged | unchanged | softened edges; continuous tonal gradients; medium detail distribution; localized surface accents | 4 |
| Wuthering Waves | unchanged | unchanged | high detail distribution; high surface frequency; variable edge strategy; variable shading strategy | 4 |
| Neverness to Everness | unchanged | unchanged | variable edge strategy; variable shading strategy; variable detail-density strategy | 3 |

## Diff boundary

The only intended prompt delta is the `## OPTIONAL GAME RENDERING STYLE`
section and its provenance metadata:

```json
{
  "game_style_id": "wuthering_waves",
  "profile_version": "game_style_profile_v1",
  "projection_version": "game_style_projection_v1",
  "source_claim_ids": [
    "art_direction_detail_density_high",
    "rendering_texture_detail_high",
    "rendering_edge_treatment_semi_hard",
    "rendering_shading_hybrid"
  ]
}
```

The character concept, hair, eyes, body, clothing, palette, footwear,
sexiness, pose, background, and nonhuman choices remain external to the
fragment. The global rendering contract, pose safety, anatomy gates, and
literal-copy protection remain active in every mode.

Unsupported game names do not create a speculative fragment: the original
request is retained in provenance and the prompt falls back to the global
contract.
