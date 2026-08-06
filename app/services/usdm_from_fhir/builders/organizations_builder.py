"""
OrganizationsBuilder — ResearchStudy.identifier + associatedParty → USDM organizations array.

Priority 10 (runs first) so IdentifiersBuilder (priority 20) can look up
organizations by name from the context bag.

Creates all organizations and stores a name → org_id index at
'version._orgsByName' for other builders to consume.

Sources (both are merged, deduplication by org name):
  1. identifier[].assigner / system   — as before (fallback when no associatedParty)
  2. associatedParty[party.type=Location] + contained[Location]
       — mirrors the INVERSE of readi_core's ResearchAssociatedPartyBuilder
         (lead-sponsor / collaborator with a Location reference) +
         ResearchContainedBuilder.buildLocations() (address / position).
       — classifier[0].text carries the sponsor subtype (OTHER/INDUSTRY/FED/NIH)
         which maps to an Organization.type Code via codes.ORG_TYPE_BY_SPONSOR_SUBTYPE,
         matching SponsorsMappedTypes::getStudyTypeMapping() in readi_core.
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir import codes
from app.services.usdm_from_fhir.codes import CDISC_CODE_SYSTEM

CT_GOV_SYSTEM = "http://terminology.hl7.org/NamingSystem/ClinicalTrials-Gov"

# FHIR party types that carry a contained Location reference.
# Only these two are built by readi_core's ResearchAssociatedPartyBuilder.
_LOCATION_PARTY_TYPE = "Location"


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
        organizations: list[dict] = []
        # dict[str, str] — name → org_id, used by IdentifiersBuilder to set scopeId
        by_name: dict[str, str] = {}

        # ── 1. associatedParty[party.type=Location] + contained[Location] ──────
        # Mirrors the INVERSE of readi_core ResearchAssociatedPartyBuilder (sponsors
        # with a Location reference) + ResearchContainedBuilder.buildLocations().
        contained_locations = _build_location_index(context.fhir.get("contained") or [])
        for party_entry in context.fhir.get("associatedParty") or []:
            party_ref: dict = party_entry.get("party") or {}
            if party_ref.get("type") != _LOCATION_PARTY_TYPE:
                continue

            # Resolve the contained Location by stripping the leading '#'
            ref_str: str = party_ref.get("reference") or ""
            loc_id = ref_str.lstrip("#")
            location: dict = contained_locations.get(loc_id) or {}

            # Prefer the Location's title (canonical org name); fall back to
            # associatedParty.name (may be a person name for individual sponsors)
            org_name: str | None = location.get("title") or party_entry.get("name")
            if not org_name or org_name in by_name:
                continue

            # Resolve type from classifier[0].text (upper-cased sponsor subtype)
            classifier_list: list = party_entry.get("classifier") or []
            subtype: str = ((classifier_list[0] if classifier_list else {}).get("text") or "").upper()
            type_code: dict = codes.ORG_TYPE_BY_SPONSOR_SUBTYPE.get(subtype, codes.ORG_TYPE_UNKNOWN)

            # Resolve address from the contained Location
            raw_address: dict | list = location.get("address") or {}
            # Guard: readi_core may serialize an empty address as []
            if isinstance(raw_address, list):
                raw_address = {}
            city        = raw_address.get("city") or ""
            state       = raw_address.get("state") or ""
            country     = raw_address.get("country") or ""
            postal_code = raw_address.get("postalCode") or ""

            org_id = f"Organization_{len(organizations)}"
            org = _make_org(
                org_id=org_id,
                label=org_name,
                name=org_name.upper(),
                type_code=type_code,
                city=city,
                state=state,
                country=country,
                postal_code=postal_code,
            )
            organizations.append(org)
            by_name[org_name] = org_id

        # ── 2. identifier[].assigner / system  (legacy / fallback) ─────────────
        # Keeps backward compatibility when associatedParty is absent (e.g. the
        # NCT01750580 test file which has no associatedParty array).
        identifiers: list[_Identifier] = context.fhir.get("identifier") or []
        for identifier in identifiers:
            display: str | None = (identifier.get("assigner") or {}).get("display")
            system: str | None = identifier.get("system")

            if display and display not in by_name:
                org_id = f"Organization_{len(organizations)}"
                org = _make_org(
                    org_id=org_id,
                    label=display,
                    name=display.upper(),
                    type_code=codes.ORG_TYPE_UNKNOWN,
                )
                organizations.append(org)
                by_name[display] = org_id

            elif system == CT_GOV_SYSTEM and "ClinicalTrials.gov" not in by_name:
                org_id = f"Organization_{len(organizations)}"
                org = _make_ct_gov_org(org_id=org_id)
                organizations.append(org)
                by_name["ClinicalTrials.gov"] = org_id

        # Store name → org_id index for IdentifiersBuilder (and future builders)
        context.set("version._orgsByName", by_name)
        return organizations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_location_index(contained: list) -> dict[str, dict]:
    """Return a dict mapping contained Location.id → location resource dict."""
    return {
        item["id"]: item
        for item in contained
        if isinstance(item, dict) and item.get("resourceType") == "Location" and item.get("id")
    }


def _make_org(
    org_id: str,
    label: str,
    name: str,
    type_code: dict,
    city: str = "",
    state: str = "",
    country: str = "",
    postal_code: str = "",
) -> dict:
    type_id = f"{org_id}_Type"
    address_id = f"{org_id}_Address"

    # Build the legalAddress text from available address fragments
    parts = [p for p in [city, state, postal_code, country] if p]
    address_text = ", ".join(parts)

    return {
        "id": org_id,
        "extensionAttributes": [],
        "name": name,
        "label": label,
        "type": {
            "id": type_id,
            "code": type_code["code"],
            "decode": type_code["decode"],
            **CDISC_CODE_SYSTEM,
            "instanceType": "Code",
        },
        "legalAddress": {
            "id": address_id,
            "text": address_text,
            "lines": [],
            "city": city,
            "state": state,
            "postalCode": postal_code,
            "instanceType": "Address",
        },
        "identifier": "Unknown",
        "identifierScheme": "Unknown",
        "managedSites": [],
        "instanceType": "Organization",
    }


def _make_ct_gov_org(org_id: str) -> dict:
    org = _make_org(
        org_id,
        label="ClinicalTrials.gov",
        name="CLINICALTRIALS.GOV",
        type_code={"code": "C93453", "decode": "Clinical Study Registry"},
    )
    # Known physical address for ClinicalTrials.gov (NLM/NIH) —
    # mirrors AddressUsdmModel in StudyInterventionsSectionBuilder.php
    org["legalAddress"]["text"] = "8600 Rockville Pike, Bethesda, MD 20894"
    org["legalAddress"]["city"] = "Rockville Pike"
    org["legalAddress"]["state"] = "Bethesda"
    org["legalAddress"]["postalCode"] = "20894"
    return org
