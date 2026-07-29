"""
TitlesBuilder — ResearchStudy.label → USDM titles array.

Priority 30 — no cross-builder dependencies.

A label item without a type.coding.code is skipped entirely (USDM requires
a type Code on every StudyTitle).
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import TITLE_TYPE


class _Coding(TypedDict, total=False):
    code: str | None
    display: str | None
    system: str | None


class _CodeableConcept(TypedDict, total=False):
    coding: _Coding | None


class _Label(TypedDict, total=False):
    value: str | None
    type: _CodeableConcept | None


class TitlesBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.titles"

    def get_priority(self) -> int:
        return 30

    def build(self, context: UsdmBuildContext) -> list:
        labels: list[_Label] = context.fhir.get("label") or []
        result = []
        idx = 0

        for label in labels:
            type_code: str | None = (
                (label.get("type") or {})
                .get("coding", {})
                .get("code")
            )
            if not type_code:
                # USDM StudyTitle requires a type — skip labels without one
                continue

            level_code = context.lookup_code(TITLE_TYPE, type_code)
            if level_code is None:
                continue  # unknown/unconfirmed title type code — skip

            title_id = f"StudyTitle_{idx}"
            idx += 1
            result.append({
                "id": title_id,
                "name": title_id.upper(),
                "text": label.get("value") or "",
                "type": level_code,
                "instanceType": "StudyTitle",
            })

        return result

