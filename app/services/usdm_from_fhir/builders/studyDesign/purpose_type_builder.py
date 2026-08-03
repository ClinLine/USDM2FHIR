"""
PurposeTypeBuilder — ResearchStudy.purposeType[] → USDM StudyDesign.intentTypes
+ StudyDesign.subTypes.

Priority 50 — no cross-builder dependencies.

Both intentTypes and subTypes are encoded in the same FHIR array
(purposeType[].coding) — see app/config/mappings/06_purpose_type.yaml, where
USDM intentTypes and subTypes both map to fhir_path purposeType.coding, only
distinguished by which CDISC code they carry. We classify each coding entry
against PURPOSE_INTENT_TYPE / PURPOSE_SUB_TYPE and route it accordingly;
unrecognized codes are skipped (same convention as every other builder here).

Writes 'version.studyDesign.subTypes' as a side-channel key (same pattern as
OrganizationsBuilder / StudyDesignTypeBuilder) since one builder can only
declare a single get_key().
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import PURPOSE_INTENT_TYPE, PURPOSE_SUB_TYPE


class _Coding(TypedDict, total=False):
    code: str | None


class _CodeableConcept(TypedDict, total=False):
    coding: list[_Coding] | None


class PurposeTypeBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.intentTypes"

    def get_priority(self) -> int:
        return 50

    def build(self, context: UsdmBuildContext) -> list:
        entries: list[_CodeableConcept] = context.fhir.get("purposeType") or []

        intent_types: list[dict] = []
        sub_types: list[dict] = []
        seen_intent: set[str] = set()
        seen_sub: set[str] = set()

        for entry in entries:
            for coding in entry.get("coding") or []:
                code = coding.get("code") if isinstance(coding, dict) else None
                if code is None:
                    continue

                if code in PURPOSE_INTENT_TYPE and code not in seen_intent:
                    seen_intent.add(code)
                    intent_types.append(context.make_code(**PURPOSE_INTENT_TYPE[code]))
                elif code in PURPOSE_SUB_TYPE and code not in seen_sub:
                    seen_sub.add(code)
                    sub_types.append(context.make_code(**PURPOSE_SUB_TYPE[code]))

        context.set("version.studyDesign.subTypes", sub_types)
        return intent_types