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

# ResearchStudy.studyDesign[].coding.code (SEVCO)  →  StudyDesign.studyType Code
# + StudyDesign.instanceType.
# Mirrors readi_core StudyDesignMappedTypes::getStudyTypeFhirMapping() (SEVCO
# side) joined with ::getStudyTypeMapping() (CDISC side); "instance_type"
# mirrors the branching in StudyDesignsSectionBuilder::build() (interventionModel
# set → InterventionalStudyDesign, observationalModel set → ObservationalStudyDesign).
# SEVCO:01038 (expanded access) intentionally omitted — readi_core does not
# define an instanceType for it either.
STUDY_DESIGN_TYPE: dict[str, dict] = {
    "SEVCO:01001": {"code": "C98388", "decode": "Interventional Study", "instance_type": "InterventionalStudyDesign"},
    "SEVCO:01002": {"code": "C16084", "decode": "Observational Study", "instance_type": "ObservationalStudyDesign"},
}

# ResearchStudy.purposeType[].coding.code  →  StudyDesign.intentTypes Code.
# FHIR-side codes come from app/config/mappings/06_purpose_type.yaml ("purpose
# Intent" row). The intentTypes/subTypes split mirrors readi_core
# StudyDesignMappedTypes::getPrimaryPurposeMapping()'s 'sdtmC66736' flag — true
# means the code belongs to the CDISC SDTM Trial Intent Type (C66736) codelist
# and goes to intentTypes; everything else goes to subTypes.
# "treatment" confirmed against Input/pilot_FHIR.json; the rest are the sibling
# codes from the same YAML $Recode table, all with sdtmC66736 = true.
PURPOSE_INTENT_TYPE: dict[str, dict] = {
    "treatment":                {"code": "C49656",  "decode": "Treatment Study"},
    "prevention":                {"code": "C49657",  "decode": "Prevention Study"},
    "diagnostic":                {"code": "C49653",  "decode": "Diagnosis Study"},
    "screening":                 {"code": "C71485",  "decode": "Screening Study"},
    "supportive-care":           {"code": "C71486",  "decode": "Supportive Care Study"},
    "health-services-research":  {"code": "C15245",  "decode": "Health Services Research"},
    "device-feasibility":        {"code": "C139174", "decode": "Device Feasibility Study"},
    "basic-science":             {"code": "C15714",  "decode": "Basic Science"},
}

# ResearchStudy.purposeType[].coding.code  →  StudyDesign.subTypes Code.
# Same FHIR array as PURPOSE_INTENT_TYPE (purposeType.coding) — distinguished
# by code, per app/config/mappings/06_purpose_type.yaml ("purpose SubType" row).
# All codes below have no 'sdtmC66736' flag in getPrimaryPurposeMapping() (i.e.
# it's absent/false), which is why they land in subTypes and not intentTypes.
# safety/efficacy/pharmacokinetic confirmed against Input/CDISC_Pilot_Study_v4_FIXED.json;
# the rest follow the same "<Name> Study" CDISC decode pattern.
PURPOSE_SUB_TYPE: dict[str, dict] = {
    "safety":           {"code": "C49667",  "decode": "Safety Study"},
    "efficacy":         {"code": "C49666",  "decode": "Efficacy Study"},
    "pharmacokinetic":  {"code": "C49663",  "decode": "Pharmacokinetic Study"},
    "pharmacodynamic":  {"code": "C49662",  "decode": "Pharmacodynamic Study"},
    "bioequivalence":   {"code": "C49665",  "decode": "Bioequivalence Study"},
    "dose-response":    {"code": "C127803", "decode": "Dose-Response Study"},
    "pharmacogenetic":  {"code": "C129001", "decode": "Pharmacogenetic Study"},
    "pharmacogenomic":  {"code": "C49661",  "decode": "Pharmacogenomic Study"},
    "incidence":        {"code": "C215653", "decode": "Incidence Study"},
    "prevalence":       {"code": "C215675", "decode": "Prevalence Study"},
}

# ResearchStudy.phase.coding[].code (FHIR research-study-phase system)  →
# StudyDesign.studyPhase.standardCode Code.
# Confirmed against app/config/mappings/07_phase.yaml and readi_core
# StudyPhaseType::getStudyPhaseMapping() / ::getStudyPhaseFhirMapping()
# (src/Doctrine/ORM/Type/StudyPhaseType.php) — decode strings are the CDISC
# side ("Phase I Trial" etc.), not the FHIR display text ("Phase 1").
STUDY_PHASE: dict[str, dict] = {
    "n-a":             {"code": "C48660",  "decode": "Not Applicable"},
    "early-phase-1":   {"code": "C54721",  "decode": "Phase 0 Trial"},
    "phase-1":         {"code": "C15600",  "decode": "Phase I Trial"},
    "phase-1-phase-2": {"code": "C15693",  "decode": "Phase I/II Trial"},
    "phase-2":         {"code": "C15601",  "decode": "Phase II Trial"},
    "phase-2-phase-3": {"code": "C15694",  "decode": "Phase II/III Trial"},
    "phase-3":         {"code": "C15602",  "decode": "Phase III Trial"},
    "phase-4":         {"code": "C15603",  "decode": "Phase IV Trial"},
}

# ResearchStudy.studyDesign[].coding[].code (SEVCO)  →  StudyDesign.characteristics Code.
# Mirrors readi_core StudyDesignMappedTypes::getAllocationMapping() joined with
# ResearchStudyDesignBuilder's SEVCO:01003 emission (only RANDOMIZED has a
# mapping there; NON_RANDOMIZED returns null / has no FHIR coding), so this
# table intentionally has a single entry — an unmatched studyDesign SEVCO code
# simply means "no characteristics", not "unknown allocation".
STUDY_DESIGN_CHARACTERISTIC: dict[str, dict] = {
    "SEVCO:01003": {"code": "C46079", "decode": "Randomized"},
}

# ResearchStudy.studyDesign[].coding[].code (SEVCO)  →  StudyRole (masking) Code.
# Mirrors readi_core StudyDesignMappedTypes::getMaskingMapping() (who -> CDISC
# code) joined with the HL7 FHIR R5 study-design ValueSet
# (https://www.hl7.org/fhir/R5/codesystem-study-design.html) for the SEVCO
# side; SEVCO:01063 (investigator) isn't on that page and was confirmed
# separately. There is no positive FHIR code for "no masking" — open-label is
# only ever represented as a free-text studyDesign[] entry (see
# MASKING_NONE_TEXT_MARKER), never a coding.
MASKING_WHO: dict[str, dict] = {
    "SEVCO:01060": {"code": "C41189",  "decode": "Study Subject"},
    "SEVCO:01061": {"code": "C17445",  "decode": "Care Provider"},
    "SEVCO:01063": {"code": "C25936",  "decode": "Investigator"},
    "SEVCO:01062": {"code": "C207599", "decode": "Outcomes Assessor"},
}

# Canonical order from readi_core StudyDesignMappedTypes::getAllMaskingMapping()
# — emitted in full, all isMasked=false, when masking is explicitly NONE/open-label.
MASKING_ALL_ORDER: list[str] = ["SEVCO:01060", "SEVCO:01061", "SEVCO:01063", "SEVCO:01062"]

# Substring (case-insensitive) that marks a studyDesign[].text entry as the
# open-label/no-masking declaration, e.g. "Design Masking: None (Open Label)"
# (confirmed in Input/pilot_FHIR.json).
MASKING_NONE_TEXT_MARKER = "open label"

