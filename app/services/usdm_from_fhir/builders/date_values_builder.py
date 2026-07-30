"""
DateValuesBuilder — ResearchStudy.progressStatus → USDM dateValues array.

Priority 52 — no cross-builder dependencies.

Only the progressStatus entry whose state.coding code is "update-posting" is
converted, into a single GovernanceDate (D_ISSUED) whose dateValue comes from
that entry's period.end. Every other progressStatus entry is out of scope —
see todo/plan_fhir_to_usdm.md.
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import GOVERNANCE_DATE_TYPE, GEOGRAPHIC_SCOPE_GLOBAL

UPDATE_POSTING_CODE = "update-posting"


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

        entry = self._find_update_posting(entries)
        if entry is None:
            return []

        date_value: str | None = (entry.get("period") or {}).get("end")
        if not date_value:
            return []

        type_code = context.lookup_code(GOVERNANCE_DATE_TYPE, UPDATE_POSTING_CODE)

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
    def _find_update_posting(entries: list[_ProgressStatus]) -> _ProgressStatus | None:
        for entry in entries:
            coding = (entry.get("state") or {}).get("coding") or []
            first: dict = coding[0] if isinstance(coding, list) and coding else (
                coding if isinstance(coding, dict) else {}
            )
            if isinstance(first, dict) and first.get("code") == UPDATE_POSTING_CODE:
                return entry
        return None