"""
TitlesBuilder — ResearchStudy.label → USDM titles array.

Priority 30 — no cross-builder dependencies.

A label item without a type.coding.code is skipped entirely (USDM requires
a type Code on every StudyTitle).

Labels of the same type.coding.code that differ only by `language` are
per-locale variants of the same title (readi_core's ResearchLabelBuilder emits
one label per ClinicalTrialTranslation locale). The entry with no `language`
is the default-locale text; the rest are reconstructed into the USDM
"languages" translation extension (mirrors TitlesSectionBuilder.php).
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import TITLE_TYPE
from app.services.usdm_from_fhir.builders.translation_extension import build_translation_extension


class _Coding(TypedDict, total=False):
    code: str | None
    display: str | None
    system: str | None


class _CodeableConcept(TypedDict, total=False):
    coding: list[_Coding] | None


class _Label(TypedDict, total=False):
    value: str | None
    type: _CodeableConcept | None
    language: str | None


class TitlesBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.titles"

    def get_priority(self) -> int:
        return 30

    def build(self, context: UsdmBuildContext) -> list:
        labels: list[_Label] = context.fhir.get("label") or []
        result = []
        idx = 0

        # Group labels by title type, preserving first-seen order.
        groups: dict[str, list[_Label]] = {}
        for label in labels:
            coding_field = (label.get("type") or {}).get("coding") or []
            # FHIR coding is always an array; guard against legacy dict shape too
            first_coding: dict = (
                coding_field[0] if isinstance(coding_field, list) else coding_field
            )
            type_code: str | None = first_coding.get("code") if isinstance(first_coding, dict) else None
            if not type_code:
                # USDM StudyTitle requires a type — skip labels without one
                continue
            groups.setdefault(type_code, []).append(label)

        for type_code, group in groups.items():
            level_code = context.lookup_code(TITLE_TYPE, type_code)
            if level_code is None:
                continue  # unknown/unconfirmed title type code — skip

            default_entries = [item for item in group if not item.get("language")]
            base = default_entries[0] if default_entries else group[0]
            translated_entries = [item for item in group if item is not base and item.get("language")]

            title_id = f"StudyTitle_{idx}"
            idx += 1

            title: dict = {
                "id": title_id,
                "name": title_id.upper(),
                "text": base.get("value") or "",
                "type": level_code,
                "instanceType": "StudyTitle",
            }

            values = [
                (item["language"], item["value"])
                for item in translated_entries
                if item.get("language") and item.get("value")
            ]
            if values:
                title["extensionAttributes"] = [build_translation_extension(context, values)]
            else:
                title["extensionAttributes"] = []

            result.append(title)

        return result

