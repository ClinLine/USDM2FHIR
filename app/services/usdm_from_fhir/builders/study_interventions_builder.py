"""
StudyInterventionsBuilder — FHIR contained EvidenceVariable → USDM version.studyInterventions.

Priority 58 — independent of every other builder; only reads 'contained' off the
root FHIR resource.

Mirrors the forward mapping in
app/config/mappings/18_study_intervention_evidence_variable.yaml (and readi_core's
ResearchContainedBuilder::buildInterventionEvidenceVariables()): each
StudyIntervention is exported as a contained EvidenceVariable resource with
meta.profile "variable-definition", title/name = intervention label, handling =
the fixed "boolean variable" STATO coding, and classifier[0].text =
"Intervention Type: <DECODE>" (e.g. "Intervention Type: DRUG"). Only contained
EvidenceVariable entries carrying that classifier marker are treated as study
interventions — the biomedical-concept/endpoint EvidenceVariable resources (see
14_evidence_variable.yaml) have no such classifier and are left untouched.

USDM StudyIntervention fields that FHIR does not carry (role,
minimumResponseDuration, codes, administrations) are intentionally left empty —
no source data exists for them on the FHIR side.
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import (
    INTERVENTION_TYPE,
    INTERVENTION_TYPE_CLASSIFIER_PREFIX,
)


class _Classifier(TypedDict, total=False):
    text: str | None


class _EvidenceVariable(TypedDict, total=False):
    resourceType: str | None
    title: str | None
    description: str | None
    classifier: list[_Classifier] | None


class StudyInterventionsBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyInterventions"

    def get_priority(self) -> int:
        return 58

    def build(self, context: UsdmBuildContext) -> list:
        contained: list[_EvidenceVariable] = context.fhir.get("contained") or []
        interventions: list[dict] = []

        i = 0
        for entry in contained:
            intervention_type = self._extract_type_text(entry)
            if intervention_type is None:
                continue

            intervention_id = f"StudyIntervention_{i}"
            i += 1

            intervention: dict = {
                "id": intervention_id,
                "extensionAttributes": [],
                "name": intervention_id.upper(),
                "label": entry.get("title") or "",
                "description": entry.get("description"),
            }
            type_code = context.lookup_code(INTERVENTION_TYPE, intervention_type)
            if type_code is not None:
                intervention["type"] = type_code
            intervention["codes"] = []
            intervention["administrations"] = []
            intervention["notes"] = []
            intervention["instanceType"] = "StudyIntervention"

            interventions.append(intervention)

        return interventions

    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_type_text(entry: _EvidenceVariable) -> str | None:
        """
        Return the raw intervention type (e.g. "DRUG") from a contained
        EvidenceVariable's classifier[].text, or None if *entry* is not one of
        our study-intervention EvidenceVariable resources.
        """
        if not isinstance(entry, dict) or entry.get("resourceType") != "EvidenceVariable":
            return None

        for classifier in entry.get("classifier") or []:
            text: str | None = classifier.get("text") if isinstance(classifier, dict) else None
            if text and text.startswith(INTERVENTION_TYPE_CLASSIFIER_PREFIX):
                return text[len(INTERVENTION_TYPE_CLASSIFIER_PREFIX):]

        return None