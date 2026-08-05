"""
AssociatedPartyRolesBuilder — ResearchStudy.associatedParty[] → USDM StudyVersion.roles
(responsible-party StudyRole entries).

Priority 57 — runs after MaskingRolesBuilder (55) and EXTENDS the 'version.roles'
list already written by that builder; returns the combined list.

FHIR → USDM mapping per role entry:
  associatedParty[].role.coding[].code        → role.code      (lookup ASSOCIATED_PARTY_ROLE)
  associatedParty[].name                      → role.label     (fallback when no contained org)

When associatedParty[].party.reference starts with '#':
  Look up the contained resource by id:
    PractitionerRole:
      PractitionerRole.organization.display   → role.label
      PractitionerRole.practitioner.display   → assignedPersons[0].text / personName.text
      PractitionerRole.code[0].text           → assignedPersons[0].jobTitle
    Practitioner:
      Practitioner.name[0].text               → assignedPersons[0].text / personName.text
      associatedParty[].name                  → role.label  (no org in plain Practitioner)

When party.display present (no '#' reference):
  associatedParty[].name  → role.label
  party.display           → assignedPersons[0].text (if different from name)

When no party:
  associatedParty[].name  → role.label
  assignedPersons = []
"""

from __future__ import annotations

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import (
    ASSOCIATED_PARTY_ROLE,
    ORG_TYPE_UNKNOWN,
)


class AssociatedPartyRolesBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.roles"

    def get_priority(self) -> int:
        return 57

    # -------------------------------------------------------------------------

    def build(self, context: UsdmBuildContext) -> list:
        # Start from whatever MaskingRolesBuilder already put in the bag.
        existing: list = list(context.get("version.roles") or [])

        # Build a quick lookup: contained resource id → resource dict
        contained_by_id: dict[str, dict] = {
            c["id"]: c
            for c in (
                list(context.fhir.get("contained") or [])
                + list(context.bundle_entries)
            )
            if isinstance(c, dict) and c.get("id")
        }

        new_roles: list[dict] = []
        for party in context.fhir.get("associatedParty") or []:
            role = self._build_role(context, party, contained_by_id)
            if role is not None:
                new_roles.append(role)

        return existing + new_roles

    # -------------------------------------------------------------------------

    def _build_role(
        self,
        ctx: UsdmBuildContext,
        party: dict,
        contained_by_id: dict[str, dict],
    ) -> dict | None:
        # --- resolve role code -----------------------------------------------
        fhir_role_code = self._extract_role_code(party)
        if fhir_role_code is None:
            return None

        code_obj = ctx.lookup_code(ASSOCIATED_PARTY_ROLE, fhir_role_code)
        if code_obj is None:
            # Unknown role code — skip rather than emit garbage
            return None

        # --- resolve contained resource (PractitionerRole / Practitioner) ----
        contained = self._resolve_contained(party, contained_by_id)

        # --- derive label + assignedPersons ----------------------------------
        label, assigned_persons = self._extract_label_and_persons(
            ctx, party, contained
        )

        # --- assemble StudyRole ----------------------------------------------
        role_id = ctx.next_id("StudyRole")
        return {
            "id": role_id,
            "extensionAttributes": [],
            "name": role_id.upper(),
            "label": label,
            "description": "",
            "code": code_obj,
            "appliesToIds": ["StudyVersion_0"],
            "assignedPersons": assigned_persons,
            "organizationIds": [],
            "masking": None,
            "notes": [],
            "instanceType": "StudyRole",
        }

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_role_code(party: dict) -> str | None:
        """Return the first code from associatedParty.role.coding[], or None."""
        role = party.get("role") or {}
        for coding in role.get("coding") or []:
            code = coding.get("code") if isinstance(coding, dict) else None
            if code:
                return code
        return None

    @staticmethod
    def _resolve_contained(
        party: dict, contained_by_id: dict[str, dict]
    ) -> dict | None:
        """
        If party.reference starts with '#', return the matching contained
        resource; otherwise return None.
        """
        ref = (party.get("party") or {}).get("reference", "")
        if isinstance(ref, str) and ref.startswith("#"):
            return contained_by_id.get(ref[1:])
        return None

    def _extract_label_and_persons(
        self,
        ctx: UsdmBuildContext,
        party: dict,
        contained: dict | None,
    ) -> tuple[str, list]:
        """
        Returns (role.label, assignedPersons[]).
        Branches on the type of the resolved contained resource.
        """
        party_name: str = party.get("name") or ""

        if contained is None:
            # No contained reference — try party.display as person name
            party_display = (party.get("party") or {}).get("display")
            if party_display:
                person = self._build_assigned_person(
                    ctx,
                    person_name=party_display,
                    job_title=None,
                    org_name=party_display,
                    org_label=party_name,
                )
                return party_name, [person]
            return party_name, []

        resource_type = contained.get("resourceType")

        if resource_type == "PractitionerRole":
            # Best-quality path: PractitionerRole has org + practitioner + jobTitle
            org_display: str = (contained.get("organization") or {}).get("display") or party_name
            pract_display: str = (contained.get("practitioner") or {}).get("display") or party_name
            job_title: str | None = None
            codes: list = contained.get("code") or []
            if codes and isinstance(codes[0], dict):
                job_title = codes[0].get("text")

            person = self._build_assigned_person(
                ctx,
                person_name=pract_display,
                job_title=job_title,
                org_name=pract_display,
                org_label=org_display,
            )
            return org_display, [person]

        if resource_type == "Practitioner":
            # Practitioner: name[0].text only
            names: list = contained.get("name") or []
            pract_name = (names[0].get("text") if names and isinstance(names[0], dict) else None) or party_name
            person = self._build_assigned_person(
                ctx,
                person_name=pract_name,
                job_title=None,
                org_name=pract_name,
                org_label=party_name,
            )
            return party_name, [person]

        # Unknown contained type — fall back to name only
        return party_name, []

    def _build_assigned_person(
        self,
        ctx: UsdmBuildContext,
        *,
        person_name: str,
        job_title: str | None,
        org_name: str,
        org_label: str,
    ) -> dict:
        person_id = ctx.next_id("AssignedPerson")
        person_name_id = ctx.next_id("PersonName")
        org_id = ctx.next_id("Organization")
        addr_id = ctx.next_id("Address")

        org = {
            "isSecondaryIdInfos": True,
            "identifiers": [],
            "id": org_id,
            "extensionAttributes": [],
            "name": org_name,
            "label": org_label,
            "type": ctx.make_code(
                ORG_TYPE_UNKNOWN["code"], ORG_TYPE_UNKNOWN["decode"]
            ),
            "legalAddress": {
                "id": addr_id,
                "text": "",
                "lines": [],
                "city": "",
                "state": "",
                "postalCode": "",
                "instanceType": "Address",
            },
            "identifier": "Unknown",
            "identifierScheme": "Unknown",
            "managedSites": [],
            "instanceType": "Organization",
        }

        person_name_obj = {
            "id": person_name_id,
            "extensionAttributes": [],
            "text": person_name,
            "familyName": "",
            "givenNames": [],
            "prefixes": [""],
            "suffixes": [""],
            "instanceType": "PersonName",
        }

        entry: dict = {
            "id": person_id,
            "extensionAttributes": [],
            "name": f"AP_{person_id}",
            "text": person_name,
            "organization": org,
            "personName": person_name_obj,
            "instanceType": "AssignedPerson",
        }

        entry["jobTitle"] = job_title if job_title is not None else ""

        return entry

