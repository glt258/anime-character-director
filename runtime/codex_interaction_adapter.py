"""Pure adapter between persisted checkpoints and Codex native input specs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping


CUSTOM_OPTION_ID = "__CUSTOM__"
_OTHER_LABELS = {"other", "custom", "自定义", "其他"}
_RECOMMENDED_SUFFIXES = ("（推荐）", "(Recommended)", "(recommended)")


class NativeInteractionError(ValueError):
    """Raised when a native answer cannot be safely mapped to this checkpoint."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class NativeOption:
    candidate_id: str
    label: str
    description: str = ""
    recommended: bool = False

    def to_request_option(self) -> dict[str, str]:
        return {"label": self.label, "description": self.description}


@dataclass(frozen=True)
class NativeQuestion:
    question_id: str
    header: str
    prompt: str
    options: tuple[NativeOption, ...]
    allow_other: bool = True
    variable: str | None = None

    def to_request_question(self) -> dict[str, Any]:
        return {
            "id": self.question_id,
            "header": self.header,
            "question": self.prompt,
            "options": [item.to_request_option() for item in self.options],
        }


@dataclass(frozen=True)
class NativeInteractionSpec:
    checkpoint_id: str
    gate_id: str
    revision: int
    questions: tuple[NativeQuestion, ...]
    custom_option_id: str = CUSTOM_OPTION_ID
    question_offset: int = 0

    def to_request_user_input(self) -> dict[str, list[dict[str, Any]]]:
        """Return only the shape accepted by the host request_user_input tool."""
        return {"questions": [item.to_request_question() for item in self.questions]}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def fingerprint(self) -> str:
        payload = {"checkpoint_id": self.checkpoint_id, "revision": self.revision, "questions": self.to_dict()["questions"]}
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class NativeInteractionResolution:
    checkpoint_id: str
    revision: int
    selections: dict[str, str]
    custom_text: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def submission_fingerprint(self) -> str:
        payload = self.to_dict()
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    def to_runtime_action(self, spec: NativeInteractionSpec) -> tuple[str, dict[str, Any]]:
        if len(spec.questions) == 1 and spec.questions[0].variable is None:
            question_id = spec.questions[0].question_id
            selected = self.selections[question_id]
            if selected == spec.custom_option_id:
                text = self.custom_text.get(question_id, "").strip()
                if not text:
                    raise NativeInteractionError("MISSING_CUSTOM_TEXT", "Other requires custom text.")
                return "CUSTOM", {"option_id": spec.custom_option_id, "text": text, "custom": text, "selection_source": "native_ui"}
            return "SELECT", {"candidate_id": selected, "selection_source": "native_ui"}

        updates: dict[str, dict[str, Any]] = {}
        for question in spec.questions:
            selected = self.selections[question.question_id]
            if not question.variable:
                raise NativeInteractionError("INVALID_NATIVE_SPEC", "A multi-question spec requires variables.")
            if selected == spec.custom_option_id:
                text = self.custom_text.get(question.question_id, "").strip()
                if not text:
                    raise NativeInteractionError("MISSING_CUSTOM_TEXT", f"Other requires custom text for {question.variable}.")
                updates[question.variable] = {"custom": text, "source": "human_custom"}
            else:
                updates[question.variable] = {"option_id": selected, "source": "human_select"}
        return "SELECT", {"field_updates": updates, "selection_source": "native_ui"}


