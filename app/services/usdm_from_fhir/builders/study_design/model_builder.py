"""
ModelBuilder — ResearchStudy.studyDesign[] (SEVCO coding) → USDM
StudyDesign.model (intervention model / cohort design).

Priority 43 — runs after CharacteristicsBuilder (42), same source array as
StudyDesignTypeBuilder/CharacteristicsBuilder.

FHIR encodes the USDM model.code as a SEVCO-coded CodeableConcept inside the
studyDesign[] array (see app/config/mappings/15_study_design.yaml, "Study
Design cohort design" row, for the forward direction — USDM model.code ->
SEVCO code). We scan studyDesign[] for the first entry carrying a known
cohort-design SEVCO code (SEVCO:01011/01012/01016) and map it back to the
CDISC Code. When none is found, falls back to C17998 "Unknown" (mirrors
readi_core's self::UNKNOWN case) instead of omitting the field.
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import STUDY_DESIGN_MODEL, STUDY_DESIGN_MODEL_UNKNOWN


class _Coding(TypedDict, total=False):
    code: str | None


class _CodeableConcept(TypedDict, total=False):
    coding: list[_Coding] | None


class ModelBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.model"

    def get_priority(self) -> int:
        return 43

    def build(self, context: UsdmBuildContext) -> dict:
        entries: list[_CodeableConcept] = context.fhir.get("studyDesign") or []

        code = self._find_model_code(entries)
        if code is None:
            return context.make_code(STUDY_DESIGN_MODEL_UNKNOWN["code"], STUDY_DESIGN_MODEL_UNKNOWN["decode"])

        return context.lookup_code(STUDY_DESIGN_MODEL, code)

    # -------------------------------------------------------------------------

    @staticmethod
    def _find_model_code(entries: list[_CodeableConcept]) -> str | None:
        for entry in entries:
            coding = entry.get("coding") or []
            for coding_item in coding:
                code = coding_item.get("code") if isinstance(coding_item, dict) else None
                if code in STUDY_DESIGN_MODEL:
                    return code
        return None