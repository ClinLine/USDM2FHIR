"""
MaskingRolesBuilder — ResearchStudy.studyDesign[] (masking SEVCO codes / open-label
text) → USDM StudyVersion.roles (masking-only StudyRole entries).

Priority 55 — independent of the studyDesign.* builders; writes 'version.roles',
a StudyVersion-level field (see readi_core RolesSectionBuilder::getKey() ==
'version.roles'), not a studyDesign sub-section.

FHIR has no positive code for "no masking" — readi_core's masking logic
(StudyDesignMappedTypes::getMaskingMapping / getAllMaskingMapping, consumed by
RolesSectionBuilder::build()) only ever distinguishes two states:
  - masking === NONE  -> all 4 canonical roles, isMasked=false
  - whoMasked[] present -> one role per entry, isMasked=true
On the FHIR side (per HL7 FHIR R5 study-design ValueSet), that maps to:
  - one or more SEVCO:0106x codings present -> isMasked=true roles for those
  - no codings, but a "... Open Label" text entry -> all 4 roles, isMasked=false
  - neither -> no masking data at all -> no roles built (not a guess)
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import MASKING_WHO, MASKING_ALL_ORDER, MASKING_NONE_TEXT_MARKER


class _Coding(TypedDict, total=False):
    code: str | None


class _StudyDesignEntry(TypedDict, total=False):
    coding: list[_Coding] | None
    text: str | None


class MaskingRolesBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.roles"

    def get_priority(self) -> int:
        return 55

    def build(self, context: UsdmBuildContext) -> list:
        entries: list[_StudyDesignEntry] = context.fhir.get("studyDesign") or []

        matched_codes: list[str] = []
        seen: set[str] = set()
        open_label = False

        for entry in entries:
            for coding in entry.get("coding") or []:
                code = coding.get("code") if isinstance(coding, dict) else None
                if code in MASKING_WHO and code not in seen:
                    seen.add(code)
                    matched_codes.append(code)

            text = entry.get("text")
            if isinstance(text, str) and MASKING_NONE_TEXT_MARKER in text.lower():
                open_label = True

        if matched_codes:
            return [self._build_role(context, code, is_masked=True) for code in matched_codes]
        if open_label:
            return [self._build_role(context, code, is_masked=False) for code in MASKING_ALL_ORDER]
        return []

    # -------------------------------------------------------------------------

    @staticmethod
    def _build_role(context: UsdmBuildContext, sevco_code: str, *, is_masked: bool) -> dict:
        entry = MASKING_WHO[sevco_code]
        role_id = context.next_id("StudyRole")
        return {
            "id": role_id,
            "extensionAttributes": [],
            "name": role_id.upper(),
            "label": entry["decode"],
            "description": "",
            "code": context.make_code(entry["code"], entry["decode"]),
            "appliesToIds": ["StudyVersion_0"],
            "assignedPersons": [],
            "organizationIds": [],
            "masking": {
                "id": context.next_id("Masking"),
                "extensionAttributes": [],
                "text": "Masked",
                "isMasked": is_masked,
                "instanceType": "Masking",
            },
            "notes": [],
            "instanceType": "StudyRole",
        }