class NativeInteractionAdapter:
    """Build and resolve native UI data without importing or calling Codex APIs."""

    _DIRECTION_GATES = {"CHARACTER_DIRECTION_GATE", "ART_DIRECTION_GATE"}
    _HEADERS = {
        "CHARACTER_DIRECTION_GATE": ("角色方向", "Character"),
        "ART_DIRECTION_GATE": ("美术方向", "Art"),
    }
    _VISUAL_NAMES = {
        "hair_color": ("发色", "Hair"),
        "hair_style_family": ("发型", "Hair Style"),
        "outfit_direction": ("服装方向", "Outfit"),
        "dominant_palette": ("主色调", "Palette"),
        "character_visual_style": ("视觉风格", "Style"),
        "major_accessories": ("主要配件", "Accessories"),
        "body_markings": ("身体标记", "Markings"),
        "eye_color": ("瞳色", "Eyes"),
        "nonhuman_trait_level": ("非人特征程度", "Non-human Traits"),
        "fanservice_level": ("性感程度", "Fanservice"),
        "body_build": ("体型", "Build"),
        "background_direction": ("背景方向", "Background"),
        "footwear_family": ("鞋履", "Footwear"),
        "legwear_family": ("腿部穿着", "Legwear"),
        "exposure_strategy": ("露肤策略", "Exposure"),
        "leg_accessory_family": ("腿部配件", "Leg Accessories"),
        "foot_visibility": ("足部可读性", "Foot Visibility"),
        "pose_intent": ("动作意图", "Pose Intent"),
    }

    def __init__(self, *, max_candidates: int = 3, max_questions: int = 3) -> None:
        self.max_candidates = max_candidates
        self.max_questions = max_questions

    def build(self, checkpoint: Any, *, question_offset: int = 0) -> NativeInteractionSpec:
        if str(checkpoint.status) != "OPEN":
            raise NativeInteractionError("CHECKPOINT_NOT_OPEN", "Only an open checkpoint can be rendered.")
        revision = self._revision(checkpoint)
        if checkpoint.gate_type in self._DIRECTION_GATES:
            questions = (self._direction_question(checkpoint, revision),)
        elif checkpoint.gate_type == "VISUAL_PREFERENCE_GATE":
            all_questions = self._visual_questions(checkpoint, revision)
            questions = tuple(all_questions[question_offset : question_offset + self.max_questions])
        else:
            raise NativeInteractionError("UNSUPPORTED_NATIVE_GATE", f"Unsupported native gate: {checkpoint.gate_type}")
        if not questions:
            raise NativeInteractionError("EMPTY_NATIVE_CHECKPOINT", "The checkpoint has no safe native questions.")
        return NativeInteractionSpec(str(checkpoint.checkpoint_id), str(checkpoint.gate_id), revision, questions, question_offset=question_offset)

    def resolve(self, spec: NativeInteractionSpec, answer: Mapping[str, Any]) -> NativeInteractionResolution:
        if not isinstance(answer, Mapping):
            raise NativeInteractionError("MISSING_NATIVE_ANSWER", "Native answer must be an object.")
        self._check_answer_metadata(spec, answer)
        answers = answer.get("answers")
        if not isinstance(answers, Mapping):
            raise NativeInteractionError("MISSING_NATIVE_ANSWER", "Native answer has no answers object.")
        question_ids = {question.question_id for question in spec.questions}
        if set(map(str, answers)) != question_ids:
            raise NativeInteractionError("INVALID_NATIVE_ANSWER", "Answer does not match the current checkpoint questions.")
        selections: dict[str, str] = {}
        custom_text: dict[str, str] = {}
        for question in spec.questions:
            label, other_text = self._answer_value(answers[question.question_id])
            mapping = self._label_mapping(question)
            if label in mapping:
                selections[question.question_id] = mapping[label]
            elif question.allow_other:
                # Codex returns native Other as the free-form text itself.
                if self._is_other(label) and not other_text:
                    raise NativeInteractionError("MISSING_CUSTOM_TEXT", "Other requires free-form text.")
                other_text = other_text or label
                if not other_text:
                    raise NativeInteractionError("MISSING_CUSTOM_TEXT", "Other requires free-form text.")
                selections[question.question_id] = CUSTOM_OPTION_ID
                custom_text[question.question_id] = other_text
            else:
                raise NativeInteractionError("INVALID_NATIVE_ANSWER", f"Answer is not valid for {question.question_id}.")
        return NativeInteractionResolution(spec.checkpoint_id, spec.revision, selections, custom_text)

    def _direction_question(self, checkpoint: Any, revision: int) -> NativeQuestion:
        real = self._candidate_options(checkpoint.options)
        if not real:
            raise NativeInteractionError("EMPTY_NATIVE_CHECKPOINT", "No real direction candidates are available.")
        zh, en = self._HEADERS[checkpoint.gate_type]
        locale = str(checkpoint.options[0].get("locale", "en-US")) if checkpoint.options else "en-US"
        zh_locale = locale.lower().startswith("zh")
        payload = checkpoint.prompt_payload or {}
        prompt = str(payload.get("prompt") or ("请选择一个方向继续设计。" if zh_locale else "Choose one direction to continue the design."))
        return NativeQuestion(
            "direction",
            zh if zh_locale else en,
            prompt,
            tuple(self._native_option(item, zh_locale) for item in real),
            allow_other=bool(checkpoint.custom_input_allowed),
        )

    def _visual_questions(self, checkpoint: Any, revision: int) -> list[NativeQuestion]:
        questions: list[NativeQuestion] = []
        payload = checkpoint.prompt_payload or {}
        for field in payload.get("variables", []):
            variable = str(field.get("variable", ""))
            if not variable or field.get("resolved"):
                continue
            real = self._candidate_options(field.get("options", []))
            if not real:
                continue
            raw_display_name = str(field.get("display_name") or variable)
            zh_locale = any("\u3400" <= char <= "\u9fff" for char in str(payload.get("title", "")) + raw_display_name)
            display_name = self._VISUAL_NAMES.get(variable, (raw_display_name, raw_display_name))[0 if zh_locale else 1]
            locale = "zh-CN" if zh_locale else "en-US"
            header = display_name if len(display_name) <= 12 else variable.replace("_", " ").title()[:12]
            prompt = f"{display_name}：请选择一个方向。" if locale == "zh-CN" else f"Choose a {display_name.lower()} direction."
            native_options: list[NativeOption] = []
            seen_labels: set[str] = set()
            for item in real:
                option = self._native_option(item, locale == "zh-CN")
                label_key = self._strip_recommended(option.label)
                if label_key in seen_labels:
                    continue
                seen_labels.add(label_key)
                native_options.append(option)
            if native_options and not any(option.recommended for option in native_options):
                first = native_options[0]
                marker = "（推荐）" if locale == "zh-CN" else " (Recommended)"
                label = first.label if first.label.endswith(_RECOMMENDED_SUFFIXES) else first.label + marker
                native_options[0] = NativeOption(first.candidate_id, label, first.description, True)
            if len(native_options) >= 2:
                questions.append(NativeQuestion(f"visual_{variable}", header[:12], prompt, tuple(native_options), allow_other=True, variable=variable))
        return questions

    def _candidate_options(self, options: Any) -> list[Mapping[str, Any]]:
        real = [item for item in (options or []) if isinstance(item, Mapping) and not item.get("is_custom") and str(item.get("option_id", item.get("id", ""))) != CUSTOM_OPTION_ID]
        recommended = [item for item in real if item.get("is_recommended")]
        ordered = recommended + [item for item in real if item not in recommended]
        return ordered[: self.max_candidates]

    @staticmethod
    def _revision(checkpoint: Any) -> int:
        try:
            return int((checkpoint.prompt_payload or {}).get("candidate_revision", 0))
        except (TypeError, ValueError):
            raise NativeInteractionError("INVALID_CHECKPOINT_REVISION", "Checkpoint revision is invalid.")

    @staticmethod
    def _native_option(item: Mapping[str, Any], zh_locale: bool) -> NativeOption:
        candidate_id = str(item.get("option_id", item.get("id", "")))
        label = str(item.get("display_title") or item.get("title_zh" if zh_locale else "title_en") or item.get("title") or candidate_id)
        marker = "（推荐）" if zh_locale else " (Recommended)"
        if item.get("is_recommended") and not label.endswith(_RECOMMENDED_SUFFIXES):
            label += marker
        description = str(item.get("display_description") or item.get("description_zh" if zh_locale else "description_en") or item.get("summary") or ("推荐的视觉方向。" if zh_locale and item.get("is_recommended") else "一个可选的视觉方向。" if zh_locale else "Recommended visual direction." if item.get("is_recommended") else "An available visual direction."))
        return NativeOption(candidate_id, label, description, bool(item.get("is_recommended")))

    @staticmethod
    def _label_mapping(question: NativeQuestion) -> dict[str, str]:
        mapping: dict[str, str] = {}
        stripped: dict[str, str] = {}
        for option in question.options:
            normalized = NativeInteractionAdapter._strip_recommended(option.label)
            if normalized in stripped and stripped[normalized] != option.candidate_id:
                raise NativeInteractionError("DUPLICATE_NATIVE_LABEL", f"Duplicate label in {question.question_id}: {normalized}")
            stripped[normalized] = option.candidate_id
            if option.label in mapping and mapping[option.label] != option.candidate_id:
                raise NativeInteractionError("DUPLICATE_NATIVE_LABEL", f"Duplicate label in {question.question_id}: {option.label}")
            mapping[option.label] = option.candidate_id
        exact_labels = set(mapping)
        for option in question.options:
            label = NativeInteractionAdapter._strip_recommended(option.label)
            if label in exact_labels and mapping[label] != option.candidate_id:
                continue
            if label in mapping and mapping[label] != option.candidate_id:
                raise NativeInteractionError("DUPLICATE_NATIVE_LABEL", f"Duplicate label in {question.question_id}: {label}")
            mapping[label] = option.candidate_id
        return mapping

    @staticmethod
    def _strip_recommended(label: str) -> str:
        for suffix in _RECOMMENDED_SUFFIXES:
            if label.endswith(suffix):
                return label[: -len(suffix)].rstrip()
        return label

    @staticmethod
    def _is_other(label: str) -> bool:
        return label.strip().lower() in _OTHER_LABELS

    @staticmethod
    def _answer_value(value: Any) -> tuple[str, str]:
        other_text = ""
        if isinstance(value, Mapping):
            raw = value.get("answers", value.get("answer"))
            other_text = str(value.get("other") or value.get("free_text") or value.get("free_form") or value.get("text") or "").strip()
        else:
            raw = value
        if isinstance(raw, (list, tuple)):
            if not raw:
                raise NativeInteractionError("MISSING_NATIVE_ANSWER", "Each native question requires an answer.")
            if len(raw) != 1:
                raise NativeInteractionError("INVALID_NATIVE_ANSWER", "Each native question requires exactly one answer.")
            raw = raw[0]
        if not isinstance(raw, str) or not raw.strip():
            raise NativeInteractionError("MISSING_NATIVE_ANSWER", "Each native question requires an answer.")
        return raw.strip(), other_text

    @staticmethod
    def _check_answer_metadata(spec: NativeInteractionSpec, answer: Mapping[str, Any]) -> None:
        answer_checkpoint = answer.get("checkpoint_id")
        if answer_checkpoint is not None and str(answer_checkpoint) != spec.checkpoint_id:
            raise NativeInteractionError("STALE_NATIVE_ANSWER", "Native answer belongs to another checkpoint.")
        answer_revision = answer.get("candidate_revision", answer.get("revision"))
        if answer_revision is not None:
            try:
                if int(answer_revision) != spec.revision:
                    raise NativeInteractionError("STALE_NATIVE_ANSWER", "Native answer belongs to another revision.")
            except (TypeError, ValueError):
                raise NativeInteractionError("STALE_NATIVE_ANSWER", "Native answer revision is invalid.")


def build_native_interaction_spec(checkpoint: Any) -> NativeInteractionSpec:
    return NativeInteractionAdapter().build(checkpoint)


__all__ = [
    "CUSTOM_OPTION_ID",
    "NativeInteractionAdapter",
    "NativeInteractionError",
    "NativeInteractionResolution",
    "NativeInteractionSpec",
    "NativeOption",
    "NativeQuestion",
    "build_native_interaction_spec",
]
