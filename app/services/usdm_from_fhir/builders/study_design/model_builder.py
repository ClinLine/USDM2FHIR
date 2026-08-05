"""
ModelBuilder — ResearchStudy.studyDesign[] (SEVCO or ct.gov ObservationalModel
coding) → USDM StudyDesign.model (intervention model / cohort design, or
observational model).

Priority 43 — runs after CharacteristicsBuilder (42), same source array as
StudyDesignTypeBuilder/CharacteristicsBuilder.

FHIR encodes the USDM model.code two different ways depending on study type
(see app/config/mappings/15_study_design.yaml for the forward direction):
  - Interventional: a SEVCO-coded CodeableConcept ("Study Design cohort
    design" row) — USDM model.code -> SEVCO code.
  - Observational: a CodeableConcept coded against the ClinicalTrials.gov
    ObservationalModel enum ("Study Design observational model" row) — USDM
    model.code -> raw ct.gov enum value (e.g. "CASE_ONLY").

We scan studyDesign[] first for a known cohort-design SEVCO code
(SEVCO:01011/01012/01016), then for a known ct.gov ObservationalModel code,
and map whichever is found back to the CDISC Code. When neither is found,
falls back to C17998 "Unknown" (mirrors readi_core's self::UNKNOWN case)
instead of omitting the field.
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import (
    STUDY_DESIGN_MODEL,
    STUDY_DESIGN_MODEL_UNKNOWN,
    STUDY_DESIGN_OBSERVATIONAL_MODEL,
)


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

        code = self._find_code(entries, STUDY_DESIGN_MODEL)
        if code is not None:
            return context.lookup_code(STUDY_DESIGN_MODEL, code)

        observational_code = self._find_code(entries, STUDY_DESIGN_OBSERVATIONAL_MODEL)
        if observational_code is not None:
            return context.lookup_code(STUDY_DESIGN_OBSERVATIONAL_MODEL, observational_code)

        return context.make_code(STUDY_DESIGN_MODEL_UNKNOWN["code"], STUDY_DESIGN_MODEL_UNKNOWN["decode"])

    # -------------------------------------------------------------------------

    @staticmethod
    def _find_code(entries: list[_CodeableConcept], table: dict[str, dict]) -> str | None:
        for entry in entries:
            coding = entry.get("coding") or []
            for coding_item in coding:
                code = coding_item.get("code") if isinstance(coding_item, dict) else None
                if code in table:
                    return code
        return None