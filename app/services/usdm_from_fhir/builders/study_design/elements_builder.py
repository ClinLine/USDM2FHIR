"""
ElementsBuilder — per-arm StudyElement scaffold: one shared screening element
plus one treatment element per arm, mirroring readi_core ArmsSectionBuilder.php's
hardcoded StudyElementUsdmModel construction.

Priority 62 — runs after ComparisonGroupBuilder (60, produces the arm list at
'version.studyDesign.arms'). Only built when there is at least one arm.

StudyCellsBuilder (priority 63) references these element ids by the same
fixed literal / naming scheme independently, rather than reading them back
from the context bag — the same pattern EpochsBuilder/StudyCellsBuilder use
for the epoch ids.
"""

from __future__ import annotations

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext

SCREENING_ELEMENT_ID = "StudyElement_Screening"


class ElementsBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.elements"

    def get_priority(self) -> int:
        return 62

    def build(self, context: UsdmBuildContext) -> list:
        arms: list[dict] = context.get("version.studyDesign.arms") or []
        if not arms:
            return []

        elements = [self._build_element(SCREENING_ELEMENT_ID, f"SE_{SCREENING_ELEMENT_ID}")]
        for arm in arms:
            element_id = f"StudyElement_{arm['id']}"
            elements.append(self._build_element(element_id, f"SE_{element_id}"))

        return elements

    # -------------------------------------------------------------------------

    @staticmethod
    def _build_element(element_id: str, name: str) -> dict:
        return {
            "id": element_id,
            "extensionAttributes": [],
            "name": name,
            "label": "",
            "description": "",
            "studyInterventionIds": [],
            "notes": [],
            "instanceType": "StudyElement",
        }