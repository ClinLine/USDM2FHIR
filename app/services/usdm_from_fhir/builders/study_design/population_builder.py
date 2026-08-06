"""
PopulationBuilder — ResearchStudy.classifier[] + recruitment.targetNumber →
USDM StudyDesign.population (StudyDesignPopulation).

Priority 45 — independent of the other studyDesign.* builders; only reads
'classifier' and 'recruitment' off the root FHIR resource.

FHIR has no dedicated "population" resource. readi_core's
PopulationSectionBuilder.php reads structured StandardCriteriaType values
(sex, min/max age, healthy volunteers, ...) directly off the trial's
eligibility-criteria domain object; on the FHIR side those same facts are
flattened into ResearchStudy.classifier[] as CDISC FEvIR codes (sex, healthy
volunteers) or free text ("Minimum Age: 18 Years") — see
app/config/mappings/04_classifier.yaml for the forward direction and
Input/pilot_FHIR.json for a confirmed real-world example.
plannedEnrollmentNumber comes from recruitment.targetNumber (see
app/config/mappings/11_recruitment.yaml).
description comes from a classifier[].text entry prefixed "Study Population
Source:" (StandardCriteriaType::STUDY_POPULATION free text) — the prefix is
a label, same convention as the "Minimum/Maximum Age:"/"IPDSharingDescription:"
classifier text entries readi_core's ResearchClassifierBuilder.php emits; not
in that file yet, but confirmed against real FHIR classifier[] data.

Not sourced from FHIR (left empty/None — no confirmed mapping exists anywhere
in app/config/mappings/ for these):
  - notes (StandardCriteriaType::GENDER_BASED marker)
  - cohorts (ResearchStudy.comparisonGroup is already fully claimed by
    ComparisonGroupBuilder as arms; telling cohort entries apart from arm
    entries needs the StudyDesignType — Observational designs use cohorts,
    Interventional designs use arms — which is out of scope here)
  - criterionIds (populated in FhirToUsdmService._assemble_study_design after EligibilityCriteriaBuilder runs)
"""

from __future__ import annotations

import re
from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import (
    CLASSIFIER_SEX,
    CLASSIFIER_HEALTHY_VOLUNTEERS,
    AGE_UNIT,
)

# "Minimum Age: 18 Years" / "Maximum Age: 100 Years" — confirmed shape in
# Input/pilot_FHIR.json and Output/pilot_FHIR.json (see 04_classifier.yaml).
_AGE_TEXT_RE = re.compile(r"^(Minimum|Maximum) Age:\s*([\d.]+)\s*([A-Za-z]+)", re.IGNORECASE)

# "Study Population Source: <free text>" — label prefix for the free-text
# population description classifier entry.
_POPULATION_SOURCE_RE = re.compile(r"^Study Population Source:\s*(.+)$", re.IGNORECASE | re.DOTALL)


class _Coding(TypedDict, total=False):
    code: str | None


class _Classifier(TypedDict, total=False):
    text: str | None
    coding: list[_Coding] | _Coding | None


class _Recruitment(TypedDict, total=False):
    targetNumber: int | float | None


class PopulationBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.population"

    def get_priority(self) -> int:
        return 45

    def build(self, context: UsdmBuildContext) -> dict | None:
        classifiers: list[_Classifier] = context.fhir.get("classifier") or []
        classifier_codes = self._classifier_codes(classifiers)

        planned_sex = self._build_planned_sex(context, classifier_codes)
        includes_healthy = self._build_includes_healthy(classifier_codes)
        planned_age = self._build_planned_age(context, classifiers)
        enrollment = self._build_enrollment(context)
        description = self._build_description(classifiers)

        if (
            not planned_sex
            and includes_healthy is None
            and planned_age is None
            and enrollment is None
            and description is None
        ):
            return None

        pop_id = context.next_id("StudyDesignPopulation")
        return {
            "id": pop_id,
            "extensionAttributes": [],
            "name": pop_id.upper(),
            "label": "",
            "description": description,
            "includesHealthySubjects": includes_healthy if includes_healthy is not None else False,
            "plannedEnrollmentNumber": enrollment,
            "plannedCompletionNumber": None,
            "plannedSex": planned_sex,
            "criterionIds": [],
            "plannedAge": planned_age,
            "notes": [],
            "cohorts": [],
            "instanceType": "StudyDesignPopulation",
        }

    # -------------------------------------------------------------------------

    @staticmethod
    def _classifier_codes(classifiers: list[_Classifier]) -> set[str]:
        """
        Flatten every classifier[].coding[].code into one set. 'coding' is a
        FHIR CodeableConcept.coding array (0..*) per spec — normalised here
        to a list since some locally-generated fixtures emit a bare object.
        """
        codes: set[str] = set()
        for entry in classifiers:
            coding = entry.get("coding") if isinstance(entry, dict) else None
            if not coding:
                continue
            items = coding if isinstance(coding, list) else [coding]
            for item in items:
                if isinstance(item, dict) and item.get("code"):
                    codes.add(item["code"])
        return codes

    @staticmethod
    def _build_planned_sex(context: UsdmBuildContext, classifier_codes: set[str]) -> list[dict]:
        return [
            context.make_code(entry["code"], entry["decode"])
            for fhir_code, entry in CLASSIFIER_SEX.items()
            if fhir_code in classifier_codes
        ]

    @staticmethod
    def _build_includes_healthy(classifier_codes: set[str]) -> bool | None:
        for fhir_code, value in CLASSIFIER_HEALTHY_VOLUNTEERS.items():
            if fhir_code in classifier_codes:
                return value
        return None

    @classmethod
    def _build_planned_age(cls, context: UsdmBuildContext, classifiers: list[_Classifier]) -> dict | None:
        min_value = max_value = None
        for entry in classifiers:
            text = entry.get("text") if isinstance(entry, dict) else None
            if not text:
                continue
            match = _AGE_TEXT_RE.match(text.strip())
            if not match:
                continue
            kind, raw_value, raw_unit = match.groups()
            quantity = cls._make_age_quantity(context, raw_value, raw_unit)
            if kind.lower() == "minimum":
                min_value = quantity
            else:
                max_value = quantity

        if min_value is None and max_value is None:
            return None

        # Apply defaults when only one bound is present in the FHIR data:
        #   minValue missing → 0 Years   (no lower bound stated)
        #   maxValue missing → 120 Years (open-ended upper bound)
        # These mirror the sentinel values used by readi_core's
        # PopulationSectionBuilder for "no minimum / no maximum" age.
        if min_value is None:
            min_value = cls._make_age_quantity(context, "0", "Years")
        if max_value is None:
            max_value = cls._make_age_quantity(context, "120", "Years")

        return {
            "id": context.next_id("Range"),
            "extensionAttributes": [],
            "isApproximate": False,
            "minValue": min_value,
            "maxValue": max_value,
            "instanceType": "Range",
        }

    @staticmethod
    def _make_age_quantity(context: UsdmBuildContext, raw_value: str, raw_unit: str) -> dict:
        unit_entry = AGE_UNIT.get(raw_unit.rstrip("sS").lower())
        unit = None
        if unit_entry is not None:
            unit = {
                "id": context.next_id("AliasCode"),
                "extensionAttributes": [],
                "standardCode": context.make_code(unit_entry["code"], unit_entry["decode"]),
                "standardCodeAliases": [],
                "instanceType": "AliasCode",
            }

        value: float = float(raw_value)
        numeric_value = int(value) if value.is_integer() else value

        return {
            "id": context.next_id("Quantity"),
            "extensionAttributes": [],
            "value": numeric_value,
            "unit": unit,
            "instanceType": "Quantity",
        }

    @staticmethod
    def _build_description(classifiers: list[_Classifier]) -> str | None:
        for entry in classifiers:
            text = entry.get("text") if isinstance(entry, dict) else None
            if not text:
                continue
            match = _POPULATION_SOURCE_RE.match(text.strip())
            if match:
                return match.group(1).strip()
        return None

    @staticmethod
    def _build_enrollment(context: UsdmBuildContext) -> dict | None:
        recruitment_raw = context.fhir.get("recruitment")
        # "recruitment" may come through as a list in some locally-generated
        # fixtures (forward-transform artifact) — normalise to a single dict,
        # same defensive pattern as PhaseBuilder uses for "phase".
        if isinstance(recruitment_raw, list):
            recruitment_raw = recruitment_raw[0] if recruitment_raw else None
        recruitment: _Recruitment = recruitment_raw or {}
        target = recruitment.get("targetNumber")
        if target is None:
            return None
        return {
            "id": context.next_id("Quantity"),
            "extensionAttributes": [],
            "value": target,
            "unit": None,
            "instanceType": "Quantity",
        }