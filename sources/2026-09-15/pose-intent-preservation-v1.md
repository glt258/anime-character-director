---
ingested: 2026-09-15
wiki_pages:
  - wiki/architecture/pose-intent-preservation.md
  - wiki/architecture/skill-and-runtime.md
  - wiki/constraints/anatomy-pose-and-footwear.md
  - wiki/roadmap/current.md
---

# anime-character-director — Pose Intent Preservation v1

继续当前 `anime-character-director` 项目。

当前已经完成并封板：

# HARD NO-CROSSED-LEGS

当前状态：

`NO_CROSSED_LEGS_HARDENED_ACCEPTED`

实际压力测试结果：

- 6/6 首发没有交叉腿
- 大腿 / 膝盖 / 小腿 / 脚踝 / 双脚全部独立可读
- centerline crossing = 0
- `LegSeparationGate` 6/6 PASS

所以：

# 禁止交叉腿这部分不要再改

现在要解决新的问题：

> AI 虽然不交叉腿了，
> 但为了安全，很多姿势被画得太普通、太老实，
> 请求的姿势语义没有真正保留下来。

---

# 一、本轮目标

新增：

# Pose Intent Preservation

也就是：

用户/系统要求什么姿势，

最终实际图片就应该真正表现出这种姿势。

例如：

- elegant 不应该只是普通站着
- sensual 不应该只靠丝袜和露肤
- low-energy 不应该站得很精神
- narrow stance 不应该被扩大成普通开腿
- one-foot-forward 必须真的存在前后脚纵深

---

# 二、新增核心结构

新增：

`PoseIntentContract`

它和现有：

`LegSeparationContract`

完全分开。

两者职责：

## LegSeparationContract

只负责：

- 不交叉腿
- 腿部可读
- 不跨 centerline

## PoseIntentContract

负责：

- 姿势是不是实际表达了目标语义

最终要求：

# LEG SAFETY PASS
# AND
# POSE INTENT PASS

才能认为姿势真正成功。

---

# 三、不要削弱现有硬规则

非常重要：

本轮不能为了让姿势更丰富，

重新允许：

- crossed thighs
- crossed knees
- crossed calves
- crossed ankles
- leg-over-leg
- scissor stance

`NO_CROSSED_LEGS_HARD_INVARIANT`

继续保持最高优先级。

---

# 四、新增 PoseIntentType

至少支持：

- `ELEGANT`
- `SENSUAL`
- `RELAXED_ASYMMETRIC`
- `LOW_ENERGY`
- `NARROW_STANCE`
- `ONE_FOOT_FORWARD`
- `OPEN_STANCE`
- `WIDE_ACTIVE`
- `STABLE_OPEN`
- `CUSTOM`

不要只为当前 6 个 benchmark 写死。

---

# 五、Pose Intent 不等于固定模板

例如：

`ELEGANT`

不能永远映射成一个 pose。

`SENSUAL`

也不能永远映射成同一种腰胯姿势。

系统应该理解：

# pose intent

是：

身体语言目标，

不是唯一动作。

---

# 六、ELEGANT 的语义

如果：

`pose_intent = ELEGANT`

实际姿势应该体现：

- posture controlled
- torso line clean
- shoulder position composed
- arm placement refined
- weight distribution graceful
- body asymmetry intentional

但：

不要：

- crossed legs
- fashion-model leg crossing
- exaggerated S-curve

允许：

- 一脚轻微前置
- 重心偏移
- 肩部轻微倾斜
- 手臂有控制感

---

# 七、SENSUAL 的语义

如果：

`pose_intent = SENSUAL`

不能只靠：

- cleavage
- stockings
- bare legs
- tight outfit

来假装 pose 性感。

实际身体语言应该至少有：

- torso / waist relationship
- relaxed shoulder
- controlled hip orientation
- gaze / head angle
- arm placement
- body confidence

但：

# SEXY != CROSSED LEGS

仍然禁止所有腿部交叉。

---

