"""
StudyDesignTypeBuilder — ResearchStudy.studyDesign[] (SEVCO coding) → USDM
StudyDesign.studyType + instanceType.

Priority 41 — runs after ObjectivesBuilder (40). Writes its own key
('version.studyDesign.studyType') plus a side-channel key
('version.studyDesign._instanceType') that FhirToUsdmService._assemble_study_design
reads to pick InterventionalStudyDesign vs ObservationalStudyDesign — same
pattern OrganizationsBuilder uses for 'version._orgsByName'.

FHIR encodes the USDM studyType as a SEVCO-coded CodeableConcept inside the
studyDesign[] array (see app/config/mappings/15_study_design.yaml for the
forward direction — USDM studyType.code -> {SEVCO code, raw CDISC code}).
We scan studyDesign[] for the first entry carrying a known SEVCO study-type
code and map it back to the CDISC Code + USDM instanceType.
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import STUDY_DESIGN_TYPE


class _Coding(TypedDict, total=False):
    code: str | None


class _CodeableConcept(TypedDict, total=False):
    coding: list[_Coding] | None
    text: str | None


class StudyDesignTypeBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.studyType"

    def get_priority(self) -> int:
        return 41

    def build(self, context: UsdmBuildContext) -> dict | None:
        entries: list[_CodeableConcept] = context.fhir.get("studyDesign") or []

        sevco_code = self._find_study_type_code(entries)
        if sevco_code is None:
            return None

        entry = STUDY_DESIGN_TYPE.get(sevco_code)
        if entry is None:
            return None

        context.set("version.studyDesign._instanceType", entry["instance_type"])
        return context.lookup_code(STUDY_DESIGN_TYPE, sevco_code)

    # -------------------------------------------------------------------------

    @staticmethod
    def _find_study_type_code(entries: list[_CodeableConcept]) -> str | None:
        for entry in entries:
            coding = entry.get("coding") or []
            for coding_item in coding:
                code = coding_item.get("code") if isinstance(coding_item, dict) else None
                if code in STUDY_DESIGN_TYPE:
                    return code
        return None