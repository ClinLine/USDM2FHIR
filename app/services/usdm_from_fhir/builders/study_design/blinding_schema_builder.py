"""
BlindingSchemaBuilder — StudyVersion.roles (masking, built by MaskingRolesBuilder)
→ USDM StudyDesign.blindingSchema (AliasCode wrapping a standardCode Code).

Priority 56 — runs right after MaskingRolesBuilder (55) and reuses its result
from the context bag ('version.roles') instead of re-scanning
ResearchStudy.studyDesign[] itself; mirrors readi_core, where
StudyDesignsSectionBuilder::buildBlindingSchema() and RolesSectionBuilder both
read the same underlying masking info off the StudyDesign entity.

FHIR has no explicit "blinding level" field (NONE/SINGLE/DOUBLE/TRIPLE) — only
per-role masking codings (or an open-label text marker). We reconstruct the
level from how many roles MaskingRolesBuilder produced with isMasked=true:
  - roles == [] (no masking data at all)         -> no blindingSchema
  - roles all isMasked=false (open-label roles)  -> "NONE" (OPEN LABEL)
  - 1/2/3 roles with isMasked=true                -> SINGLE/DOUBLE/TRIPLE BLIND
  - 4 roles with isMasked=true (QUADRUPLE)        -> no blindingSchema (see
    codes.BLINDING_SCHEMA_BY_MASKED_COUNT — readi_core's
    getBlindingSchemaMapping() has no QUADRUPLE case either)
"""

from __future__ import annotations

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import BLINDING_SCHEMA_BY_MASKED_COUNT


class BlindingSchemaBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.blindingSchema"

    def get_priority(self) -> int:
        return 56

    def build(self, context: UsdmBuildContext) -> dict | None:
        roles: list[dict] = context.get("version.roles") or []
        if not roles:
            return None

        masked_count = sum(1 for role in roles if (role.get("masking") or {}).get("isMasked"))
        entry = BLINDING_SCHEMA_BY_MASKED_COUNT.get(masked_count)
        if entry is None:
            return None

        return {
            "id": context.next_id("AliasCode"),
            "extensionAttributes": [],
            "standardCode": context.make_code(entry["code"], entry["decode"]),
            "standardCodeAliases": [],
            "instanceType": "AliasCode",
        }