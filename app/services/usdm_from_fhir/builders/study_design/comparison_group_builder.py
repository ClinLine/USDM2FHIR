"""
ComparisonGroupBuilder — ResearchStudy.comparisonGroup[] → USDM StudyDesign.arms.

Priority 60 — independent of the studyDesign.* builders above it; only reads
'comparisonGroup' and 'contained' off the root FHIR resource.

Each FHIR comparisonGroup maps to one USDM StudyArm. comparisonGroup.name is
the human-readable label (USDM 'label'); comparisonGroup.description carries
over as-is. The arm's type Code is not on comparisonGroup itself — it has to
be resolved through comparisonGroup.eligibility.reference (a local '#...'
reference) into the matching contained Group resource, whose code.text (e.g.
"Experimental") is looked up in ARM_TYPE. dataOriginDescription/dataOriginType
are fixed per readi_core's ArmsSectionBuilder (every arm is study-generated
data). populationIds is left empty — no population/cohort builder exists yet
(see todo/plan_fhir_to_usdm.md Faza B) so there is nothing to reference.
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import (
    ARM_TYPE,
    DATA_ORIGIN_TYPE_WITHIN_STUDY,
    DATA_ORIGIN_DESCRIPTION_WITHIN_STUDY,
)


class _Eligibility(TypedDict, total=False):
    reference: str | None


class _ComparisonGroup(TypedDict, total=False):
    name: str | None
    description: str | None
    eligibility: _Eligibility | None


class _CodeableConcept(TypedDict, total=False):
    text: str | None


class _Group(TypedDict, total=False):
    id: str | None
    code: _CodeableConcept | None


class ComparisonGroupBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.arms"

    def get_priority(self) -> int:
        return 60

    def build(self, context: UsdmBuildContext) -> list:
        comparison_groups: list[_ComparisonGroup] = context.fhir.get("comparisonGroup") or []
        groups_by_id = self._index_contained_groups(context.fhir.get("contained") or [])

        arms: list[dict] = []
        for i, cg in enumerate(comparison_groups):
            arm_id = f"StudyArm_{i}"

            arm_type = self._resolve_type(context, cg, groups_by_id)

            arm: dict = {
                "id": arm_id,
                "extensionAttributes": [],
                "name": arm_id.upper(),
                "label": cg.get("name") or "",
                "description": cg.get("description"),
            }
            if arm_type is not None:
                arm["type"] = arm_type
            arm["dataOriginDescription"] = DATA_ORIGIN_DESCRIPTION_WITHIN_STUDY
            arm["dataOriginType"] = context.make_code(
                DATA_ORIGIN_TYPE_WITHIN_STUDY["code"], DATA_ORIGIN_TYPE_WITHIN_STUDY["decode"]
            )
            arm["populationIds"] = []
            arm["notes"] = []
            arm["instanceType"] = "StudyArm"

            arms.append(arm)

        return arms

    # -------------------------------------------------------------------------

    @staticmethod
    def _index_contained_groups(contained: list[dict]) -> dict[str, _Group]:
        return {
            entry["id"]: entry
            for entry in contained
            if isinstance(entry, dict) and entry.get("resourceType") == "Group" and entry.get("id")
        }

    @staticmethod
    def _resolve_type(
        context: UsdmBuildContext,
        cg: _ComparisonGroup,
        groups_by_id: dict[str, _Group],
    ) -> dict | None:
        reference: str | None = (cg.get("eligibility") or {}).get("reference")
        if not reference or not reference.startswith("#"):
            return None

        group = groups_by_id.get(reference[1:])
        if group is None:
            return None

        code_text: str | None = (group.get("code") or {}).get("text")
        if not code_text:
            return None

        return context.lookup_code(ARM_TYPE, code_text)