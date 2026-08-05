"""
AbstractIndicationsBuilder — shared extraction logic for indications and
contra-indications from the FHIR contained eligibility Group.

Algorithm (mirrors readi_core AbstractIndicationsSectionBuilder.php):

1. Find the contained Group with id="eligibility-criteria".
2. From its characteristic[], collect every valueReference.reference that
   starts with "#" — these point to other contained Groups.
3. For each referenced Group, scan characteristic[] for entries where
   code.coding[0].code == ELIGIBILITY_CONDITION_LOINC_CODE ("75323-6").
4. Partition by exclude:
   - false  → inclusion criterion → Indication
   - true   → exclusion criterion → ContraIndication
"""

from __future__ import annotations

from abc import abstractmethod

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import (
    ELIGIBILITY_CONDITION_LOINC_CODE,
    SNOMED_CODE_SYSTEM,
    SNOMED_CODE_SYSTEM_VERSION,
    FHIR_SYSTEM_TO_USDM_CODE_SYSTEM,
)

_ELIGIBILITY_GROUP_ID = "eligibility-criteria"


class AbstractIndicationsBuilder(AbstractSectionBuilder):
    """
    Base for IndicationsBuilder (inclusions) and ContraIndicationsBuilder
    (exclusions). Subclasses only differ in the exclude flag they filter for
    and in what they produce.
    """

    @abstractmethod
    def is_contra_indication(self) -> bool:
        """Return True for ContraIndicationsBuilder, False for IndicationsBuilder."""

    # -------------------------------------------------------------------------
    # Shared extraction helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _collect_condition_chars(fhir_data: dict) -> list[dict]:
        """
        Return all characteristic entries with code.coding[0].code ==
        ELIGIBILITY_CONDITION_LOINC_CODE from the Groups referenced by the
        'eligibility-criteria' contained Group.
        """
        contained: list[dict] = fhir_data.get("contained") or []
        contained_by_id: dict[str, dict] = {
            item["id"]: item
            for item in contained
            if isinstance(item, dict) and item.get("id")
        }

        elig_group = contained_by_id.get(_ELIGIBILITY_GROUP_ID)
        if not elig_group:
            return []

        # Collect referenced group IDs (strip leading "#")
        ref_ids: list[str] = []
        for ch in elig_group.get("characteristic") or []:
            ref = (ch.get("valueReference") or {}).get("reference", "")
            if ref.startswith("#"):
                ref_ids.append(ref[1:])

        # Collect condition-typed characteristics from each referenced Group
        condition_chars: list[dict] = []
        for ref_id in ref_ids:
            group = contained_by_id.get(ref_id)
            if not group:
                continue
            for ch in group.get("characteristic") or []:
                coding = ((ch.get("code") or {}).get("coding") or [])
                if coding and coding[0].get("code") == ELIGIBILITY_CONDITION_LOINC_CODE:
                    condition_chars.append(ch)

        return condition_chars

    @staticmethod
    def _extract_name(ch: dict) -> str:
        """
        Best-effort name: use the SNOMED display from valueCodeableConcept
        (short, standardised term). Falls back to description.
        """
        coding = ((ch.get("valueCodeableConcept") or {}).get("coding") or [])
        if coding and coding[0].get("display"):
            return coding[0]["display"]
        return ch.get("description") or ""

    @staticmethod
    def _extract_label(ch: dict) -> str:
        """Label: the characteristic description text."""
        return ch.get("description") or ""

    @staticmethod
    def _build_code(context: UsdmBuildContext, ch: dict) -> dict | None:
        """Build a USDM Code from the valueCodeableConcept coding of the characteristic."""
        coding = ((ch.get("valueCodeableConcept") or {}).get("coding") or [])
        if not coding:
            return None
        c = coding[0]
        code_val: str = c.get("code") or ""
        decode: str = c.get("display") or ""
        fhir_system: str = c.get("system") or ""
        # Map FHIR system URI → USDM codeSystem display name; fall back to SNOMED default
        code_system: str = FHIR_SYSTEM_TO_USDM_CODE_SYSTEM.get(fhir_system, fhir_system or SNOMED_CODE_SYSTEM)
        if not code_val:
            return None
        return context.make_code_with_system(
            code_val,
            decode,
            code_system,
            SNOMED_CODE_SYSTEM_VERSION,
        )

