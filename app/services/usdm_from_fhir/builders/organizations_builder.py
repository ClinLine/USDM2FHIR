"""
OrganizationsBuilder — ResearchStudy.identifier → USDM organizations array.

Priority 10 (runs first) so IdentifiersBuilder (priority 20) can look up
organizations by name from the context bag.

Creates all organizations and stores a name → org_id index at
'version._orgsByName' for other builders to consume.

In the future, other sources (sites, roles, …) can be added here
without touching any other builder.
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import CDISC_CODE_SYSTEM

CT_GOV_SYSTEM = "http://terminology.hl7.org/NamingSystem/ClinicalTrials-Gov"


class _Assigner(TypedDict, total=False):
    display: str | None


class _Identifier(TypedDict, total=False):
    system: str | None
    value: str | None
    assigner: _Assigner | None


class OrganizationsBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.organizations"

    def get_priority(self) -> int:
        return 10  # runs first — IdentifiersBuilder (priority 20) reads the index

    def build(self, context: UsdmBuildContext) -> list:
        # list[_Identifier] — source for org names/systems
        identifiers: list[_Identifier] = context.fhir.get("identifier") or []

        organizations: list[dict] = []
        # dict[str, str] — name → org_id, used by IdentifiersBuilder to set scopeId
        by_name: dict[str, str] = {}

        for identifier in identifiers:
            display: str | None = (identifier.get("assigner") or {}).get("display")
            system: str | None = identifier.get("system")

            if display and display not in by_name:
                org = _make_org(
                    org_id=f"Organization_{len(organizations)}",
                    label=display,
                    name=display.upper(),
                    code="C17998", decode="Unknown",
                )
                organizations.append(org)
                by_name[display] = org["id"]

            elif system == CT_GOV_SYSTEM and "ClinicalTrials.gov" not in by_name:
                org = _make_ct_gov_org(org_id=f"Organization_{len(organizations)}")
                organizations.append(org)
                by_name["ClinicalTrials.gov"] = org["id"]

        # Store name → org_id index for IdentifiersBuilder (and future builders)
        context.set("version._orgsByName", by_name)
        return organizations


# ---------------------------------------------------------------------------
# Org factory helpers
# ---------------------------------------------------------------------------

def _make_org(org_id: str, label: str, name: str, code: str, decode: str) -> dict:
    type_id = f"{org_id}_Type"
    return {
        "id": org_id,
        "name": name,
        "label": label,
        "type": {
            "id": type_id,
            "name": type_id.upper(),
            "code": code,
            "decode": decode,
            **CDISC_CODE_SYSTEM,
            "instanceType": "Code",
        },
        "instanceType": "Organization",
    }


def _make_ct_gov_org(org_id: str) -> dict:
    address_id = f"{org_id}_Address"
    org = _make_org(
        org_id, label="ClinicalTrials.gov", name="ClinicalTrials.gov",
        code="C93453", decode="Clinical Study Registry",
    )
    org.update({
        "legalAddress": {
            "id": address_id,
            "name": address_id.upper(),
            "text": "   ",
            "lines": [],
            "city": "",
            "state": "",
            "postalCode": "",
            "instanceType": "Address",
        },
        "extensionAttributes": [],
        "identifier": "Unknown",
        "identifierScheme": "Unknown",
        "managedSites": [],
    })
    return org
