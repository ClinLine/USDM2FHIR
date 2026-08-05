"""
ObjectivesBuilder — ResearchStudy.objective → USDM objectives array (+ endpoints).

Priority 40 — no cross-builder dependencies.

Each FHIR objective maps to one USDM Objective.
Each FHIR outcomeMeasure maps to one USDM Endpoint nested inside its Objective.

An Objective without a type.coding.code still gets built (level is omitted).
An Endpoint without a type.coding.code still gets built (level is omitted).
"""

from __future__ import annotations

from typing import TypedDict

from app.services.usdm_from_fhir.base_builder import AbstractSectionBuilder
from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import OBJECTIVE_LEVEL, ENDPOINT_LEVEL


class _Coding(TypedDict, total=False):
    code: str | None
    display: str | None
    system: str | None


class _CodeableConcept(TypedDict, total=False):
    coding: list[_Coding] | None


class _Endpoint(TypedDict, total=False):
    display: str | None


class _OutcomeMeasure(TypedDict, total=False):
    endpoint: _Endpoint | None
    type: _CodeableConcept | None


class _Objective(TypedDict, total=False):
    name: str | None
    type: _CodeableConcept | None
    outcomeMeasure: list[_OutcomeMeasure] | None


def _first_coding_code(codeable_concept: dict | None) -> str | None:
    """Return the code of the first coding entry in a CodeableConcept, or None."""
    if not codeable_concept:
        return None
    coding = codeable_concept.get("coding") or []
    first = coding[0] if isinstance(coding, list) and coding else (coding if isinstance(coding, dict) else {})
    return first.get("code") if isinstance(first, dict) else None


class ObjectivesBuilder(AbstractSectionBuilder):

    def get_key(self) -> str:
        return "version.studyDesign.objectives"

    def get_priority(self) -> int:
        return 40

    def build(self, context: UsdmBuildContext) -> list:
        fhir_objectives: list[_Objective] = context.fhir.get("objective") or []
        result = []

        for i, fhir_obj in enumerate(fhir_objectives):
            obj_id = f"Objective_{i}"

            # --- level (optional) -------------------------------------------
            type_code: str | None = _first_coding_code(fhir_obj.get("type"))
            level = context.lookup_code(OBJECTIVE_LEVEL, type_code) if type_code else None

            # --- endpoints ---------------------------------------------------
            endpoints = self._build_endpoints(context, i, fhir_obj.get("outcomeMeasure") or [])

            # --- assemble ----------------------------------------------------
            objective: dict = {
                "id": obj_id,
                "name": obj_id.upper(),
            }
            if level is not None:
                objective["level"] = level
            objective["text"] = fhir_obj.get("name") or ""
            objective["endpoints"] = endpoints
            objective["notes"] = []
            objective["instanceType"] = "Objective"

            result.append(objective)

        return result

    # -------------------------------------------------------------------------

    @staticmethod
    def _build_endpoints(
        context: UsdmBuildContext,
        obj_index: int,
        outcome_measures: list[_OutcomeMeasure],
    ) -> list:
        endpoints = []
        for j, om in enumerate(outcome_measures):
            ep_id = f"Endpoint_{obj_index}_{j}"
            display: str = (om.get("endpoint") or {}).get("display") or ""

            type_code: str | None = _first_coding_code(om.get("type"))
            level = context.lookup_code(ENDPOINT_LEVEL, type_code) if type_code else None

            endpoint: dict = {
                "id": ep_id,
                "name": ep_id.upper(),
                "text": display,
                "purpose": "",
                "notes": [],
            }
            if level is not None:
                endpoint["level"] = level
            endpoint["instanceType"] = "Endpoint"

            endpoints.append(endpoint)

        return endpoints

