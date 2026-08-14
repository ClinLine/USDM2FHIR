"""
IdentifiersBuilder — ResearchStudy.identifier → USDM studyIdentifiers array.

Priority 20 — runs after OrganizationsBuilder (priority 10) which creates
the organizations and stores a name → org_id index at 'version._orgsByName'.

Each identifier looks up its issuing organization by name from that index
to obtain the scopeId.
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext

CT_GOV_SYSTEM = "http://terminology.hl7.org/NamingSystem/ClinicalTrials-Gov"


class _Assigner(TypedDict, total=False):
    display: str | None


class _Identifier(TypedDict, total=False):
    system: str | None
    value: str | None
    assigner: _Assigner | None


class IdentifiersBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyIdentifiers"

    def get_priority(self) -> int:
        return 20

    def build(self, context: UsdmBuildContext) -> list:
        # list[_Identifier] — each element is a FHIR Identifier object, e.g.:
        # {
        #   "system": "http://terminology.hl7.org/NamingSystem/ClinicalTrials-Gov",
        #   "value": "NCT12345678",
        #   "assigner": {"display": "ClinicalTrials.gov"}
        # }
        identifiers: list[_Identifier] = context.fhir.get("identifier") or []

        # dict[str, str] — name → org_id, built by OrganizationsBuilder (priority 10)
        # e.g.: {"Eli Lilly": "Organization_0", "ClinicalTrials.gov": "Organization_1"}
        orgs_by_name: dict[str, str] = context.get("version._orgsByName", {})

        result = []
        used_scope_ids: set[str] = set()
        for i, identifier in enumerate(identifiers):
            # str — raw identifier value, e.g.: "NCT12345678"
            value: str = identifier.get("value") or ""

            # str — id of the organization that issued this identifier
            scope_id: str = self._resolve_scope_id(identifier, orgs_by_name)

            # skip if we couldn't resolve the issuing organization
            if not scope_id:
                continue

            # CORE-000956: each organization can appear at most once
            if scope_id in used_scope_ids:
                continue
            used_scope_ids.add(scope_id)

            si_id = f"StudyIdentifier_{i}"
            result.append({
                "id": si_id,
                "text": value,
                "scopeId": scope_id,
                "instanceType": "StudyIdentifier",
            })

        return result

    # -------------------------------------------------------------------------

    @staticmethod
    def _resolve_scope_id(identifier: _Identifier, orgs_by_name: dict[str, str]) -> str:
        """
        Look up the org_id for this identifier by matching its assigner name
        (or ClinicalTrials.gov system) against the index built by OrganizationsBuilder.
        Returns an empty string if no match is found.
        """
        display: str | None = (identifier.get("assigner") or {}).get("display")
        system: str | None = identifier.get("system")

        if display:
            return orgs_by_name.get(display, "")

        if system == CT_GOV_SYSTEM:
            return orgs_by_name.get("ClinicalTrials.gov", "")

        return ""
