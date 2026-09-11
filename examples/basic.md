# Basic CREATE dry-run

## User Request

白发、金瞳、电属性、冷淡女性、都市近未来。

## CharacterDesignSpec 摘要

- Core fantasy：把战斗当作城市电网维修工单处理的故障处理员。
- Face identity：短圆矩形脸、窄水平眼、截断下巴、单侧眉形标记；全部为 anime geometry。
- Silhouette：紧凑上重矩形；单侧大型维护袖是 `silhouette_anchor`。
- Outfit logic：基础工作服、绝缘功能层、维护袖 identity layer；没有无理由的露脐装/短裤/绑带组合。
- Visual anchor：单侧 oversized maintenance sleeve；三秒记忆为“带一只巨型维修袖的电网技师”。

## Runtime dry-run

```text
CharacterDesignSpec → validate-design → VALID / LOW
PromptCompiler → PromptBundle
Image generation: not called in this example
```
