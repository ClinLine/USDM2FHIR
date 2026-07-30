"""
Shared CDISC code lookup tables for FHIR → USDM reverse conversion.

Each lookup maps a FHIR coded value (e.g. "primary") to the corresponding
USDM Code {code, decode}.  An entry is intentionally omitted when the mapping
is unconfirmed — the builder that uses it should skip the field rather than guess.
"""

CDISC_CODE_SYSTEM = {
    "codeSystem": "http://www.cdisc.org",
    "codeSystemVersion": "2025-09-26",
}

# ---------------------------------------------------------------------------
# Individual lookup tables
# ---------------------------------------------------------------------------

# ResearchStudy.label.type.coding.code  →  StudyTitle.type Code
# Confirmed against Input/NCT01750580_limited_tagged_resp.json
TITLE_TYPE: dict[str, dict] = {
    "short-title": {"code": "C207615", "decode": "Brief Study Title"},
    "official":    {"code": "C207616", "decode": "Official Study Title"},
    "scientific":  {"code": "C207618", "decode": "Scientific Study Title"},
    # "acronym" intentionally omitted — C207617 vs C94108 unresolved, see plan
}

# ResearchStudy.objective.type.coding.code  →  Objective.level Code
# Confirmed against Input/NCT01750580_limited_tagged_resp.json
OBJECTIVE_LEVEL: dict[str, dict] = {
    "primary":     {"code": "C85826",  "decode": "Study Primary Objective"},
    "secondary":   {"code": "C85827",  "decode": "Study Secondary Objective"},
    "exploratory": {"code": "C163559", "decode": "Exploratory Study Objective"},
}

# ResearchStudy.objective.outcomeMeasure.type.coding.code  →  Endpoint.level Code
# primary/secondary confirmed in test data; exploratory is a reasonable assumption
ENDPOINT_LEVEL: dict[str, dict] = {
    "primary":     {"code": "C94496",  "decode": "Primary Endpoint"},
    "secondary":   {"code": "C139173", "decode": "Secondary Endpoint"},
    "exploratory": {"code": "C163560", "decode": "Exploratory Endpoint"},
}

# ResearchStudy.progressStatus[].state.coding.code  →  GovernanceDate.type Code
# Only "update-posting" is confirmed/needed — all other progressStatus states
# are intentionally ignored by DateValuesBuilder (out of scope for now).
GOVERNANCE_DATE_TYPE: dict[str, dict] = {
    "update-posting": {"code": "C215664", "decode": "Issued Date"},
}

# Fixed GeographicScope used for the D_ISSUED GovernanceDate until per-country
# progressStatus mapping is needed.
GEOGRAPHIC_SCOPE_GLOBAL: dict = {"code": "C68846", "decode": "Global"}

