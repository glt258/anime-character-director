"""Persistent, user-facing continuation over the existing interaction runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence
from uuid import uuid4

try:
    from .codex_interaction_adapter import NativeInteractionAdapter, NativeInteractionError, NativeInteractionSpec
    from .interaction_runtime import (
        CreationMode,
        GateType,
        InteractionAction,
        InteractionEvent,
        InteractionRuntime,
    )
except ImportError:  # pragma: no cover
    from codex_interaction_adapter import NativeInteractionAdapter, NativeInteractionError, NativeInteractionSpec  # type: ignore
    from interaction_runtime import (  # type: ignore
        CreationMode,
        GateType,
        InteractionAction,
        InteractionEvent,
        InteractionRuntime,
    )


WORKFLOW_SCHEMA_VERSION = "1.0.0"
CUSTOM_OPTION_ID = "__CUSTOM__"
CUSTOM_INPUT_GATE = "CUSTOM_INPUT_GATE"


class WorkflowRunStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING_FOR_INTERACTION = "WAITING_FOR_INTERACTION"
    RESUMING = "RESUMING"
    GENERATION_READY = "GENERATION_READY"
    GENERATING = "GENERATING"
    ADHERENCE_REVIEWED = "ADHERENCE_REVIEWED"
    REPAIR_PLANNED = "REPAIR_PLANNED"
    REPAIR_GENERATED = "REPAIR_GENERATED"
    REPAIR_REVIEWED = "REPAIR_REVIEWED"
    ACCEPTED = "ACCEPTED"
    REPAIR_EXHAUSTED = "REPAIR_EXHAUSTED"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class CheckpointStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED = "CANCELLED"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _value(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def infer_interaction_locale(text: str, explicit_locale: str | None = None) -> str:
    if explicit_locale:
        normalized = explicit_locale.lower().replace("_", "-")
        return "zh-CN" if normalized.startswith("zh") else "en-US" if normalized.startswith("en") else "en-US"
    return "zh-CN" if len(re.findall(r"[\u3400-\u9fff]", text)) >= 2 else "en-US"


@dataclass
class InteractionOption:
    option_id: str
    internal_label: str
    display_title: str
    display_description: str
    locale: str
    is_recommended: bool = False
    is_custom: bool = False
    source_artifact_ref: str | None = None
    variable: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InteractionCheckpoint:
    checkpoint_id: str
    run_id: str
    gate_id: str
    gate_type: str
    stage: str
    prompt_payload: dict[str, Any]
    options: list[dict[str, Any]] = field(default_factory=list)
    custom_input_allowed: bool = True
    custom_option_id: str = CUSTOM_OPTION_ID
    allowed_actions: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    resolved_at: str | None = None
    resolution: dict[str, Any] | None = None
    status: str = CheckpointStatus.OPEN.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "InteractionCheckpoint":
        values = dict(data)
        values.setdefault("options", [])
        values.setdefault("allowed_actions", [])
        values.setdefault("custom_input_allowed", True)
        values.setdefault("custom_option_id", CUSTOM_OPTION_ID)
        values.setdefault("status", CheckpointStatus.OPEN.value)
        return cls(**values)


@dataclass
class WorkflowRun:
    run_id: str
    session_id: str
    creation_mode: str
    original_user_input: str
    status: str = WorkflowRunStatus.CREATED.value
    current_stage: str = "INPUT"
    current_checkpoint: str | None = None
    checkpoint_history: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    completed_at: str | None = None
    generation_requested: bool = False
    continuation_expected: bool = False
    interaction_locale: str = "en-US"
    schema_version: str = WORKFLOW_SCHEMA_VERSION
    last_user_message: str | None = None
    last_resolved_checkpoint: str | None = None
    last_native_submission: str | None = None
    design_seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WorkflowRun":
        values = dict(data)
        values.setdefault("checkpoint_history", [])
        values.setdefault("schema_version", WORKFLOW_SCHEMA_VERSION)
        values.setdefault("interaction_locale", "en-US")
        values.setdefault("last_user_message", None)
        values.setdefault("last_resolved_checkpoint", None)
        values.setdefault("last_native_submission", None)
        values.setdefault("design_seed", None)
        return cls(**values)


@dataclass
class WorkflowResponse:
    run_id: str
    status: str
    stage: str
    user_message: str
    checkpoint: InteractionCheckpoint | None = None
    generation_ready: bool = False
    error_code: str | None = None
    session_id: str | None = None

    def to_dict(self, *, include_internal: bool = False) -> dict[str, Any]:
        result = {
            "run_id": self.run_id,
            "status": self.status,
            "stage": self.stage,
            "user_message": self.user_message,
            "checkpoint": self.checkpoint.to_dict() if self.checkpoint else None,
            "generation_ready": self.generation_ready,
            "error_code": self.error_code,
        }
        if include_internal:
            result["session_id"] = self.session_id
        return result


class InteractionLocalizer:
    """Render stable internal options into the conversation locale."""

    _VARIABLE_NAMES = {
        "hair_color": ("发色", "Hair Color"),
        "hair_style_family": ("发型", "Hair Style"),
        "outfit_direction": ("服装方向", "Outfit Direction"),
        "dominant_palette": ("主色调", "Dominant Palette"),
        "major_accessories": ("主要配件", "Major Accessories"),
        "body_markings": ("身体标记", "Body Markings"),
        "eye_color": ("瞳色", "Eye Color"),
        "nonhuman_trait_level": ("非人特征程度", "Non-human Trait Level"),
        "fanservice_level": ("性感程度", "Fanservice Level"),
        "body_build": ("体型", "Body Build"),
        "background_direction": ("背景方向", "Background Direction"),
        "footwear_family": ("鞋履", "Footwear"),
        "legwear_family": ("腿部穿着", "Legwear"),
        "exposure_strategy": ("露肤策略", "Exposure Strategy"),
        "leg_accessory_family": ("腿部配件", "Leg Accessories"),
        "foot_visibility": ("足部可读性", "Foot Visibility"),
        "pose_intent": ("动作意图", "Pose Intent"),
        "pose_family": ("站姿族", "Pose Family"),
    }

    def __init__(self, locale: str = "en-US") -> None:
        self.locale = infer_interaction_locale("", locale)

    def _direction_option(self, item: Mapping[str, Any], recommended: str | None) -> InteractionOption:
        thesis = str(item.get("short_label") or item.get("design_thesis") or item.get("id") or "direction")
        zh_title = str(item.get("title_zh") or f"方向 {item.get('id', '')}")
        en_title = str(item.get("title_en") or thesis.replace("_", " ").title())
        zh_desc = str(item.get("description_zh") or item.get("summary") or "保持角色方向清晰可读。")
        en_desc = str(item.get("description_en") or item.get("summary") or thesis)
        title, desc = (zh_title, zh_desc) if self.locale == "zh-CN" else (en_title, en_desc)
        return InteractionOption(
            option_id=str(item.get("id")),
            internal_label=thesis,
            display_title=title,
            display_description=desc,
            locale=self.locale,
            is_recommended=str(item.get("id")) == str(recommended),
            metadata=dict(item),
        )

    def _custom_option(self, *, variable: str | None = None) -> InteractionOption:
        if self.locale == "zh-CN":
            title, desc = "自定义", "输入你自己的方向或要求。"
        else:
            title, desc = "Custom", "Enter your own direction or requirement."
        return InteractionOption(CUSTOM_OPTION_ID, CUSTOM_OPTION_ID, title, desc, self.locale, is_custom=True, variable=variable)

    def _value_copy(self, value: Any) -> tuple[str, str]:
        raw = str(value)
        translations = {
            "ash-silver": "银灰", "silver-white": "银白", "silver-gray": "银灰", "gray-blue": "灰蓝", "muted rose": "柔和玫红", "blue-black": "蓝黑",
            "asymmetric long layers": "不对称长层次", "short geometric bob": "几何短波波头", "braided side mass": "侧面编发量感",
            "structured contemporary fantasy tailoring": "结构化当代幻想剪裁", "soft layered streetwear": "柔和层叠街头服", "ceremonial modular coat": "仪式感模块化外套",
            "deep teal with warm accent": "深青配暖色点缀", "ivory and coral": "象牙白与珊瑚色", "violet and graphite": "紫罗兰与石墨色",
            "one iconic compact tool": "一件标志性小型工具", "asymmetric ear communicator": "不对称耳部通讯器", "small geometric cheek mark": "小型几何面颊标记",
            "clear teal": "清透青绿色", "amber": "琥珀色", "violet": "紫罗兰色", "restrained and character-motivated": "克制且服务角色动机",
            "strong but non-explicit": "强烈但不露骨", "adult balanced athletic build": "成年均衡运动型体态", "slender adult build": "成年纤细体态", "powerful adult build": "成年有力体态",
            "clean atmospheric gradient with restrained motif": "带克制图案的清透氛围渐变", "quiet city dusk": "安静的城市黄昏", "abstract temporal haze": "抽象时序雾气",
            "low asymmetrical boots": "低帮不对称短靴", "barefoot with ankle ornament": "裸足配踝饰", "flat sneakers": "平底运动鞋", "barefoot": "裸足",
            "white opaque tights": "白色不透明连裤袜", "sheer tights": "薄透连裤袜", "controlled partial exposure": "受控局部露肤", "mostly covered": "大部分覆盖", "full-leg exposure": "完整腿部露肤",
            "ankle ornament": "踝部配件", "both feet readable": "双脚清晰可读", "toes visible": "脚趾可见", "shoes fully visible": "鞋履完整可见",
            "clean-line contemporary gacha anime": "清线条当代二游动漫", "quiet minimalist anime": "安静极简动漫", "geometric high-contrast anime": "几何高对比动漫",
            "human-anime traits": "人类动漫特征", "subtle fox ears": "细微狐耳特征", "STABLE_OPEN": "稳定开放站姿", "OPEN_PARALLEL_STANCE": "开放平行站姿",
            "RELAXED_ASYMMETRIC": "放松不对称站姿", "ONE_FOOT_FORWARD": "单脚前置站姿", "NARROW_SEPARATED_STANCE": "窄幅分腿站姿", "FORWARD_STEP_NON_CROSSING": "前踏但不交叉站姿",
            "supports identity and a grounded playable-character silhouette": "支撑身份与稳固的可玩角色轮廓", "supports the selected contemporary design language": "支撑已选的当代设计语言", "keeps both legs in separate visible lanes": "让双腿保持在分离且可见的区域", "low": "低",
        }
        return (translations.get(raw, raw), raw) if self.locale == "zh-CN" else (raw, raw)

    def checkpoint_for(self, run_id: str, response: Any) -> InteractionCheckpoint | None:
        if not response.gate:
            return None
        gate = response.gate
        gate_type = str(gate.get("gate_type", ""))
        options: list[InteractionOption] = []
        payload: dict[str, Any]
        if gate_type in {GateType.CHARACTER_DIRECTION_GATE.value, GateType.ART_DIRECTION_GATE.value}:
            options = [self._direction_option(item, response.recommended) for item in response.options]
            options.append(self._custom_option())
            title = "角色方向" if gate_type == GateType.CHARACTER_DIRECTION_GATE.value else "美术方向"
            prompt = "我整理了几个角色方向：" if gate_type == GateType.CHARACTER_DIRECTION_GATE.value else "接下来是美术方向："
        else:
            for field in response.options:
                variable = str(field.get("variable", ""))
                name = self._VARIABLE_NAMES.get(variable, (variable, variable))[0 if self.locale == "zh-CN" else 1]
                for item in field.get("options", []):
                    display, internal = self._value_copy(item.get("value"))
                    options.append(InteractionOption(str(item.get("id")), internal, display, "可直接选择，也可以改为自定义。" if self.locale == "zh-CN" else "Select directly or provide a custom value.", self.locale, str(item.get("id")) == str(field.get("recommended")), variable=variable))
                if field.get("locked") is not True:
                    options.append(self._custom_option(variable=variable))
            title = "视觉偏好" if self.locale == "zh-CN" else "Visual Preferences"
            prompt = "你可以一次说明少数视觉要求，其余按推荐；也可以逐项选择。" if self.locale == "zh-CN" else "State a few visual preferences at once; use recommendations for the rest."
            payload = {"title": title, "prompt": prompt, "variables": [self._visual_field(field) for field in response.options]}
        if gate_type in {GateType.CHARACTER_DIRECTION_GATE.value, GateType.ART_DIRECTION_GATE.value}:
            payload = {
                "title": title,
                "prompt": prompt,
                "original_user_input": gate.get("original_user_input", ""),
                "current_gate": gate_type,
                "recommendation": {
                    "option_id": response.recommended,
                    "rationale": self._direction_rationale(gate.get("recommendation_rationale", {})),
                },
                "candidate_generator_version": gate.get("candidate_generator_version"),
                "candidate_revision": gate.get("candidate_revision", 0),
            }
        checkpoint_id = f"{run_id}:checkpoint:{uuid4().hex}"
        actions = ["直接回复选项字母或描述你的想法", "也可以回复自定义", "也可以要求重新给几个方案"] if self.locale == "zh-CN" else ["Reply with an option letter or describe your idea", "You may also choose Custom", "You may ask for another set"]
        return InteractionCheckpoint(checkpoint_id, run_id, str(gate.get("gate_id", "")), gate_type, response.stage, payload, [option.to_dict() for option in options], True, CUSTOM_OPTION_ID, actions)

    def _direction_rationale(self, rationale: Mapping[str, Any] | Any) -> str:
        if not isinstance(rationale, Mapping):
            return str(rationale or "")
        return str(rationale.get("zh" if self.locale == "zh-CN" else "en") or rationale.get("en") or rationale.get("zh") or "")

    def _visual_field(self, field: Mapping[str, Any]) -> dict[str, Any]:
        variable = str(field.get("variable", ""))
        title = self._VARIABLE_NAMES.get(variable, (variable, variable))[0 if self.locale == "zh-CN" else 1]
        items = []
        recommended = str(field.get("recommended"))
        for item in field.get("options", []):
            display, internal = self._value_copy(item.get("value"))
            is_recommended = str(item.get("id")) == recommended or (str(item.get("value")) == recommended and not any(option.get("is_recommended") for option in items))
            items.append({"option_id": str(item.get("id")), "display_title": display, "internal_label": internal, "is_recommended": is_recommended})
        if field.get("locked") is not True:
            custom = self._custom_option(variable=variable).to_dict()
            items.append(custom)
        return {
            "variable": variable,
            "display_name": title,
            "resolved": bool(field.get("resolved")),
            "recommendation_rationale": field.get("recommendation_reason") if self.locale == "zh-CN" else field.get("recommendation_reason_en", field.get("recommendation_reason")),
            "options": items,
        }

    def relocalize_checkpoint(self, checkpoint: InteractionCheckpoint) -> InteractionCheckpoint:
        if checkpoint.gate_type in {GateType.CHARACTER_DIRECTION_GATE.value, GateType.ART_DIRECTION_GATE.value}:
            title = "角色方向" if checkpoint.gate_type == GateType.CHARACTER_DIRECTION_GATE.value else "美术方向"
            prompt = "我整理了几个角色方向：" if checkpoint.gate_type == GateType.CHARACTER_DIRECTION_GATE.value else "接下来是美术方向："
            recommended = next((option["option_id"] for option in checkpoint.options if option.get("is_recommended")), None)
            checkpoint.prompt_payload.update(title=title if self.locale == "zh-CN" else ("Character Direction" if checkpoint.gate_type == GateType.CHARACTER_DIRECTION_GATE.value else "Art Direction"), prompt=prompt if self.locale == "zh-CN" else ("I prepared several character directions:" if checkpoint.gate_type == GateType.CHARACTER_DIRECTION_GATE.value else "Next are several art directions:"))
            for option in checkpoint.options:
                if option.get("is_custom"):
                    copy = self._custom_option().to_dict()
                else:
                    copy = self._direction_option({**option.get("metadata", {}), "id": option["option_id"]}, recommended).to_dict()
                option.update(copy)
            recommended_option = next((option for option in checkpoint.options if option.get("option_id") == str(recommended)), None)
            if recommended_option:
                metadata = recommended_option.get("metadata", {})
                checkpoint.prompt_payload.setdefault("recommendation", {})["rationale"] = self._direction_rationale(
                    {"zh": metadata.get("rationale_zh", ""), "en": metadata.get("rationale_en", "")}
                )
        elif checkpoint.gate_type == GateType.VISUAL_PREFERENCE_GATE.value:
            checkpoint.prompt_payload.update(
                title="视觉偏好" if self.locale == "zh-CN" else "Visual Preferences",
                prompt="你可以一次说明少数视觉要求，其余按推荐；也可以逐项选择。" if self.locale == "zh-CN" else "State a few visual preferences at once; use recommendations for the rest.",
            )
            for field in checkpoint.prompt_payload.get("variables", []):
                variable = str(field.get("variable", ""))
                field["display_name"] = self._VARIABLE_NAMES.get(variable, (variable, variable))[0 if self.locale == "zh-CN" else 1]
                for option in field.get("options", []):
                    if option.get("is_custom"):
                        option.update(self._custom_option(variable=variable).to_dict())
                    else:
                        display, internal = self._value_copy(option.get("internal_label"))
                        option.update(display_title=display, internal_label=internal)
        return checkpoint

    def custom_input_checkpoint(self, run_id: str, gate_id: str, stage: str, target_gate_type: str | None = None) -> InteractionCheckpoint:
        if self.locale == "zh-CN":
            prompt = "请输入要修改的字段和值，例如‘发色灰蓝，鞋履裸足’，我会继续同一个角色创建流程。" if target_gate_type == GateType.VISUAL_PREFERENCE_GATE.value else "请输入你想要的方向或要求，我会继续同一个角色创建流程。"
            payload = {"title": "自定义方向", "prompt": prompt}
            actions = ["输入自定义内容"]
        else:
            prompt = "Enter fields and values, for example ‘gray-blue hair, barefoot’; I will continue this same character workflow." if target_gate_type == GateType.VISUAL_PREFERENCE_GATE.value else "Enter your direction or requirement; I will continue this same character workflow."
            payload = {"title": "Custom Direction", "prompt": prompt}
            actions = ["Enter your custom content"]
        if target_gate_type:
            payload["target_gate_type"] = target_gate_type
        return InteractionCheckpoint(f"{run_id}:custom-input:{uuid4().hex}", run_id, gate_id, CUSTOM_INPUT_GATE, stage, payload, [], True, CUSTOM_OPTION_ID, actions)

    def message_for(self, response: Any, checkpoint: InteractionCheckpoint | None = None) -> str:
        if response.error_code:
            if self.locale == "zh-CN":
                return response.user_message if response.user_message else "请做一个最小选择，或直接描述你的想法。"
            return "Please make a clear choice or describe your idea."
        if checkpoint and checkpoint.gate_type == CUSTOM_INPUT_GATE:
            return checkpoint.prompt_payload["prompt"]
        if checkpoint:
            lines = [checkpoint.prompt_payload["prompt"]]
            if checkpoint.prompt_payload.get("variables"):
                visible = checkpoint.prompt_payload["variables"]
                for field in visible[:3]:
                    values = [item.get("display_title") for item in field.get("options", [])[:3]]
                    lines.append(f"{field['display_name']}：" + " / ".join(values))
                if len(visible) > 3:
                    lines.append("其余字段可按推荐，也可以一次说明你想修改的字段。" if self.locale == "zh-CN" else "Use recommendations for the remaining fields or state your overrides at once.")
            direction_index = 0
            for option in checkpoint.options:
                if option.get("variable"):
                    continue
                display_id = chr(65 + direction_index)
                direction_index += 1
                marker = "（推荐）" if option.get("is_recommended") and self.locale == "zh-CN" else " (recommended)" if option.get("is_recommended") else ""
                lines.append(f"{display_id}｜{option['display_title']}{marker}\n{option['display_description']}")
            recommended = response.recommended
            if recommended:
                label = "推荐" if self.locale == "zh-CN" else "Recommended"
                if isinstance(recommended, dict):
                    lines.append(f"{label}：按推荐或直接说明你想改的字段。")
                else:
                    rec_index = next((index for index, item in enumerate(checkpoint.options) if not item.get("variable") and item.get("option_id") == str(recommended)), None)
                    rec = next((item.get("display_title") for item in checkpoint.options if item.get("option_id") == str(recommended)), str(recommended))
                    rec_display = chr(65 + rec_index) if rec_index is not None else str(recommended)
                    rationale = checkpoint.prompt_payload.get("recommendation", {}).get("rationale")
                    lines.append(f"{label}：{rec_display}｜{rec}" + (f"\n{rationale}" if rationale else ""))
            lines.append("你可以直接回复选项字母，也可以说出你的想法。" if self.locale == "zh-CN" else "Reply with a letter or describe your idea.")
            return "\n\n".join(lines)
        if response.status == "GENERATION_READY":
            return "设计已完成，已准备进入生成。" if self.locale == "zh-CN" else "The design is complete and ready for generation."
        if response.status == "CANCELLED":
            return "这个角色创建流程已取消。" if self.locale == "zh-CN" else "This character workflow was cancelled."
        return response.user_message


class PersistentWorkflowRunner:
    """One logical WorkflowRun across multiple conversation turns or restarts."""

    def __init__(self, session_root: str | Path = "sessions") -> None:
        self.session_root = Path(session_root)
        self.runtime = InteractionRuntime(self.session_root)

    def _session_dir(self, run: WorkflowRun) -> Path:
        return self.session_root / run.session_id

    @staticmethod
    def _atomic_write(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)

    def _save_run(self, run: WorkflowRun) -> None:
        run.updated_at = _now()
        self._atomic_write(self._session_dir(run) / "workflow_run.json", run.to_dict())

    def _save_checkpoint(self, checkpoint: InteractionCheckpoint, event: str) -> None:
        path = self._checkpoint_path(checkpoint.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"event": event, "checkpoint": checkpoint.to_dict()}, ensure_ascii=False) + "\n")

    def _checkpoint_path(self, run_id: str) -> Path:
        for path in self.session_root.glob("*/workflow_run.json"):
            try:
                if json.loads(path.read_text(encoding="utf-8")).get("run_id") == run_id:
                    return path.parent / "checkpoints.jsonl"
            except (OSError, json.JSONDecodeError):
                continue
        return self.session_root / run_id / "checkpoints.jsonl"

    def _load_run(self, run_id: str) -> WorkflowRun:
        for path in self.session_root.glob("*/workflow_run.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if str(data.get("run_id")) == run_id:
                return WorkflowRun.from_dict(data)
        raise FileNotFoundError(f"workflow run not found: {run_id}")

    def _load_checkpoint(self, run: WorkflowRun, checkpoint_id: str | None = None) -> InteractionCheckpoint | None:
        path = self._checkpoint_path(run.run_id)
        if not path.is_file():
            return None
        latest: dict[str, InteractionCheckpoint] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)["checkpoint"]
            latest[str(data["checkpoint_id"])] = InteractionCheckpoint.from_dict(data)
        wanted = checkpoint_id or run.current_checkpoint
        return latest.get(wanted) if wanted else None

    def _set_checkpoint(self, run: WorkflowRun, checkpoint: InteractionCheckpoint) -> None:
        run.current_checkpoint = checkpoint.checkpoint_id
        run.checkpoint_history.append(checkpoint.checkpoint_id)
        run.status = WorkflowRunStatus.WAITING_FOR_INTERACTION.value
        run.continuation_expected = True
        run.current_stage = checkpoint.stage
        self._save_checkpoint(checkpoint, "created")
        self._save_run(run)

    def _resolve_checkpoint(self, checkpoint: InteractionCheckpoint, resolution: Mapping[str, Any]) -> None:
        checkpoint.status = CheckpointStatus.RESOLVED.value
        checkpoint.resolved_at = _now()
        checkpoint.resolution = dict(resolution)
        self._save_checkpoint(checkpoint, "resolved")

    def _checkpoint_response(self, run: WorkflowRun, raw_response: Any, localizer: InteractionLocalizer) -> WorkflowResponse:
        run.creation_mode = raw_response.mode
        checkpoint = localizer.checkpoint_for(run.run_id, raw_response)
        if checkpoint:
            self._set_checkpoint(run, checkpoint)
        else:
            run.current_checkpoint = None
            run.continuation_expected = False
            run.current_stage = raw_response.stage
            run.status = WorkflowRunStatus.GENERATION_READY.value if raw_response.status == "GENERATION_READY" else str(raw_response.status)
            self._save_run(run)
        return WorkflowResponse(run.run_id, run.status, run.current_stage, localizer.message_for(raw_response, checkpoint), checkpoint, raw_response.status == "GENERATION_READY", raw_response.error_code, run.session_id)

    def start_workflow(self, user_input: str, mode: str | CreationMode | None = None, *, generation_requested: bool = False, interaction_locale: str | None = None, seed: int | None = None) -> WorkflowResponse:
        run_id = uuid4().hex
        session_id = uuid4().hex
        raw_response = self.runtime.create_session(user_input, mode, session_id=session_id, seed=seed)
        saved_session = self.runtime.load_session(session_id)
        run = WorkflowRun(run_id, session_id, raw_response.mode, user_input, WorkflowRunStatus.RUNNING.value, raw_response.stage, generation_requested=generation_requested, interaction_locale=infer_interaction_locale(user_input, interaction_locale), design_seed=saved_session.design_seed)
        self._save_run(run)
        localizer = InteractionLocalizer(run.interaction_locale)
        return self._checkpoint_response(run, raw_response, localizer)

    def _stale_response(self, run: WorkflowRun, localizer: InteractionLocalizer) -> WorkflowResponse:
        message = "这条回复属于旧的交互步骤，当前流程没有改变。" if localizer.locale == "zh-CN" else "That reply belongs to an older interaction step; the workflow did not change."
        return WorkflowResponse(run.run_id, run.status, run.current_stage, message, None, False, "STALE_CHECKPOINT", run.session_id)

    def _duplicate_response(self, run: WorkflowRun, checkpoint: InteractionCheckpoint, localizer: InteractionLocalizer) -> WorkflowResponse:
        message = "这条回复看起来已经提交过了，当前步骤没有继续推进。" if localizer.locale == "zh-CN" else "That reply appears to have already been submitted; the current step did not advance."
        return WorkflowResponse(run.run_id, run.status, run.current_stage, message, checkpoint, False, "DUPLICATE_INTERACTION", run.session_id)

    @staticmethod
    def _is_new_workflow_request(text: str) -> bool:
        return bool(re.search(r"取消这个.*(?:重新|新).*(?:角色|设计)|开始一个新角色|重新做一个角色", text, re.IGNORECASE))

    @staticmethod
    def _requested_locale(text: str) -> str | None:
        if re.search(r"(?:后面|接下来|改用|换成).*(?:英文|英语)|(?:switch|use)\s+(?:to\s+)?english", text, re.IGNORECASE):
            return "en-US"
        if re.search(r"(?:后面|接下来|改用|换成).*(?:中文|汉语)|(?:switch|use)\s+(?:back\s+)?(?:to\s+)?chinese", text, re.IGNORECASE):
            return "zh-CN"
        return None

    @staticmethod
    def _strip_locale_request(text: str) -> str:
        return re.sub(r"^(?:后面|接下来|改用|换成)?(?:都)?(?:用|说)?(?:英文|英语|中文|汉语)|^(?:switch|use)\s+(?:back\s+)?(?:to\s+)?(?:english|chinese)", "", text, flags=re.IGNORECASE).strip(" ，,：:。.!！")

    def _cancel_run(self, run: WorkflowRun) -> None:
        checkpoint = self._load_checkpoint(run)
        if checkpoint and checkpoint.status == CheckpointStatus.OPEN.value:
            checkpoint.status = CheckpointStatus.CANCELLED.value
            checkpoint.resolved_at = _now()
            checkpoint.resolution = {"decision_source": "human_cancel"}
            self._save_checkpoint(checkpoint, "cancelled")
        run.status = WorkflowRunStatus.CANCELLED.value
        run.current_checkpoint = None
        run.continuation_expected = False
        run.completed_at = _now()
        self._save_run(run)

    def _custom_choice(self, text: str, checkpoint: InteractionCheckpoint) -> bool:
        return bool(re.fullmatch(r"(?:E|自定义|custom|__CUSTOM__|我想自己定|我想自定义|我自己定|自己描述)[。.!！]?$", text.strip(), re.IGNORECASE)) and checkpoint.custom_option_id == CUSTOM_OPTION_ID

    def native_interaction_spec(self, run_id: str, *, checkpoint_id: str | None = None) -> NativeInteractionSpec:
        """Build the host-facing spec for the currently persisted open checkpoint."""
        run = self._load_run(run_id)
        if checkpoint_id is not None and checkpoint_id != run.current_checkpoint:
            raise NativeInteractionError("STALE_NATIVE_CHECKPOINT", "The requested checkpoint is not current.")
        checkpoint = self._load_checkpoint(run, run.current_checkpoint)
        if checkpoint is None or checkpoint.status != CheckpointStatus.OPEN.value:
            raise NativeInteractionError("CHECKPOINT_NOT_OPEN", "The workflow is not waiting at an open checkpoint.")
        return NativeInteractionAdapter().build(checkpoint)

    def _native_error_response(self, run: WorkflowRun, checkpoint: InteractionCheckpoint, localizer: InteractionLocalizer, error: NativeInteractionError) -> WorkflowResponse:
        message = "原生选择无效，当前步骤保持等待，不会自动选择。" if localizer.locale == "zh-CN" else "The native answer is invalid; this step remains waiting and no choice was applied."
        return WorkflowResponse(run.run_id, run.status, run.current_stage, message, checkpoint, False, error.code, run.session_id)

    def continue_native_workflow(self, run_id: str, answer: Mapping[str, Any], *, checkpoint_id: str | None = None) -> WorkflowResponse:
        """Resolve one real host answer and advance the same WorkflowRun."""
        run = self._load_run(run_id)
        localizer = InteractionLocalizer(run.interaction_locale)
        if checkpoint_id is not None and checkpoint_id != run.current_checkpoint:
            return self._stale_response(run, localizer)
        checkpoint = self._load_checkpoint(run, run.current_checkpoint)
        if checkpoint is None or checkpoint.status != CheckpointStatus.OPEN.value:
            return self._stale_response(run, localizer)
        try:
            adapter = NativeInteractionAdapter()
            spec = adapter.build(checkpoint)
            resolution = adapter.resolve(spec, answer)
            action, payload = resolution.to_runtime_action(spec)
        except NativeInteractionError as error:
            return self._native_error_response(run, checkpoint, localizer, error)
        fingerprint = resolution.submission_fingerprint()
        if run.last_native_submission == fingerprint:
            return self._duplicate_response(run, checkpoint, localizer)
        run.status = WorkflowRunStatus.RESUMING.value
        self._save_run(run)
        event = InteractionEvent(
            uuid4().hex,
            run.session_id,
            checkpoint.gate_id,
            action,
            {
                **payload,
                "native_ui": True,
                "checkpoint_id": checkpoint.checkpoint_id,
                "candidate_revision": spec.revision,
            },
        )
        raw_response = self.runtime.resume_session(run.session_id, event)
        if raw_response.error_code:
            run.status = WorkflowRunStatus.WAITING_FOR_INTERACTION.value
            self._save_run(run)
            return self._native_error_response(run, checkpoint, localizer, NativeInteractionError(raw_response.error_code, raw_response.user_message))
        self._resolve_checkpoint(checkpoint, {"decision_source": "native_ui", "candidate_revision": spec.revision, "resolution": resolution.to_dict()})
        run.last_native_submission = fingerprint
        run.last_user_message = None
        run.last_resolved_checkpoint = checkpoint.checkpoint_id
        run.current_stage = raw_response.stage
        if raw_response.status == "CANCELLED":
            run.status = WorkflowRunStatus.CANCELLED.value
            run.current_checkpoint = None
            run.continuation_expected = False
            run.completed_at = _now()
            self._save_run(run)
            return WorkflowResponse(run.run_id, run.status, run.current_stage, localizer.message_for(raw_response), None, False, None, run.session_id)
        return self._checkpoint_response(run, raw_response, localizer)

    def continue_workflow(self, run_id: str, user_message: str, *, checkpoint_id: str | None = None) -> WorkflowResponse:
        run = self._load_run(run_id)
        requested_locale = self._requested_locale(user_message)
        if requested_locale:
            run.interaction_locale = requested_locale
            self._save_run(run)
            user_message = self._strip_locale_request(user_message)
        localizer = InteractionLocalizer(run.interaction_locale)
        if self._is_new_workflow_request(user_message):
            self._cancel_run(run)
            clean = re.sub(r"^(?:取消这个[，,]?|开始|重新)(?:这个)?(?:角色创建流程)?[，,：: ]*", "", user_message).strip() or "设计一个新角色"
            return self.start_workflow(clean, interaction_locale=run.interaction_locale)
        if checkpoint_id is not None and checkpoint_id != run.current_checkpoint:
            return self._stale_response(run, localizer)
        checkpoint = self._load_checkpoint(run, run.current_checkpoint)
        if checkpoint is None or checkpoint.status != CheckpointStatus.OPEN.value:
            return self._stale_response(run, localizer)
        normalized_message = user_message.strip()
        if checkpoint_id is None and normalized_message and run.last_user_message == normalized_message and run.last_resolved_checkpoint and run.last_resolved_checkpoint != checkpoint.checkpoint_id:
            return self._duplicate_response(run, checkpoint, localizer)
        if not user_message:
            if requested_locale:
                checkpoint = localizer.relocalize_checkpoint(checkpoint)
                self._save_checkpoint(checkpoint, "localized")
            message = ("语言已切换。" if localizer.locale == "zh-CN" else "Language updated. ") + checkpoint.prompt_payload["prompt"]
            return WorkflowResponse(run.run_id, run.status, run.current_stage, message, checkpoint, False, None, run.session_id)
        run.status = WorkflowRunStatus.RESUMING.value
        self._save_run(run)
        control_message = bool(re.search(r"返回上一步|回到上一步|重选前面|后面.*(?:你决定|交给你)|切成(?:快速|AI)|取消", user_message, re.IGNORECASE))
        if checkpoint.gate_type == CUSTOM_INPUT_GATE and not control_message:
            if checkpoint.prompt_payload.get("target_gate_type") == GateType.VISUAL_PREFERENCE_GATE.value:
                raw_response = self.runtime.resume_session(run.session_id, user_message)
            else:
                event = InteractionEvent(uuid4().hex, run.session_id, checkpoint.gate_id, InteractionAction.CUSTOM.value, {"text": user_message, "custom": user_message})
                raw_response = self.runtime.resume_session(run.session_id, event)
        elif self._custom_choice(user_message, checkpoint):
            self._resolve_checkpoint(checkpoint, {"action": "CUSTOM_OPTION", "option_id": CUSTOM_OPTION_ID, "decision_source": "human_select"})
            run.last_user_message = normalized_message
            run.last_resolved_checkpoint = checkpoint.checkpoint_id
            target_gate = checkpoint.gate_type if checkpoint.gate_type == GateType.VISUAL_PREFERENCE_GATE.value else None
            custom = localizer.custom_input_checkpoint(run.run_id, checkpoint.gate_id, checkpoint.stage, target_gate)
            self._set_checkpoint(run, custom)
            message = localizer.message_for(type("Response", (), {"error_code": None})(), custom)
            return WorkflowResponse(run.run_id, run.status, run.current_stage, message, custom, False, None, run.session_id)
        else:
            raw_response = self.runtime.resume_session(run.session_id, user_message)
        if raw_response.error_code:
            run.status = WorkflowRunStatus.WAITING_FOR_INTERACTION.value
            self._save_run(run)
            return WorkflowResponse(run.run_id, run.status, run.current_stage, localizer.message_for(raw_response, checkpoint), checkpoint, False, raw_response.error_code, run.session_id)
        if re.search(r"[?？]|为什么|有何区别|什么区别|最大的区别|你推荐哪个|推荐哪个|你觉得哪个|哪个更适合", user_message, re.IGNORECASE):
            run.status = WorkflowRunStatus.WAITING_FOR_INTERACTION.value
            self._save_run(run)
            return WorkflowResponse(run.run_id, run.status, run.current_stage, localizer.message_for(raw_response, checkpoint), checkpoint, False, None, run.session_id)
        self._resolve_checkpoint(checkpoint, {"decision_source": "user_message", "raw_response_status": raw_response.status, "raw_response_stage": raw_response.stage})
        run.last_user_message = normalized_message
        run.last_resolved_checkpoint = checkpoint.checkpoint_id
        run.current_stage = raw_response.stage
        if raw_response.status == "CANCELLED":
            run.status = WorkflowRunStatus.CANCELLED.value
            run.current_checkpoint = None
            run.continuation_expected = False
            run.completed_at = _now()
            self._save_run(run)
            return WorkflowResponse(run.run_id, run.status, run.current_stage, localizer.message_for(raw_response), None, False, None, run.session_id)
        return self._checkpoint_response(run, raw_response, localizer)

    def continue_active_workflow(self, user_message: str) -> WorkflowResponse:
        runs = []
        for path in self.session_root.glob("*/workflow_run.json"):
            run = WorkflowRun.from_dict(json.loads(path.read_text(encoding="utf-8")))
            if run.status == WorkflowRunStatus.WAITING_FOR_INTERACTION.value:
                runs.append(run)
        if not runs:
            return self.start_workflow(user_message)
        runs.sort(key=lambda item: item.updated_at, reverse=True)
        return self.continue_workflow(runs[0].run_id, user_message)

    def load_workflow(self, run_id: str) -> WorkflowRun:
        return self._load_run(run_id)

    def load_checkpoint(self, run_id: str, checkpoint_id: str | None = None) -> InteractionCheckpoint | None:
        run = self._load_run(run_id)
        return self._load_checkpoint(run, checkpoint_id)

    def record_visual_adherence_review(
        self,
        run_id: str,
        actual_image: str | Path,
        *,
        observations: Mapping[str, Any],
        prompt_hash: str | None = None,
    ) -> dict[str, Any]:
        """Persist one post-generation review on the run's underlying session."""
        run = self._load_run(run_id)
        review = self.runtime.record_visual_adherence_review(
            run.session_id,
            actual_image,
            observations=observations,
            prompt_hash=prompt_hash,
        )
        run.status = WorkflowRunStatus.ACCEPTED.value if review.get("overall_result") == "PASS" else WorkflowRunStatus.ADHERENCE_REVIEWED.value
        self._save_run(run)
        return review

    def record_generation_artifact(
        self,
        run_id: str,
        image: str | Path,
        *,
        generation_id: str | None = None,
        prompt_hash: str | None = None,
    ) -> dict[str, Any]:
        run = self._load_run(run_id)
        artifact = self.runtime.record_generation_artifact(
            run.session_id,
            image,
            run_id=run.run_id,
            generation_id=generation_id,
            prompt_hash=prompt_hash,
        )
        self._save_run(run)
        return artifact

    def build_visual_repair_plan(
        self,
        run_id: str,
        *,
        max_attempts: int = 2,
        include_minor: bool = True,
        manual_repair_fields: Sequence[str] = (),
    ) -> dict[str, Any]:
        run = self._load_run(run_id)
        result = self.runtime.build_visual_repair_plan(
            run.session_id,
            max_attempts=max_attempts,
            include_minor=include_minor,
            manual_repair_fields=manual_repair_fields,
        )
        run.status = str(result.get("status", run.status))
        self._save_run(run)
        return result

    def record_visual_repair_generation(
        self,
        run_id: str,
        attempt_id: str,
        repair_image: str | Path,
        *,
        repair_prompt: str | None = None,
        prompt_hash: str | None = None,
    ) -> dict[str, Any]:
        run = self._load_run(run_id)
        result = self.runtime.record_visual_repair_generation(
            run.session_id,
            attempt_id,
            repair_image,
            repair_prompt=repair_prompt,
            prompt_hash=prompt_hash,
        )
        run.status = WorkflowRunStatus.REPAIR_GENERATED.value
        self._save_run(run)
        return result

    def record_visual_repair_review(
        self,
        run_id: str,
        attempt_id: str,
        *,
        observations: Mapping[str, Any],
    ) -> dict[str, Any]:
        run = self._load_run(run_id)
        result = self.runtime.record_visual_repair_review(run.session_id, attempt_id, observations=observations)
        run.status = {
            "ACCEPTED": WorkflowRunStatus.ACCEPTED.value,
            "REPAIR_EXHAUSTED": WorkflowRunStatus.REPAIR_EXHAUSTED.value,
        }.get(self.runtime.load_session(run.session_id).repair_status or "", WorkflowRunStatus.REPAIR_REVIEWED.value)
        self._save_run(run)
        return result


