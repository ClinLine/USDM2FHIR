"""
CharacteristicsBuilder — ResearchStudy.studyDesign[] (SEVCO coding) → USDM
StudyDesign.characteristics.

Priority 42 — runs after StudyDesignTypeBuilder (41), same source array.

FHIR only ever emits a SEVCO:01003 ("randomized assignment") entry into
studyDesign[] when allocation is RANDOMIZED (see readi_core
ResearchStudyDesignBuilder); there is no FHIR-side code for NON_RANDOMIZED.
We scan studyDesign[] for that code and map it back to the CDISC C46079
"Randomized" Code; no match means an empty characteristics list, not a guess.
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import STUDY_DESIGN_CHARACTERISTIC


class _Coding(TypedDict, total=False):
    code: str | None


class _CodeableConcept(TypedDict, total=False):
    coding: list[_Coding] | None


class CharacteristicsBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.characteristics"

    def get_priority(self) -> int:
        return 42

    def build(self, context: UsdmBuildContext) -> list:
        entries: list[_CodeableConcept] = context.fhir.get("studyDesign") or []

        characteristics: list[dict] = []
        for entry in entries:
            for coding in entry.get("coding") or []:
                code = coding.get("code") if isinstance(coding, dict) else None
                if code in STUDY_DESIGN_CHARACTERISTIC:
                    characteristics.append(context.lookup_code(STUDY_DESIGN_CHARACTERISTIC, code))

        return characteristics