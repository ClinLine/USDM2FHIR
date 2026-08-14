"""
ContraIndicationsBuilder — FHIR contained eligibility Group → intermediate
contra-indication dicts stored at version.studyDesign.contraIndications.

Priority 35 (exclusion side) — mirrors readi_core ContraIndicationsSectionBuilder.php.

Scans the same characteristic[] entries as IndicationsBuilder but keeps only
those with exclude=*true*.  The result is a plain list of dicts (not full USDM
objects) that service.py's _assemble_study_design() converts into the
extensionAttributes[] structure on the StudyDesign.

Dict shape stored in the context bag:
{
    "name":  "<valueCodeableConcept.coding[0].display>",
    "label": "<characteristic.description>",
    "code":  <USDM Code dict | None>,
}

The final USDM extensionAttributes shape is built in service.py following
StudyDesignsSectionBuilder::buildAttributesFrom() from readi_core:

StudyDesign.extensionAttributes[] →
  ExtensionAttribute_N
    └─ ValueExtensionClass  (ExtensionClass_ContraIndic_N)
         ├─ ClassExtId_N      valueId   "ContraIndication_N"
         ├─ ClassExtName_N    valueString  <name>
         ├─ ClassExtLabel_N   valueString  <label>
         └─ ClassExtCode_N    valueCode    <Code>
"""

from __future__ import annotations

from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.builders.study_design.base_indications_builder import (
    AbstractIndicationsBuilder,
)


class ContraIndicationsBuilder(AbstractIndicationsBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.contraIndications"

    def get_priority(self) -> int:
        return 35

    def is_contra_indication(self) -> bool:
        return True

    def build(self, context: UsdmBuildContext) -> list:
        condition_chars = self._collect_condition_chars(context.fhir)
        contra_indications: list[dict] = []
        counter = 0

        for ch in condition_chars:
            if not ch.get("exclude", False):
                continue  # skip inclusion criteria

            counter += 1
            code = self._build_code(context, ch)
            contra_indications.append({
                "name": f"CIDN_{counter}",
                "label": self._extract_label(ch),
                "code": code,
            })

        return contra_indications