def start_workflow(session_root: str | Path, user_input: str, mode: str | CreationMode | None = None, *, generation_requested: bool = False, interaction_locale: str | None = None, seed: int | None = None) -> WorkflowResponse:
    return PersistentWorkflowRunner(session_root).start_workflow(user_input, mode, generation_requested=generation_requested, interaction_locale=interaction_locale, seed=seed)


def continue_workflow(session_root: str | Path, run_id: str, user_message: str, *, checkpoint_id: str | None = None) -> WorkflowResponse:
    return PersistentWorkflowRunner(session_root).continue_workflow(run_id, user_message, checkpoint_id=checkpoint_id)


def continue_active_workflow(session_root: str | Path, user_message: str) -> WorkflowResponse:
    return PersistentWorkflowRunner(session_root).continue_active_workflow(user_message)


def native_interaction_spec(session_root: str | Path, run_id: str, *, checkpoint_id: str | None = None) -> NativeInteractionSpec:
    return PersistentWorkflowRunner(session_root).native_interaction_spec(run_id, checkpoint_id=checkpoint_id)


def continue_native_workflow(session_root: str | Path, run_id: str, answer: Mapping[str, Any], *, checkpoint_id: str | None = None) -> WorkflowResponse:
    return PersistentWorkflowRunner(session_root).continue_native_workflow(run_id, answer, checkpoint_id=checkpoint_id)


