"""
EligibilityCriteriaBuilder — FHIR eligibility Group → USDM eligibility structures.

Priority 70.

Reads the contained Group whose id is referenced by
``recruitment.eligibility.reference`` (typically ``#eligibility-criteria``).

Each ``characteristic`` in that Group produces:

  • one ``EligibilityCriterionItem`` (stored at ``version.eligibilityCriterionItems``
    — returned as this builder's result)

  • one ``EligibilityCriterion`` inside the study design (stored directly at
    ``version.studyDesign.eligibilityCriteria`` via ``ctx.set()`` so that the
    standard assembly loop picks it up)

Category mapping:
  characteristic.exclude == False  → Inclusion Criteria  (C25532)
  characteristic.exclude == True   → Exclusion Criteria  (C25370)

Text: ``<p>{description}</p>``  (no tag resolution — accepted limitation).
dictionaryId: ``""`` (empty — no SyntaxTemplateDictionary referenced back).
"""

from __future__ import annotations

import uuid

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir import codes as C


class EligibilityCriteriaBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.eligibilityCriterionItems"

    def get_priority(self) -> int:
        return 70

    # ------------------------------------------------------------------

    def build(self, context: UsdmBuildContext) -> list:
        elig_group = self._find_eligibility_group(context)
        if elig_group is None:
            context.set("version.studyDesign.eligibilityCriteria", [])
            return []

        characteristics: list[dict] = elig_group.get("characteristic") or []

        items: list[dict] = []
        criteria: list[dict] = []

        inclusion_counter = 0
        exclusion_counter = 0

        for char in characteristics:
            description: str = (char.get("description") or "").strip()
            exclude: bool = bool(char.get("exclude", False))

            # ---- EligibilityCriterionItem --------------------------------
            item_id = f"EligibilityCriterionItem_{len(items) + 1}"
            item_name = f"ECI_{len(items) + 1}"

            item: dict = {
                "id": item_id,
                "name": item_name,
                "text": f"<p>{description}</p>" if description else "<p></p>",
                "dictionaryId": "",
                "notes": [],
                "instanceType": "EligibilityCriterionItem",
            }
            items.append(item)

            # ---- EligibilityCriterion ------------------------------------
            crit_id = str(uuid.uuid4())
            crit_index = len(criteria) + 1

            if exclude:
                exclusion_counter += 1
                identifier = f"EX{exclusion_counter:03d}"
                cat_entry = C.ELIGIBILITY_CATEGORY_EXCLUSION
            else:
                inclusion_counter += 1
                identifier = f"IN{inclusion_counter:03d}"
                cat_entry = C.ELIGIBILITY_CATEGORY_INCLUSION

            category = context.make_code(cat_entry["code"], cat_entry["decode"])

            criterion: dict = {
                "id": crit_id,
                "name": f"CRIT_{crit_index}",
                "label": "",
                "identifier": identifier,
                "category": category,
                "notes": [],
                "criterionItemId": item_id,
                "instanceType": "EligibilityCriterion",
            }
            criteria.append(criterion)

        # Store criteria directly into the study-design bag so _assemble_study_design picks them up
        context.set("version.studyDesign.eligibilityCriteria", criteria)

        return items

    # ------------------------------------------------------------------

    @staticmethod
    def _find_eligibility_group(context: UsdmBuildContext) -> dict | None:
        """
        Resolve the eligibility Group from the ResearchStudy's contained resources.

        Looks at ``recruitment.eligibility.reference`` first (e.g. ``"#eligibility-criteria"``).
        Falls back to searching contained for a Group with the EBM profile.
        """
        # Prefer the explicit reference from recruitment
        recruitment = context.fhir.get("recruitment") or {}
        if isinstance(recruitment, list):
            recruitment = recruitment[0] if recruitment else {}

        ref: str = (recruitment.get("eligibility") or {}).get("reference", "")
        group_id: str | None = ref.lstrip("#") if ref.startswith("#") else None

        contained: list[dict] = context.fhir.get("contained") or []

        if group_id:
            group = next(
                (r for r in contained if r.get("resourceType") == "Group" and r.get("id") == group_id),
                None,
            )
            if group is not None:
                return group

        # Fallback: first Group with EBM study-eligibility-criteria profile
        ebm_profile = "http://hl7.org/fhir/uv/ebm/StructureDefinition/study-eligibility-criteria"
        for r in contained:
            if r.get("resourceType") == "Group":
                profiles: list[str] = (r.get("meta") or {}).get("profile") or []
                if ebm_profile in profiles:
                    return r

        return None