# 八、RELAXED_ASYMMETRIC

需要实际表现：

- 左右肩高度略不同
- weight distribution 不完全对称
- one knee may be softer
- torso slightly offset
- arms not mirrored
- head angle may be slightly asymmetric

但：

左右腿保持独立。

不能把：

`asymmetric`

理解成：

一条腿跨另一条腿。

---

# 九、LOW_ENERGY

这是本轮重点。

如果：

`pose_intent = LOW_ENERGY`

需要至少通过 2–3 个信号体现：

- shoulders slightly lowered
- neck / head relaxed
- knees slightly soft
- arms less active
- torso less upright
- weight naturally settled
- hands in pocket / loose hand
- gaze softer / less alert

不要：

站得笔直、肩膀打开、像准备工作。

同时不要：

- slouch into anatomy failure
- pigeon toe
- ankle crossing

---

# 十、NARROW_STANCE

必须新增实际几何定义。

目标：

# 窄，但不交叉

应该：

- feet closer than normal neutral stance
- knees closer
- thighs closer
- calves closer

但仍然：

- visible separation
- no overlap
- no centerline crossing

不能为了安全：

直接扩大成普通中等站距。

---

# 十一、ONE_FOOT_FORWARD

必须真实体现：

# 前后纵深

至少：

- one foot clearly closer to camera / forward in body depth
- opposite foot remains behind
- pelvis / torso naturally responds
- stance still balanced

但：

前脚不能横向跨过另一腿。

也就是说：

# depth change YES
# lateral crossover NO

---

# 十二、PoseIntentContract

建议字段：

- requested_intent
- resolved_pose_family
- required_body_signals
- forbidden_shortcuts
- minimum_visible_signals
- leg_safety_required
- depth_requirement
- stance_width_requirement
- asymmetry_requirement
- energy_level
- torso_requirement
- arm_requirement
- head_requirement

不要把 contract 只做成一个字符串。

---

# 十三、PromptCompiler

新增独立区块：

# POSE INTENT

不要只输出：

`relaxed asymmetric stance`

而应该展开成：

具体身体语言要求。

例如：

`LOW_ENERGY`

编译成：

- relaxed shoulders
- softened knees
- settled weight
- quiet arm placement
- reduced torso tension
- natural restrained stance

然后再接：

# LEG GEOMETRY / ANATOMY CONSTRAINT

确保：

Pose Intent
+
No Crossed Legs

同时存在。

---

# 十四、不要让 Leg Geometry 覆盖 Pose Intent

当前最大的风险：

Leg Contract 太强，

把所有 pose 洗成：

- legs apart
- straight stance
- neutral standing

需要明确：

`LegSeparationContract`

只限制：

# 腿之间的关系

不能决定：

- shoulder
- torso
- hip
- arms
- head
- energy level
- depth

---

# 十五、增加 PoseIntentGate

实际图片生成后新增：

`PoseIntentGate`

必须基于：

# ACTUAL IMAGE

不是 Prompt。

---

# 十六、PoseIntentGate 检查什么

至少：

## Stance Width

- NARROW
- NORMAL
- WIDE

## Foot Depth

- SAME_PLANE
- FORWARD_LEFT
- FORWARD_RIGHT

## Weight Distribution

- CENTERED
- LEFT
- RIGHT
- UNCERTAIN

## Knee State

- STRAIGHT
- SOFT
- BENT

## Torso

- UPRIGHT
- RELAXED
- TILTED
- FORWARD
- BACK

## Shoulder Relation

- LEVEL
- ASYMMETRIC
- RELAXED

## Arm Activity

- ACTIVE
- RELAXED
- ASYMMETRIC
- CLOSED

## Head Angle

- NEUTRAL
- TILTED
- TURNED

## Energy Read

- HIGH
- MEDIUM
- LOW

## Overall Pose Intent Match

- STRONG
- ACCEPTABLE
- WEAK
- FAIL

---

# 十七、Case-specific Gate Logic

