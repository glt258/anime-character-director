# Advanced CREATE dry-run

## User Request

都市近未来女性战斗角色；职业是暴雨中的电网救援员；性格冷淡但会优先保护陌生人；保留白发、金瞳、电属性；禁止无功能的随机腰带、单侧大腿袜和纯装饰外套。

## Immutable requirements

- 保留：都市近未来、女性表达、白发、金瞳、电属性、电网救援职业、冷淡但保护他人的人格反差。
- 禁止：没有功能解释的随机腰带、单侧大腿袜、纯装饰外套。
- 自主补全：宽大防护轮廓、移动安全区 mantle、低稳定救援靴，因为它们都从职业和功能故事推导出来。

## Validation handoff

```text
CharacterDesignSpec → Design self-review
                  → Runtime validation: VALID
                  → PromptCompiler (style-owned / character-owned separated)
                  → ready for $imagegen after user confirms generation
```

本示例不调用 `$imagegen`，不产生图片。
