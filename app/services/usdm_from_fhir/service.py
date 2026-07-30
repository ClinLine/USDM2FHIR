"""
FhirToUsdmService — orchestrates all section builders.

Usage:
    service = FhirToUsdmService()
    usdm_dict = service.build(fhir_data)

Adding a new builder:
    1. Create app/services/usdm_from_fhir/builders/my_builder.py
    2. Implement AbstractSectionBuilder
    3. Register it in _BUILDERS below — that's it.
"""

from __future__ import annotations

from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.builders.organizations_builder import OrganizationsBuilder
from app.services.usdm_from_fhir.builders.identifiers_builder import IdentifiersBuilder
from app.services.usdm_from_fhir.builders.titles_builder import TitlesBuilder
from app.services.usdm_from_fhir.builders.objectives_builder import ObjectivesBuilder
from app.services.usdm_from_fhir.builders.study_design_type_builder import StudyDesignTypeBuilder
from app.services.usdm_from_fhir.builders.purpose_type_builder import PurposeTypeBuilder
from app.services.usdm_from_fhir.builders.date_values_builder import DateValuesBuilder

# ---------------------------------------------------------------------------
# Default empty fields appended to every StudyVersion (instanceType last).
# ---------------------------------------------------------------------------
_VERSION_EMPTY_FIELDS: list[str] = [
    "documentVersionIds",
    "amendments",
    "businessTherapeuticAreas",
    "referenceIdentifiers",
    "narrativeContentItems",
    "abbreviations",
    "administrableProducts",
    "medicalDevices",
    "productOrganizationRoles",
    "bcSurrogates",
    "conditions",
    "notes",
]


class FhirToUsdmService:
    """
    Collects all registered builders, runs them in priority order and assembles
    the final USDM document dict.
    """

    # Register builders here — order in this list does NOT matter (sorted by priority).
    _BUILDERS: list[AbstractSectionBuilder] = [
        OrganizationsBuilder(),   # priority 10
        IdentifiersBuilder(),     # priority 20
        TitlesBuilder(),          # priority 30
        ObjectivesBuilder(),      # priority 40
        StudyDesignTypeBuilder(), # priority 41
        PurposeTypeBuilder(),     # priority 50
        DateValuesBuilder(),      # priority 52
    ]

    def build(self, fhir_data: dict) -> dict:
        ctx = UsdmBuildContext(fhir_data)

        for builder in sorted(self._BUILDERS, key=lambda b: b.get_priority()):
            result = builder.build(ctx)
            ctx.set(builder.get_key(), result)

        return self._assemble(ctx)

    # -------------------------------------------------------------------------

    def _assemble(self, ctx: UsdmBuildContext) -> dict:
        version = self._assemble_version(ctx)
        return {
            "study": {
                "id": None,
                "name": "CDISC/FHIR - STUDY",
                "description": None,
                "label": None,
                "versions": [version],
                "instanceType": "Study",
            },
            "usdmVersion": "4.0",
            "systemName": "CDISC USDM E2J",
            "systemVersion": "0.62.0",
        }

    def _assemble_version(self, ctx: UsdmBuildContext) -> dict:
        version: dict = {}
        version.setdefault('id', "StudyVersion_0")
        version.setdefault('extensionAttributes', [])
        version.setdefault('versionIdentifier', "Not Available")
        version.setdefault('rationale', "")

        # --- studyDesigns: wrap studyDesign.* sub-sections -------------------
        study_design = self._assemble_study_design(ctx)
        if study_design:
            version["studyDesigns"] = [study_design]

        # --- top-level version fields ----------------------------------------
        for field in ("studyIdentifiers", "titles", "organizations", "dateValues"):
            val = ctx.get(f"version.{field}")
            if val is not None:
                version[field] = val

        # --- default empty collections (instanceType comes last) -------------
        for field in _VERSION_EMPTY_FIELDS:
            version.setdefault(field, [])
        version["instanceType"] = "StudyVersion"

        return version

    def _assemble_study_design(self, ctx: UsdmBuildContext) -> dict | None:
        """
        Collect everything stored at 'version.studyDesign.*' and return a
        single studyDesign dict, or None if no sub-section produced data.
        """
        sd_bag: dict = ctx.get("version.studyDesign") or {}
        if not sd_bag:
            return None

        sd_id = "StudyDesign_1"
        study_design: dict = {
            "id": sd_id,
            "extensionAttributes": [],
            "name": sd_id.upper(),
            "label": "",
        }

        study_type = sd_bag.get("studyType")
        if study_type is not None:
            study_design["studyType"] = study_type

        # Insert sub-sections in a stable order
        for key in ("intentTypes", "subTypes", "objectives"):   # extend as more builders are added
            val = sd_bag.get(key)
            if val is not None:
                study_design[key] = val

        # Set by StudyDesignTypeBuilder alongside studyType (side-channel key,
        # same pattern as OrganizationsBuilder's 'version._orgsByName').
        study_design["instanceType"] = sd_bag.get("_instanceType") or "StudyDesign"
        return study_design