## ELEGANT

至少检查：

- controlled posture
- intentional asymmetry
- refined arm / torso relation

不能只是：

普通站姿 + 漂亮衣服。

---

## SENSUAL

至少检查：

- body confidence
- torso / waist interaction
- controlled head / shoulder / hip language

不能只靠：

服装性感。

---

## RELAXED_ASYMMETRIC

必须：

- actual asymmetry visible

不能：

左右完全镜像站立。

---

## LOW_ENERGY

必须：

至少两个实际低能量身体信号。

---

## NARROW_STANCE

必须：

实际站距达到 narrow。

不能：

normal stance 假装 narrow。

---

## ONE_FOOT_FORWARD

必须：

前后脚深度明显。

不能：

两脚几乎同一平面。

---

# 十八、PoseIntentGate 和 LegSeparationGate 的关系

最终：

## Leg PASS
## Pose Intent PASS

才：

`POSE_VALID`

如果：

Leg PASS
但
Pose Intent FAIL

则：

`POSE_INTENT_FAIL`

不能因为腿安全：

就判整个 pose 成功。

---

# 十九、新增 Failure Types

增加：

`POSE_INTENT_FAIL`

`POSE_SEMANTIC_EROSION`

`POSE_SAFETY_OVERCONSTRAINT`

`NARROW_STANCE_EXPANDED`

`ONE_FOOT_FORWARD_DEPTH_MISSING`

`LOW_ENERGY_READ_MISSING`

`SENSUAL_POSE_REDUCED_TO_OUTFIT`

`ELEGANT_POSE_REDUCED_TO_NEUTRAL`

`RELAXED_ASYMMETRY_MISSING`

这些错误：

不是 anatomy failure。

和 crossed-leg failure 分开。

---

# 二十、不要自动把 Pose Intent FAIL 当成 Anatomy FAIL

例如：

角色腿没交叉，
人体也正常，

但 narrow stance 画成普通站姿。

应该：

`POSE_INTENT_FAIL`

而不是：

`ANATOMY_FAIL`

保持诊断准确。

---

# 二十一、Pose Repair

以后如果：

Leg PASS
但
Pose Intent FAIL

允许：

# pose-intent-only repair

保留：

- character identity
- face
- hair
- outfit
- palette
- body build
- lower-body design
- footwear
- regional style
- background direction

只修改：

- body language
- stance width
- foot depth
- torso
- shoulder
- arms
- head
- energy level

---

# 二十二、Pose Repair 不能破坏 Leg Safety

pose-intent repair 后：

仍然必须重新跑：

`LegSeparationGate`

不能为了修：

ONE_FOOT_FORWARD

结果又把腿交叉。

---

# 二十三、Pose Diversity

新增：

`PoseDiversityLedger`

记录：

- stance width
- foot depth
- weight side
- knee state
- torso angle
- shoulder asymmetry
- arm structure
- head angle
- energy level

用于检测：

# 大家虽然腿不交叉
# 但全部普通正面站立

---

# 二十四、新增 Safe Pose Homogenization Detection

新增：

`SAFE_POSE_HOMOGENIZATION`

如果连续多个角色：

- same stance width
- same foot plane
- same torso
- same arms
- same head angle

即使 pose family 名字不同，

也要检测出来。

---

# 二十五、不要机械追求 Pose Diversity

仍然：

# character fit first

如果同一阵营或用户明确要求统一 pose：

允许相似。

Pose diversity：

只做 repetition warning / penalty。

不是硬 ban。

---

# 二十六、Visual Preference

如果用户选择：

- elegant
- sensual
- low-energy
- narrow stance
- one foot forward

系统必须保存：

`pose_intent`

不能只存：

最终 pose family。

否则用户意图在中间会丢失。

---

# 二十七、Schema

相关 schema 增加：

- pose_intent
- pose_intent_contract
- pose_intent_gate
- actual_pose_features
- pose_intent_result
- pose_intent_failure_type

