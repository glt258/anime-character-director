"""Deterministic natural-language intent parsing for interaction gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import re
from typing import Any, Mapping, Sequence


class IntentType(str, Enum):
    SELECTION = "SELECTION"
    MIX_SELECTION = "MIX_SELECTION"
    CUSTOM_UPDATE = "CUSTOM_UPDATE"
    DELEGATION = "DELEGATION"
    PARTIAL_DELEGATION = "PARTIAL_DELEGATION"
    ACCEPT_RECOMMENDED = "ACCEPT_RECOMMENDED"
    ACCEPT_ALL_RECOMMENDED = "ACCEPT_ALL_RECOMMENDED"
    BACK = "BACK"
    MODE_SWITCH = "MODE_SWITCH"
    REGENERATE_OPTIONS = "REGENERATE_OPTIONS"
    CANCEL = "CANCEL"
    CONTINUE = "CONTINUE"
    QUESTION_ONLY = "QUESTION_ONLY"
    CONSTRAINT_UPDATE = "CONSTRAINT_UPDATE"
    AMBIGUOUS = "AMBIGUOUS"
    INVALID = "INVALID"


@dataclass
class ParsedInteractionIntent:
    intent_type: str
    action: str | None = None
    target_gate: str | None = None
    selected_options: list[str] = field(default_factory=list)
    field_updates: dict[str, Any] = field(default_factory=dict)
    delegated_fields: list[str] = field(default_factory=list)
    accepted_recommended_fields: list[str] = field(default_factory=list)
    mode_switch_target: str | None = None
    question: str | None = None
    regenerate_requested: bool = False
    continue_requested: bool = False
    cancel_requested: bool = False
    confidence: float = 0.0
    needs_clarification: bool = False
    clarification_reason: str = ""
    raw_text: str = ""
    rationale: str = ""
    human_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_payload(self) -> dict[str, Any]:
        return {
            "intent_type": self.intent_type,
            "target_gate": self.target_gate,
            "selected_options": list(self.selected_options),
            "field_updates": self.field_updates,
            "delegated_fields": list(self.delegated_fields),
            "accepted_recommended_fields": list(self.accepted_recommended_fields),
            "mode_switch_target": self.mode_switch_target,
            "question": self.question,
            "regenerate_requested": self.regenerate_requested,
            "continue_requested": self.continue_requested,
            "cancel_requested": self.cancel_requested,
            "confidence": self.confidence,
            "needs_clarification": self.needs_clarification,
            "clarification_reason": self.clarification_reason,
            "raw_text": self.raw_text,
            "rationale": self.rationale,
            "human_fields": list(self.human_fields),
        }


class ExplicitConstraintExtractor:
    """Extract high-confidence user constraints before any exploration."""

    _HAIR = {
        "粉": "粉发",
        "粉色": "粉发",
        "银灰": "银灰发",
        "银白": "银白发",
        "银": "银发",
        "白": "白发",
        "黑": "黑发",
        "蓝": "蓝发",
        "红": "红发",
        "金": "金发",
        "紫": "紫发",
    }
    _COLORS = {"粉": "pink", "粉色": "pink", "银": "silver", "银白": "silver-white", "银灰": "silver-gray", "白": "white", "黑": "black", "蓝": "blue", "红": "red", "金": "gold", "紫": "purple", "绿": "green", "绿色": "green", "琥珀": "amber", "teal": "teal"}

    def extract(self, text: str) -> dict[str, Any]:
        raw = str(text)
        lower = raw.lower()
        constraints: dict[str, Any] = {"raw": raw, "explicit_user_fields": [], "negative_constraints": {}, "constraint_provenance": {}}
        positive: dict[str, Any] = {}
        negative: dict[str, Any] = {}

        def positive_field(name: str, value: Any) -> None:
            constraints[name] = value
            positive[name] = value
            if name not in constraints["explicit_user_fields"]:
                constraints["explicit_user_fields"].append(name)
            constraints["constraint_provenance"][name] = "explicit_user"

        def negative_field(name: str, value: Any) -> None:
            negative[name] = value
            constraints["constraint_provenance"][name] = "explicit_user"

        hair_matches = list(re.finditer(r"(银灰|银白|粉色|粉|银|白|黑|蓝|红|金|紫)(?:色)?(?:的)?(?:长|短)?发", raw, re.IGNORECASE))
        if hair_matches:
            token = hair_matches[-1].group(1)
            positive_field("hair_color", self._HAIR.get(token, token.lower()))
        if "短发" in raw:
            positive_field("hair_style_family", "short hair")
        elif "长发" in raw:
            positive_field("hair_style_family", "long hair")
        if re.search(r"很拽|拽|傲娇|高冷|冷淡|arrogant|aloof", raw, re.IGNORECASE):
            positive_field("personality", "arrogant/aloof")
        if re.search(r"成年|adult", raw, re.IGNORECASE):
            positive_field("age_group", "adult")
        if re.search(r"女性|女人|女角色|female|woman", raw, re.IGNORECASE):
            positive_field("gender", "female")
        elif re.search(r"男性|男人|男角色|male|man", raw, re.IGNORECASE):
            positive_field("gender", "male")

        eye = self._last_color(raw, r"(?:眼睛|瞳色|眼眸)(?:改成|换成|用|是|为)?\s*(银灰|银白|粉色|粉|银|白|黑|蓝|红|金|紫|绿|绿色|琥珀)")
        if eye:
            positive_field("eye_color", self._COLORS.get(eye, eye))
        if re.search(r"白色连裤袜|白色\s*连裤袜|white opaque tights", raw, re.IGNORECASE):
            positive_field("legwear_family", "white opaque tights")
            positive_field("tights", "white opaque")
        if re.search(r"不要(?:黑丝|丝袜|连裤袜|长袜)|不穿(?:黑丝|丝袜|连裤袜|长袜)|no stockings|no tights", raw, re.IGNORECASE):
            constraints["legwear_family"] = "none"
            if "legwear_family" not in constraints["explicit_user_fields"]:
                constraints["explicit_user_fields"].append("legwear_family")
            negative_field("forbid_legwear", "stockings/tights")
        if re.search(r"裸足|赤脚|barefoot", raw, re.IGNORECASE):
            positive_field("footwear_family", "barefoot")
        if re.search(r"不要高跟鞋|不穿高跟鞋|no high heels", raw, re.IGNORECASE):
            negative_field("forbid_footwear_family", "heels")
        if re.search(r"不要裙子|不穿裙子|no skirt", raw, re.IGNORECASE):
            negative_field("forbid_outfit_lower", "skirt")
        if re.search(r"短裤|裤装|长裤|shorts|trousers|pants", raw, re.IGNORECASE):
            positive_field("outfit_lower", "shorts/pants")
        if re.search(r"性感程度\s*(?:为|改成|换成)?\s*中等|中等性感|moderate fanservice", raw, re.IGNORECASE):
            positive_field("fanservice_level", "moderate")
        if re.search(r"兽耳|狐狸|狐系|fox", raw, re.IGNORECASE):
            positive_field("nonhuman_trait_level", "subtle fox traits")
        if re.search(r"正面|正对镜头|站立|front-facing", raw, re.IGNORECASE):
            positive_field("pose_intent", "STABLE_OPEN")

        constraints["positive_constraints"] = positive
        constraints["negative_constraints"] = negative
        if not constraints["explicit_user_fields"]:
            constraints.pop("explicit_user_fields")
        return constraints

    @staticmethod
    def _last_color(text: str, pattern: str) -> str | None:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        return matches[-1].group(1) if matches else None


class NaturalLanguageInteractionParser:
    """A small deterministic parser at the interaction seam.

    The parser only describes intent. Gate legality, state changes, and
    provenance remain in InteractionRuntime and GateResolver.
    """

    _FIELD_ALIASES = {
        "hair_color": ("发色", "头发", "发型"),
        "outfit_direction": ("衣服", "服装", "上衣", "穿着"),
        "footwear_family": ("鞋子", "鞋"),
        "eye_color": ("眼睛", "瞳色", "眼眸"),
        "legwear_family": ("黑丝", "丝袜", "连裤袜", "长袜"),
        "fanservice_level": ("性感程度", "性感"),
        "hair_style_family": ("发型",),
    }
    _COLOR_VALUES = {
        "粉": "pink", "粉色": "pink", "银": "silver", "银白": "silver-white", "银灰": "silver-gray",
        "白": "white", "蓝": "blue", "红": "red", "黑": "black", "金": "gold", "紫": "purple", "绿": "green",
    }

    def parse(self, text: str, context: Mapping[str, Any] | None = None) -> ParsedInteractionIntent:
        raw = str(text).strip()
        ctx = context or {}
        gate = str(ctx.get("gate_type") or "")
        mode = str(ctx.get("mode") or "")
        options = list(ctx.get("options") or [])
        option_ids = [str(item.get("id")) for item in options if item.get("id")]
        variables = dict(ctx.get("visual_variables") or {})
        base = {"target_gate": gate, "raw_text": raw}
        if not raw:
            return ParsedInteractionIntent(IntentType.INVALID.value, confidence=1.0, needs_clarification=True, clarification_reason="请告诉我你想选择、修改，还是交给 AI。", rationale="empty input", **base)
        if self._is_question(raw):
            return ParsedInteractionIntent(IntentType.QUESTION_ONLY.value, question=raw, confidence=0.98, rationale="question does not imply selection", **base)
        if re.search(r"^(?:取消|不做了(?:[，,]?取消)?|先算了|停止这个角色|cancel)\s*[。.!！]?$", raw, re.IGNORECASE):
            return ParsedInteractionIntent(IntentType.CANCEL.value, action="CANCEL", cancel_requested=True, confidence=0.99, rationale="explicit cancellation", **base)
        if self._is_regenerate(raw):
            return ParsedInteractionIntent(IntentType.REGENERATE_OPTIONS.value, action="REGENERATE_OPTIONS", regenerate_requested=True, confidence=0.97, rationale="user requested another set of options", **base)
        if self._is_back(raw):
            target = "CHARACTER" if re.search(r"人物|角色方向|最开始", raw) else "ART" if re.search(r"美术|视觉方向", raw) else None
            return ParsedInteractionIntent(IntentType.BACK.value, action="BACK", confidence=0.96, rationale="explicit return request", target_gate=target or gate, **{k: v for k, v in base.items() if k != "target_gate"})

        partial = self._partial_delegate(raw, variables) if gate == "VISUAL_PREFERENCE_GATE" else None
        if partial:
            return ParsedInteractionIntent(IntentType.PARTIAL_DELEGATION.value, action="PARTIAL_DELEGATE", confidence=0.96, rationale="named fields remain human-owned; remaining fields are delegated", human_fields=partial["human_fields"], field_updates=partial["field_updates"], delegated_fields=partial["delegated_fields"], **base)

        if mode == "USER_DECIDE" and re.search(r"后面.*(?:都|全|交给)|剩下.*(?:你来|你决定)|全交给你", raw):
            return ParsedInteractionIntent(IntentType.MODE_SWITCH.value, action="DELEGATE", mode_switch_target="AI_DECIDE", confidence=0.97, rationale="explicitly delegated the remaining workflow", **base)
        if mode == "AI_DECIDE" and re.search(r"等一下|等等|想自己选|让我选|接下来我来决定|不要直接替我决定", raw):
            return ParsedInteractionIntent(IntentType.MODE_SWITCH.value, action="DELEGATE", mode_switch_target="USER_DECIDE", confidence=0.96, rationale="explicitly reclaimed control", **base)

        if self._is_delegate(raw) and not (gate == "VISUAL_PREFERENCE_GATE" and self._field_in_text(raw, variables)):
            return ParsedInteractionIntent(IntentType.DELEGATION.value, action="DELEGATE", confidence=0.97, rationale="explicit current-gate delegation", **base)

        if self._is_all_recommended(raw):
            updates = self._visual_updates(raw, variables)
            return ParsedInteractionIntent(IntentType.ACCEPT_ALL_RECOMMENDED.value, action="USE_ALL_RECOMMENDED", accepted_recommended_fields=[name for name in variables if name not in updates], field_updates=updates, confidence=0.97, rationale="accept recommendations except explicit overrides", **base)

        if self._is_single_recommended(raw, variables):
            name = self._field_in_text(raw, variables)
            if name:
                return ParsedInteractionIntent(IntentType.ACCEPT_RECOMMENDED.value, action="USE_RECOMMENDED", accepted_recommended_fields=[name], confidence=0.96, rationale="accepted one field recommendation", field_updates={name: {"source": "human_accept_recommended"}}, **base)

        if re.search(r"^继续\s*[。.!！]?$", raw, re.IGNORECASE):
            return ParsedInteractionIntent(IntentType.CONTINUE.value, continue_requested=True, confidence=0.99, rationale="continue request", **base)

        if gate in {"CHARACTER_DIRECTION_GATE", "ART_DIRECTION_GATE"}:
            mix = self._candidate_mix(raw, option_ids)
            if mix:
                field_mix = self._field_mix(raw, option_ids)
                return ParsedInteractionIntent(IntentType.MIX_SELECTION.value, action="MIX", selected_options=mix, confidence=0.95, rationale="combined candidate directions", field_updates={"field_mix": field_mix} if field_mix else {}, **base)
            visual_updates = self._visual_updates(raw, variables)
            if visual_updates:
                return ParsedInteractionIntent(IntentType.CONSTRAINT_UPDATE.value, action="CONSTRAINT_UPDATE", field_updates=visual_updates, confidence=0.9, rationale="future visual constraint saved without selecting the current candidate gate", **base)
            selected = self._candidate_selection(raw, option_ids)
            if selected:
                return ParsedInteractionIntent(IntentType.SELECTION.value, action="SELECT", selected_options=[selected], confidence=0.99, rationale="matched candidate id or ordinal", **base)
            if "中间" in raw and option_ids:
                middle = [option_ids[(len(option_ids) - 1) // 2], option_ids[len(option_ids) // 2]] if len(option_ids) % 2 == 0 else [option_ids[len(option_ids) // 2]]
                if len(middle) == 1:
                    return ParsedInteractionIntent(IntentType.SELECTION.value, action="SELECT", selected_options=middle, confidence=0.9, rationale="resolved the only middle option", **base)
                return ParsedInteractionIntent(IntentType.AMBIGUOUS.value, confidence=0.98, needs_clarification=True, clarification_reason=f"你指 {middle[0]} 还是 {middle[1]}？", rationale="two middle options are equally plausible", **base)
            constraint_updates = ExplicitConstraintExtractor().extract(raw)
            field_updates = {name: {"value": value, "source": "explicit_user"} for name, value in constraint_updates.items() if name in variables}
            if field_updates:
                return ParsedInteractionIntent(IntentType.CONSTRAINT_UPDATE.value, action="CONSTRAINT_UPDATE", field_updates=field_updates, confidence=0.9, rationale="future visual constraint saved without selecting the current candidate gate", **base)
            if re.search(r"自定义|自己描述|我想要一个|做成", raw):
                return ParsedInteractionIntent(IntentType.CUSTOM_UPDATE.value, action="CUSTOM", confidence=0.85, rationale="explicit custom candidate direction", **base)
            return ParsedInteractionIntent(IntentType.INVALID.value, confidence=0.55, needs_clarification=True, clarification_reason="请选一个当前方向，或说“混一下”“你来决定”。", rationale="no safe candidate action matched", **base)

        if gate == "VISUAL_PREFERENCE_GATE":
            updates = self._visual_updates(raw, variables)
            field_delegates = [
                name
                for name in variables
                if self._field_alias_present(raw, name)
                and re.search(rf"(?:{'|'.join(map(re.escape, self._FIELD_ALIASES[name]))}).{{0,6}}(?:随你|你决定|交给你)", raw)
            ]
            if updates or field_delegates:
                if field_delegates or re.search(r"其他.*(?:随你|你决定|交给你)|剩下.*(?:随你|你决定|交给你)", raw):
                    human_fields = list(updates)
                    delegated = [name for name in variables if name not in human_fields]
                    return ParsedInteractionIntent(IntentType.PARTIAL_DELEGATION.value, action="PARTIAL_DELEGATE", field_updates=updates, human_fields=human_fields, delegated_fields=delegated, confidence=0.95, rationale="explicit visual overrides plus delegated remainder", **base)
                return ParsedInteractionIntent(IntentType.CUSTOM_UPDATE.value, action="CUSTOM", field_updates=updates, confidence=0.94, rationale="field-level visual updates", **base)
            if field_delegates:
                return ParsedInteractionIntent(IntentType.PARTIAL_DELEGATION.value, action="PARTIAL_DELEGATE", human_fields=[], delegated_fields=list(variables), confidence=0.9, rationale="named visual fields were delegated to AI", **base)
            if self._has_visual_field_request(raw, variables):
                human_fields = [name for name in variables if self._field_alias_present(raw, name)]
                delegated = [name for name in variables if name not in human_fields]
                return ParsedInteractionIntent(IntentType.PARTIAL_DELEGATION.value, action="PARTIAL_DELEGATE", human_fields=human_fields, delegated_fields=delegated, confidence=0.9, rationale="fields were named as human-owned without values", **base)
            return ParsedInteractionIntent(IntentType.INVALID.value, confidence=0.5, needs_clarification=True, clarification_reason="你可以修改发色、衣服、鞋子等少数字段，其余可按推荐或交给我。", rationale="no safe visual action matched", **base)

        return ParsedInteractionIntent(IntentType.INVALID.value, confidence=0.4, needs_clarification=True, clarification_reason="请告诉我下一步怎么处理。", rationale="unsupported gate context", **base)

    @staticmethod
    def _is_question(text: str) -> bool:
        return bool(re.search(r"[?？]|为什么|有何区别|什么区别|最大的区别|你推荐哪个|推荐哪个|你觉得哪个|哪个更适合", text, re.IGNORECASE))

    @staticmethod
    def _is_regenerate(text: str) -> bool:
        return bool(re.search(r"都不喜欢.*(?:再来|重新|换一批)|换一批|重新给几个|没有喜欢的|再生成几个方向", text))

    @staticmethod
    def _is_back(text: str) -> bool:
        return bool(re.search(r"返回上一步|回到上一步|重选前面|回去重选|重选最开始|换回上一步|重新选(?:角色|美术|视觉)方向|我还是想换角色方向", text))

    @staticmethod
    def _is_delegate(text: str) -> bool:
        return bool(re.search(r"你来决定|你决定|你来选|交给你|这个你定|你挑一个最好的|我不想选了", text))

    @staticmethod
    def _is_all_recommended(text: str) -> bool:
        return bool(re.search(r"都按(?:你)?(?:的)?推荐|全部按推荐|其他(?:就)?(?:按)?(?:你)?(?:的)?推荐|剩下都按推荐|就按你(?:的)?推荐|那就按你(?:的)?推荐|大体按推荐|这个按推荐", text))

    @staticmethod
    def _is_single_recommended(text: str, variables: Mapping[str, Any]) -> bool:
        return bool(re.search(r"按(?:你)?(?:的)?推荐", text)) and not NaturalLanguageInteractionParser._is_all_recommended(text) and bool(NaturalLanguageInteractionParser._field_in_text(text, variables))

    def _candidate_selection(self, text: str, option_ids: Sequence[str]) -> str | None:
        if not option_ids:
            return None
        upper = text.upper()
        match = re.search(r"(?:我选|选|就|还是|选择)\s*([A-Z])", upper)
        if not match:
            match = re.fullmatch(r"\s*([A-Z])(?:吧|了|比较好)?(?:\s*[,，。.!！]?\s*(?:然后)?继续)?", upper)
        if match and match.group(1) in option_ids:
            return match.group(1)
        ordinals = {"一": 1, "二": 2, "三": 3, "四": 4, "1": 1, "2": 2, "3": 3, "4": 4}
        match = re.search(r"第\s*([一二三四1-4])\s*(?:个|套|项)", text)
        if match:
            index = ordinals[match.group(1)] - 1
            return option_ids[index] if index < len(option_ids) else None
        if re.search(r"最后一个|最后一项|最后一套", text):
            return option_ids[-1]
        return None

    @staticmethod
    def _candidate_mix(text: str, option_ids: Sequence[str]) -> list[str] | None:
        letters = [letter for letter in re.findall(r"[A-D]", text.upper()) if letter in option_ids]
        if len(set(letters)) >= 2 and ("+" in text or re.search(r"混|结合|加|参考|整体感觉|轮廓|头发|衣服|服装", text)):
            return list(dict.fromkeys(letters))
        return None

    @staticmethod
    def _field_mix(text: str, option_ids: Sequence[str]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name, aliases in (("hair_color", ("头发", "发色", "发型")), ("outfit_direction", ("衣服", "服装", "上衣"))):
            values = []
            for alias in aliases:
                values.extend(re.findall(rf"([A-D])[^A-D，,。；;]{{0,8}}{alias}", text.upper()))
            values = [value for value in values if value in option_ids]
            if values:
                result[name] = list(dict.fromkeys(values))
        return result

    def _visual_updates(self, text: str, variables: Mapping[str, Any]) -> dict[str, Any]:
        updates: dict[str, Any] = {}

        def put(name: str, value: Any = None, *, option_id: str | None = None, source: str | None = None, mix: list[str] | None = None) -> None:
            if name not in variables:
                return
            update: dict[str, Any] = {}
            if option_id:
                update["option_id"] = option_id
            elif mix:
                update["mix"] = mix
            else:
                update["value"] = value
            if source:
                update["source"] = source
            updates[name] = update

        hair_match = re.search(r"(?:发色|头发).{0,8}(?:(?:改成|换成|换为|要|想要)\s*)?(银灰|银白|银|粉色|粉|深红|红色|红|黑|蓝|白)", text)
        if hair_match:
            put("hair_color", self._COLOR_VALUES.get(hair_match.group(1), hair_match.group(1)))
        else:
            match = re.search(r"(?:发色|头发)(?:用|我?选)\s*([A-D])", text.upper())
            if match:
                put("hair_color", option_id=match.group(1), source="human_select")
            else:
                match = re.search(r"(?:我(?:就)?要|我想要)\s*(银灰发|银白发|银发|粉色发|粉发|深红发|红发|黑发|蓝发|白发)", text)
                if match:
                    put("hair_color", match.group(1))
        match = re.search(r"(?:衣服|服装|上衣).{0,6}(?:(?:用|选|改成|换成)\s*)?([A-D])\s*(?:和|\+)\s*([A-D]).{0,5}(?:混|结合)", text.upper())
        if match:
            put("outfit_direction", mix=[match.group(1), match.group(2)], source="human_mix")
        else:
            match = re.search(r"(?:衣服|服装|上衣).{0,6}(?:(?:用|选|改成|换成)\s*)?([A-D])", text.upper())
            if match:
                put("outfit_direction", option_id=match.group(1), source="human_select")
        match = re.search(r"(?:眼睛|瞳色|眼眸)(?:用|选|改成|换成)?\s*([A-D])", text.upper())
        if match:
            put("eye_color", option_id=match.group(1), source="human_select")
        else:
            match = re.search(r"(?:眼睛|瞳色|眼眸).{0,6}(?:改成|换成|用|是)\s*(绿色|绿|琥珀|蓝|紫)", text)
            if match:
                put("eye_color", self._COLOR_VALUES.get(match.group(1), match.group(1)))
        if re.search(r"鞋子.*(?:裸足|赤脚)|(?:裸足|赤脚).*鞋子", text):
            put("footwear_family", "barefoot")
        if re.search(r"(?:不要|不穿)(?:黑丝|丝袜|连裤袜)|(?:黑丝|丝袜|连裤袜)(?:不要|不穿)", text):
            put("legwear_family", "none")
        elif re.search(r"白色连裤袜", text):
            put("legwear_family", "white opaque tights")
        match = re.search(r"性感程度\s*(?:改成|换成|为)?\s*(低|中等|高|moderate|low|high)", text, re.IGNORECASE)
        if match:
            put("fanservice_level", {"低": "restrained", "中等": "moderate", "高": "strong", "low": "restrained", "moderate": "moderate", "high": "strong"}.get(match.group(1).lower(), match.group(1)))
        return updates

    def _partial_delegate(self, text: str, variables: Mapping[str, Any]) -> dict[str, Any] | None:
        has_delegate = bool(re.search(r"其他.*(?:你决定|随你|交给你)|剩下.*(?:你决定|随你|交给你)|其他你决定|剩下你来", text))
        has_human = bool(re.search(r"自己选|我选|我来定|让我选|我想自己", text))
        updates = self._visual_updates(text, variables)
        if not has_delegate and not (has_human and updates):
            return None
        human_fields = list(updates)
        for name in variables:
            if self._field_alias_present(text, name) and name not in human_fields and has_human:
                human_fields.append(name)
        delegated = [name for name in variables if name not in human_fields]
        return {"human_fields": human_fields, "delegated_fields": delegated, "field_updates": updates}

    def _has_visual_field_request(self, text: str, variables: Mapping[str, Any]) -> bool:
        return bool(re.search(r"自己选|我选|我来定|让我选|我想自己", text)) and bool(self._field_in_text(text, variables))

    @staticmethod
    def _field_in_text(text: str, variables: Mapping[str, Any]) -> str | None:
        for name in variables:
            if NaturalLanguageInteractionParser._field_alias_present(text, name):
                return name
        return None

    @staticmethod
    def _field_alias_present(text: str, name: str) -> bool:
        return any(alias in text for alias in NaturalLanguageInteractionParser._FIELD_ALIASES.get(name, ()))


__all__ = ["ExplicitConstraintExtractor", "IntentType", "NaturalLanguageInteractionParser", "ParsedInteractionIntent"]
