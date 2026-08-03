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
from app.services.usdm_from_fhir.builders.study_design.objectives_builder import ObjectivesBuilder
from app.services.usdm_from_fhir.builders.study_design.study_design_type_builder import StudyDesignTypeBuilder
from app.services.usdm_from_fhir.builders.study_design.characteristics_builder import CharacteristicsBuilder
from app.services.usdm_from_fhir.builders.study_design.purpose_type_builder import PurposeTypeBuilder
from app.services.usdm_from_fhir.builders.study_design.phase_builder import PhaseBuilder
from app.services.usdm_from_fhir.builders.study_design.population_builder import PopulationBuilder
from app.services.usdm_from_fhir.builders.date_values_builder import DateValuesBuilder
from app.services.usdm_from_fhir.builders.masking_roles_builder import MaskingRolesBuilder
from app.services.usdm_from_fhir.builders.study_design.blinding_schema_builder import BlindingSchemaBuilder
from app.services.usdm_from_fhir.builders.study_design.comparison_group_builder import ComparisonGroupBuilder
from app.services.usdm_from_fhir.builders.study_design.epochs_builder import EpochsBuilder
from app.services.usdm_from_fhir.builders.study_design.elements_builder import ElementsBuilder
from app.services.usdm_from_fhir.builders.study_design.study_cells_builder import StudyCellsBuilder

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
    "biomedicalConcepts",
    "bcCategories",
    "bcSurrogates",
    "conditions",
    "dictionaries",
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
        CharacteristicsBuilder(), # priority 42
        PopulationBuilder(),      # priority 45
        PurposeTypeBuilder(),     # priority 50
        PhaseBuilder(),           # priority 51
        DateValuesBuilder(),      # priority 52
        MaskingRolesBuilder(),    # priority 55
        BlindingSchemaBuilder(),  # priority 56
        ComparisonGroupBuilder(), # priority 60
        EpochsBuilder(),          # priority 61
        ElementsBuilder(),        # priority 62
        StudyCellsBuilder(),      # priority 63
    ]

    # -------------------------------------------------------------------------
    # Bundle / single-resource detection
    # -------------------------------------------------------------------------

    @staticmethod
    def _resolve_input(fhir_data: dict) -> tuple[dict, list[dict]]:
        """
        Accept either:
          - a plain FHIR ResearchStudy resource, or
          - a FHIR Bundle (resourceType=="Bundle") / Bundle-like collection
            (has an "entry" list without resourceType).

        Returns ``(research_study_dict, bundle_entries)`` where *bundle_entries*
        is the flat list of resource dicts extracted from the bundle (empty when
        the input was a single resource).

        For bundles, the *first* entry whose resourceType is "ResearchStudy" is
        used.  If none is found, the first entry is used as a fallback.
        """
        entries_raw: list = fhir_data.get("entry", [])

        # Not a bundle — return as-is
        if not entries_raw or not isinstance(entries_raw, list):
            return fhir_data, []

        # Flatten entries: each entry may be {"resource": {...}} or the resource itself
        bundle_entries: list[dict] = []
        for e in entries_raw:
            if isinstance(e, dict):
                bundle_entries.append(e.get("resource", e))

        # Pick the first ResearchStudy (or fall back to the first entry)
        research_study: dict | None = next(
            (r for r in bundle_entries if r.get("resourceType") == "ResearchStudy"),
            bundle_entries[0] if bundle_entries else fhir_data,
        )

        return research_study, bundle_entries

    def build(self, fhir_data: dict) -> dict:
        research_study, bundle_entries = self._resolve_input(fhir_data)
        ctx = UsdmBuildContext(research_study, bundle_entries=bundle_entries)

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
        for field in ("studyIdentifiers", "titles", "organizations", "dateValues", "roles"):
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
        for key in ("intentTypes", "subTypes", "studyPhase", "characteristics", "blindingSchema", "objectives", "population", "arms", "studyCells", "epochs", "elements"):   # extend as more builders are added
            val = sd_bag.get(key)
            if val is not None:
                study_design[key] = val

        # Set by StudyDesignTypeBuilder alongside studyType (side-channel key,
        # same pattern as OrganizationsBuilder's 'version._orgsByName').
        study_design["instanceType"] = sd_bag.get("_instanceType") or "StudyDesign"
        return study_design

