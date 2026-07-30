"""
PhaseBuilder — ResearchStudy.phase.coding[] → USDM StudyDesign.studyPhase
(AliasCode wrapping a standardCode Code).

Priority 51 — no cross-builder dependencies.

FHIR encodes phase as a CodeableConcept using the HL7 research-study-phase
system (see app/config/mappings/07_phase.yaml for the forward direction).
We map the first coding's code back to the CDISC Code via STUDY_PHASE, then
wrap it in an AliasCode — USDM's studyPhase is always an AliasCode, not a
bare Code, even though only standardCode is populated here
(standardCodeAliases stays empty — no non-CDISC alias data on the FHIR side).
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import STUDY_PHASE


class _Coding(TypedDict, total=False):
    code: str | None


class _CodeableConcept(TypedDict, total=False):
    coding: list[_Coding] | None


class PhaseBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.studyPhase"

    def get_priority(self) -> int:
        return 51

    def build(self, context: UsdmBuildContext) -> dict | None:
        phase: _CodeableConcept = context.fhir.get("phase") or {}
        coding = phase.get("coding") or []
        code = coding[0].get("code") if coding and isinstance(coding[0], dict) else None

        standard_code = context.lookup_code(STUDY_PHASE, code) if code else None
        if standard_code is None:
            return None

        return {
            "id": context.next_id("AliasCode"),
            "extensionAttributes": [],
            "standardCode": standard_code,
            "standardCodeAliases": [],
            "instanceType": "AliasCode",
        }