def record_visual_adherence_review(
    session_root: str | Path,
    run_id: str,
    actual_image: str | Path,
    *,
    observations: Mapping[str, Any],
    prompt_hash: str | None = None,
) -> dict[str, Any]:
    return PersistentWorkflowRunner(session_root).record_visual_adherence_review(
        run_id,
        actual_image,
        observations=observations,
        prompt_hash=prompt_hash,
    )


def build_visual_repair_plan(
    session_root: str | Path,
    run_id: str,
    *,
    max_attempts: int = 2,
    include_minor: bool = True,
    manual_repair_fields: Sequence[str] = (),
) -> dict[str, Any]:
    return PersistentWorkflowRunner(session_root).build_visual_repair_plan(
        run_id,
        max_attempts=max_attempts,
        include_minor=include_minor,
        manual_repair_fields=manual_repair_fields,
    )


def record_generation_artifact(
    session_root: str | Path,
    run_id: str,
    image: str | Path,
    *,
    generation_id: str | None = None,
    prompt_hash: str | None = None,
) -> dict[str, Any]:
    return PersistentWorkflowRunner(session_root).record_generation_artifact(
        run_id,
        image,
        generation_id=generation_id,
        prompt_hash=prompt_hash,
    )


def record_visual_repair_generation(
    session_root: str | Path,
    run_id: str,
    attempt_id: str,
    repair_image: str | Path,
    *,
    repair_prompt: str | None = None,
    prompt_hash: str | None = None,
) -> dict[str, Any]:
    return PersistentWorkflowRunner(session_root).record_visual_repair_generation(
        run_id,
        attempt_id,
        repair_image,
        repair_prompt=repair_prompt,
        prompt_hash=prompt_hash,
    )


def record_visual_repair_review(
    session_root: str | Path,
    run_id: str,
    attempt_id: str,
    *,
    observations: Mapping[str, Any],
) -> dict[str, Any]:
    return PersistentWorkflowRunner(session_root).record_visual_repair_review(run_id, attempt_id, observations=observations)


__all__ = [
    "CUSTOM_INPUT_GATE",
    "CUSTOM_OPTION_ID",
    "CheckpointStatus",
    "InteractionCheckpoint",
    "InteractionLocalizer",
    "InteractionOption",
    "NativeInteractionSpec",
    "PersistentWorkflowRunner",
    "WorkflowResponse",
    "WorkflowRun",
    "WorkflowRunStatus",
    "build_visual_repair_plan",
    "continue_active_workflow",
    "continue_native_workflow",
    "continue_workflow",
    "infer_interaction_locale",
    "native_interaction_spec",
    "record_generation_artifact",
    "record_visual_adherence_review",
    "record_visual_repair_generation",
    "record_visual_repair_review",
    "start_workflow",
]