保持 backward compatibility。

---

# 二十八、Migration

旧 artifact 没有：

`pose_intent`

时：

根据旧 pose family 尽可能映射。

如果无法可靠映射：

使用：

`UNKNOWN_LEGACY_POSE_INTENT`

不要伪造用户选择。

---

# 二十九、Tests

至少新增以下测试。

## Test 1

ELEGANT
不能被编译成纯 neutral stance。

## Test 2

SENSUAL
不能只保留 clothing fanservice 而没有 pose language。

## Test 3

LOW_ENERGY
PromptCompiler 必须加入 low-energy body signals。

## Test 4

NARROW_STANCE
必须保留 narrow width requirement。

## Test 5

ONE_FOOT_FORWARD
必须加入 depth requirement。

## Test 6

RELAXED_ASYMMETRIC
必须加入 asymmetry signals。

## Test 7

Leg Contract
不能把 narrow 强制变 wide。

## Test 8

Leg Contract
不能把 one-foot-forward 变 same-plane。

## Test 9

PoseIntentGate：
NARROW requested + actual NORMAL
→ FAIL。

## Test 10

ONE_FOOT_FORWARD requested + actual SAME_PLANE
→ FAIL。

## Test 11

LOW_ENERGY requested + actual HIGH/MEDIUM energy
→ FAIL。

## Test 12

SENSUAL requested + outfit sexy but neutral body
→ WEAK/FAIL。

## Test 13

ELEGANT requested + neutral military stance
→ FAIL。

## Test 14

Relaxed asymmetric + actual asymmetry visible
→ PASS。

## Test 15

Leg PASS + Pose FAIL
→ overall pose FAIL。

## Test 16

Leg FAIL + Pose PASS
→ overall pose FAIL。

## Test 17

Both PASS
→ overall pose PASS。

## Test 18

Pose-intent repair
不能修改 character identity。

## Test 19

Pose-intent repair
必须重新跑 Leg Gate。

## Test 20

Pose diversity ledger
能识别多个“不同名字、实际同姿势”。

---

# 三十、Full Regression

修改完成后：

先跑：

- pose intent tests
- leg separation tests
- PromptCompiler tests
- Visual Preference tests
- Lower-Body tests

然后跑：

# full pytest

确保：

NO_CROSSED_LEGS
没有被破坏。

---

# 三十一、不要修改其他系统

本轮不要顺手改：

- Regional Style
- Fanservice
- Body Build
- Outfit
- Lower-Body
- Hair
- Character Explore

只改：

# POSE INTENT PRESERVATION

---

# 三十二、本轮不要生图

本次：

# MODIFY SKILL ONLY

不要调用 `$imagegen`。

不要重跑六张 pose benchmark。

完成：

- runtime
- compiler
- gate
- schema
- tests
- docs
- wiki

然后停止。

---

# 三十三、最终向我汇报

1. 修改了哪些文件
2. `PoseIntentContract` 结构
3. `PoseIntentGate` 结构
4. PromptCompiler 如何保留姿势语义
5. ELEGANT 如何定义
6. SENSUAL 如何定义
7. RELAXED_ASYMMETRIC 如何定义
8. LOW_ENERGY 如何定义
9. NARROW_STANCE 如何定义
10. ONE_FOOT_FORWARD 如何定义
11. 如何保证 NO_CROSSED_LEGS 不被削弱
12. 如何避免所有姿势被洗成普通站姿
13. 新增 failure types
14. Pose Diversity Ledger
15. Safe Pose Homogenization 检测
16. Pose-intent-only repair 流程
17. migration / backward compatibility
18. 新增测试数量
19. 定向测试结果
20. full pytest 结果
21. 是否存在 breaking change
22. docs / Wiki 更新位置

最终状态：

`POSE_INTENT_PRESERVATION_IMPLEMENTED_PENDING_HUMAN_REVIEW`

# 不调用 `$imagegen`
# 不生成图片
# 不自动启动下一轮 benchmark
