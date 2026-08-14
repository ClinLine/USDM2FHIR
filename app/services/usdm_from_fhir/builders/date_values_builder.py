"""
DateValuesBuilder — ResearchStudy.progressStatus → USDM dateValues array.

Priority 52 — no cross-builder dependencies.

Tries first to find a progressStatus entry with code "update-posting" (period.end).
Falls back to "overall-study" with actual=true (period.start) if not found.
See todo/plan_fhir_to_usdm.md.
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import GOVERNANCE_DATE_TYPE, GEOGRAPHIC_SCOPE_GLOBAL

UPDATE_POSTING_CODE = "update-posting"
OVERALL_STUDY_CODE = "overall-study"


class _Coding(TypedDict, total=False):
    code: str | None


class _State(TypedDict, total=False):
    coding: list[_Coding] | None


class _Period(TypedDict, total=False):
    end: str | None


class _ProgressStatus(TypedDict, total=False):
    state: _State | None
    actual: bool | None
    period: _Period | None


class DateValuesBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.dateValues"

    def get_priority(self) -> int:
        return 52

    def build(self, context: UsdmBuildContext) -> list:
        entries: list[_ProgressStatus] = context.fhir.get("progressStatus") or []

        entry = self._find_by_code(entries, UPDATE_POSTING_CODE)
        if entry is not None:
            date_value: str | None = (entry.get("period") or {}).get("end")
            type_code_key = UPDATE_POSTING_CODE
        else:
            entry = self._find_by_code(entries, OVERALL_STUDY_CODE, actual=True)
            if entry is None:
                return []
            date_value = (entry.get("period") or {}).get("start")
            type_code_key = UPDATE_POSTING_CODE  # GovernanceDate type stays the same

        if not date_value:
            return []

        type_code = context.lookup_code(GOVERNANCE_DATE_TYPE, type_code_key)

        governance_date = {
            "id": "GovernanceDate_0",
            "extensionAttributes": [],
            "name": "D_ISSUED",
            "label": "Last update posted (Clinical gov provider)",
            "description": "Design approval date",
            "type": type_code,
            "dateValue": date_value,
            "geographicScopes": [
                {
                    "id": "GeographicScope_0",
                    "extensionAttributes": [],
                    "type": context.make_code(**GEOGRAPHIC_SCOPE_GLOBAL),
                    "code": None,
                    "instanceType": "GeographicScope",
                }
            ],
            "instanceType": "GovernanceDate",
        }

        return [governance_date]

    # -------------------------------------------------------------------------

    @staticmethod
    def _find_by_code(
        entries: list[_ProgressStatus],
        code: str,
        actual: bool | None = None,
    ) -> _ProgressStatus | None:
        for entry in entries:
            coding = (entry.get("state") or {}).get("coding") or []
            first: dict = coding[0] if isinstance(coding, list) and coding else (
                coding if isinstance(coding, dict) else {}
            )
            if not (isinstance(first, dict) and first.get("code") == code):
                continue
            if actual is not None and entry.get("actual") != actual:
                continue
            return entry
        return None