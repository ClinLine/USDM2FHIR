"""
IndicationsBuilder — FHIR contained eligibility Group → USDM StudyDesign.indications.

Priority 34 (inclusion side) — mirrors readi_core IndicationsSectionBuilder.php.

Scans the characteristic[] entries of every contained Group referenced by
"eligibility-criteria" that carry LOINC code 75323-6 ("Condition") and whose
exclude flag is *false*.  Each such characteristic becomes one Indication dict.

USDM shape produced:
{
    "id": "Indication_1",
    "extensionAttributes": [],
    "name": "<valueCodeableConcept.coding[0].display>",
    "label": "<characteristic.description>",
    "codes": [ <Code dict> ],
    "notes": [],
    "instanceType": "Indication"
}
"""

from __future__ import annotations

from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.builders.study_design.base_indications_builder import (
    AbstractIndicationsBuilder,
)


class IndicationsBuilder(AbstractIndicationsBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.indications"

    def get_priority(self) -> int:
        return 34

    def is_contra_indication(self) -> bool:
        return False

    def build(self, context: UsdmBuildContext) -> list:
        condition_chars = self._collect_condition_chars(context.fhir)
        indications: list[dict] = []
        counter = 0

        for ch in condition_chars:
            if ch.get("exclude", False):
                continue  # skip exclusion criteria

            counter += 1
            code = self._build_code(context, ch)
            indication: dict = {
                "id": f"Indication_{counter}",
                "extensionAttributes": [],
                "name": f"IND_{counter}",
                "label": self._extract_label(ch),
                "codes": [code] if code else [],
                "notes": [],
                "instanceType": "Indication",
            }
            indications.append(indication)

        return indications

