"""
StudyCellsBuilder — per-arm StudyCell (Screening + Treatment), mirroring
readi_core ArmsSectionBuilder.php's `foreach ($arms as $arm) { ...new
StudyCellUsdmModel... }` loop: a screening cell pointing at one shared
screening StudyElement, and a treatment cell pointing at a per-arm treatment
StudyElement.

Priority 63 — runs after ComparisonGroupBuilder (60, produces the arm list at
'version.studyDesign.arms'), EpochsBuilder (61, defines the fixed epoch id
literals) and ElementsBuilder (62, defines the fixed element id literals) —
this builder points at both sets of ids independently rather than reading
them back from the context bag, the same way readi_core's
ComparisonGroupBuilder/ResearchContainedBuilder keep their generated ids in
sync without reading each other's output.
"""

from __future__ import annotations

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.builders.studyDesign.epochs_builder import SCREENING_EPOCH_ID, TREATMENT_EPOCH_ID
from app.services.usdm_from_fhir.builders.studyDesign.elements_builder import SCREENING_ELEMENT_ID


class StudyCellsBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.studyCells"

    def get_priority(self) -> int:
        return 63

    def build(self, context: UsdmBuildContext) -> list:
        arms: list[dict] = context.get("version.studyDesign.arms") or []
        if not arms:
            return []

        study_cells: list[dict] = []
        cell_index = 1

        for arm in arms:
            arm_id: str = arm["id"]
            treatment_element_id = f"StudyElement_{arm_id}"

            study_cells.append(self._build_cell(cell_index, arm_id, SCREENING_EPOCH_ID, [SCREENING_ELEMENT_ID]))
            cell_index += 1
            study_cells.append(self._build_cell(cell_index, arm_id, TREATMENT_EPOCH_ID, [treatment_element_id]))
            cell_index += 1

        return study_cells

    # -------------------------------------------------------------------------

    @staticmethod
    def _build_cell(index: int, arm_id: str, epoch_id: str, element_ids: list[str]) -> dict:
        return {
            "id": f"StudyCell_{index}",
            "extensionAttributes": [],
            "armId": arm_id,
            "epochId": epoch_id,
            "elementIds": element_ids,
            "instanceType": "StudyCell",
        }