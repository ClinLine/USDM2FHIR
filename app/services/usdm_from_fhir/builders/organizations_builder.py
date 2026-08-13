"""
OrganizationsBuilder — ResearchStudy.identifier + associatedParty + site[] → USDM organizations array.

Priority 10 (runs first) so IdentifiersBuilder (priority 20) can look up
organizations by name from the context bag.

Creates all organizations and stores a name → org_id index at
'version._orgsByName' for other builders to consume.

Sources (all merged, deduplication by org name):
  1. identifier[].assigner / system   — as before (fallback when no associatedParty)
  2. associatedParty[party.type=Location] + contained[Location]
       — mirrors the INVERSE of readi_core's ResearchAssociatedPartyBuilder
         (lead-sponsor / collaborator with a Location reference) +
         ResearchContainedBuilder.buildLocations() (address / position).
       — classifier[0].text carries the sponsor subtype (OTHER/INDUSTRY/FED/NIH)
         which maps to an Organization.type Code via codes.ORG_TYPE_BY_SPONSOR_SUBTYPE,
         matching SponsorsMappedTypes::getStudyTypeMapping() in readi_core.
  3. site[] + contained[Location]      — study-site organizations, one per entry
       — mirrors the INVERSE of readi_core's
         OrganizationsSectionBuilder::buildLocationOrganizations() (Symfony side)
         + ResearchContainedBuilder::addLocationFromOrganizationSite() (FHIR side).
         Unlike source 2, these Locations carry no associatedParty back-reference
         (confirmed on Input/pilot_FHIR.json: 35 site[] entries, 0 of type Location
         in associatedParty) — each is its own independent organization, named
         "ORG_<n>", typed Academic Institution (name contains "research hospital"
         / "research institute") or Unknown otherwise, and given a single synthetic
         managedSites entry mirroring UsdmBuildContext::buildManagedSites() (label
         "Site One", country resolved name → alpha-3 via codes.resolve_country_alpha3,
         itself ported from CountryType::COUNTRY_ALPHA3_MAP).
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

# Associated-party role codes that represent organizations (no assignedPersons).
# These parties carry only a `name` field (no party.reference), so they need
# to be materialized as top-level organizations here so that AssociatedPartyRolesBuilder
# (priority 57) can resolve their organizationIds via version._orgsByName.
# "sponsor" = co-sponsor (C215669), added alongside lead-sponsor (C70793).
_ORG_ROLE_CODES: frozenset[str] = frozenset({"lead-sponsor", "sponsor", "collaborator"})

# Substrings (case-insensitive) that mark a study-site organization as an
# Academic Institution. Mirrors readi_core's inline heuristic in
# OrganizationsSectionBuilder::buildLocationOrganizations() /
# buildOwnerOrganization() / UsdmBuildContext::createOrganizationObjectFromSponsor().
_ACADEMIC_INSTITUTION_MARKERS = ("research hospital", "research institute")

# Fixed managedSites label — UsdmBuildContext::buildManagedSites() is always
# called with its default label ('Site One') throughout readi_core, never a
# custom one, so there is nothing in FHIR to reconstruct it from.
_MANAGED_SITE_LABEL = "Site One"


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

        # ── 2. associatedParty plain-name org roles (no party reference) ─────────
        # Handles lead-sponsor, sponsor (co-sponsor), collaborator entries that
        # carry only a `name` field (no party.reference / party.type).
        # These are created here so that AssociatedPartyRolesBuilder can resolve
        # their org IDs from version._orgsByName (MaskingRolesBuilder also uses
        # the lead-sponsor org ID for masking roles).
        for party_entry in context.fhir.get("associatedParty") or []:
            party_ref: dict = party_entry.get("party") or {}
            # Skip entries with any kind of party reference (handled by source 1 or
            # by AssociatedPartyRolesBuilder via the contained resource).
            if party_ref.get("reference") or party_ref.get("type") or party_ref.get("display"):
                continue

            # Only create organizations for the three org-type roles.
            fhir_role_code = _extract_party_role_code(party_entry)
            if fhir_role_code not in _ORG_ROLE_CODES:
                continue

            org_name: str | None = party_entry.get("name")
            if not org_name or org_name in by_name:
                continue

            # Subtype classifier (if present) drives the Organization.type code.
            classifier_list: list = party_entry.get("classifier") or []
            subtype: str = ((classifier_list[0] if classifier_list else {}).get("text") or "").upper()
            type_code: dict = codes.ORG_TYPE_BY_SPONSOR_SUBTYPE.get(subtype, codes.ORG_TYPE_UNKNOWN)

            org_id = f"Organization_{len(organizations)}"
            org = _make_org(
                org_id=org_id,
                label=org_name,
                name=org_name.upper(),
                type_code=type_code,
            )
            organizations.append(org)
            by_name[org_name] = org_id

        # ── 3. identifier[].assigner / system  (legacy / fallback) ─────────────
        # Keeps backward compatibility when associatedParty is absent (e.g. the
        # NCT01750580 test file which has no associatedParty array).
        identifiers: list[_Identifier] = context.fhir.get("identifier") or []
        for identifier in identifiers:
            display: str | None = (identifier.get("assigner") or {}).get("display")
            system: str | None = identifier.get("system")

            # ClinicalTrials.gov must use _make_ct_gov_org (carries the NLM address)
            # regardless of whether assigner.display is also set.
            if system == CT_GOV_SYSTEM and "ClinicalTrials.gov" not in by_name:
                org_id = f"Organization_{len(organizations)}"
                org = _make_ct_gov_org(org_id=org_id)
                organizations.append(org)
                by_name["ClinicalTrials.gov"] = org_id

            elif display and display not in by_name:
                org_id = f"Organization_{len(organizations)}"
                org = _make_org(
                    org_id=org_id,
                    label=display,
                    name=display.upper(),
                    type_code=codes.ORG_TYPE_UNKNOWN,
                )
                organizations.append(org)
                by_name[display] = org_id

        # ── 4. site[] + contained[Location]  (study-site organizations) ────────
        # Mirrors the INVERSE of readi_core OrganizationsSectionBuilder::
        # buildLocationOrganizations(). Independent of source 2 above — these
        # Locations aren't referenced from associatedParty.
        for site_entry in context.fhir.get("site") or []:
            if site_entry.get("type") != _LOCATION_PARTY_TYPE:
                continue

            ref_str: str = site_entry.get("reference") or ""
            loc_id = ref_str.lstrip("#")
            location: dict = contained_locations.get(loc_id) or {}

            site_name: str | None = location.get("name")
            if not site_name or site_name in by_name:
                continue

            raw_address: dict | list = location.get("address") or {}
            if isinstance(raw_address, list):
                raw_address = {}
            city        = raw_address.get("city") or ""
            state       = raw_address.get("state") or ""
            country     = raw_address.get("country") or ""
            postal_code = raw_address.get("postalCode") or ""

            site_name_lower = site_name.lower()
            is_academic_institution = any(marker in site_name_lower for marker in _ACADEMIC_INSTITUTION_MARKERS)
            type_code = codes.ORG_TYPE_ACADEMIC_INSTITUTION if is_academic_institution else codes.ORG_TYPE_BY_SPONSOR_SUBTYPE["OTHER"]

            org_id = f"Organization_{len(organizations)}"
            org = _make_org(
                org_id=org_id,
                label=site_name,
                name=f"ORG_{len(organizations)}",
                type_code=type_code,
                city=city,
                state=state,
                country=country,
                postal_code=postal_code,
            )
            org["managedSites"] = _build_managed_sites(context, country)
            organizations.append(org)
            by_name[site_name] = org_id

        # Store name → org_id index for IdentifiersBuilder (and future builders)
        context.set("version._orgsByName", by_name)
        return organizations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_party_role_code(party: dict) -> str | None:
    """Return the first role coding code from an associatedParty entry, or None."""
    role = party.get("role") or {}
    for coding in role.get("coding") or []:
        code = coding.get("code") if isinstance(coding, dict) else None
        if code:
            return code
    return None


def _build_location_index(contained: list) -> dict[str, dict]:
    """Return a dict mapping contained Location.id → location resource dict."""
    return {
        item["id"]: item
        for item in contained
        if isinstance(item, dict) and item.get("resourceType") == "Location" and item.get("id")
    }


def _build_managed_sites(context: UsdmBuildContext, country_name: str) -> list[dict]:
    """
    Single synthetic managedSites entry mirroring UsdmBuildContext::buildManagedSites().
    Skips (returns []) when the country is absent or doesn't resolve to an
    alpha-3 code — matches buildManagedSites()'s own early-return behaviour
    rather than emitting a managedSite with a guessed/blank country.
    """
    alpha3 = codes.resolve_country_alpha3(country_name)
    if alpha3 is None:
        return []

    counter = context.next_attr_counter()
    return [{
        "id": f"ManagedSite_{counter}",
        "name": f"MS{counter}",
        "label": _MANAGED_SITE_LABEL,
        "country": context.make_code(alpha3, country_name),
        "instanceType": "StudySite",
    }]


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

    # Build the legalAddress text from available address fragments;
    # fall back to the org label so the address is never fully blank.
    parts = [p for p in [city, state, postal_code, country] if p]
    address_text = ", ".join(parts) if parts else label

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
