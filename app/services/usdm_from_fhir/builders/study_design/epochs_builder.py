"""
EpochsBuilder — fixed default StudyEpoch scaffold (Screening -> Treatment).

Priority 61 — runs after ComparisonGroupBuilder (60). No FHIR field drives
this; it mirrors readi_core ArmsSectionBuilder.php, which always builds the
same two hardcoded epochs alongside arms/studyCells (not derived from any
source data). Only built when there is at least one arm — epochs are
meaningless without a StudyArm to place a StudyCell in.

StudyCellsBuilder (priority 62) references these epoch ids by the same fixed
literals independently, rather than reading them back from the context bag —
the same way readi_core's ComparisonGroupBuilder/ResearchContainedBuilder keep
their generated ids in sync without reading each other's output.
"""

from __future__ import annotations

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext

SCREENING_EPOCH_ID = "StudyEpoch_1"
TREATMENT_EPOCH_ID = "StudyEpoch_2"


class EpochsBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.epochs"

    def get_priority(self) -> int:
        return 61

    def build(self, context: UsdmBuildContext) -> list:
        arms: list = context.get("version.studyDesign.arms") or []
        if not arms:
            return []

        return [
            {
                "id": SCREENING_EPOCH_ID,
                "extensionAttributes": [],
                "name": "Screening",
                "label": "Screening",
                "description": "Screening Epoch",
                "type": context.make_code("C202487", "Screening Epoch"),
                "previousId": None,
                "nextId": TREATMENT_EPOCH_ID,
                "notes": [],
                "instanceType": "StudyEpoch",
            },
            {
                "id": TREATMENT_EPOCH_ID,
                "extensionAttributes": [],
                "name": "Treatment",
                "label": "Treatment",
                "description": "Treatment Epoch",
                "type": context.make_code("C101526", "Treatment Epoch"),
                "previousId": SCREENING_EPOCH_ID,
                "nextId": None,
                "notes": [],
                "instanceType": "StudyEpoch",
            },
        ]