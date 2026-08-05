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

# Default SNOMED CT version used when building condition/indication codes
# (the FHIR payload does not carry a version, so we fall back to this constant).
SNOMED_CODE_SYSTEM = "Systematic Nomenclature of Medicine - Clinical Terms (IHTSDO)"
SNOMED_CODE_SYSTEM_VERSION = "2025-02-01"

# Maps FHIR coding.system URIs → USDM codeSystem display names.
# Used by builders that construct Code objects from non-CDISC FHIR codings
# (e.g. SNOMED CT condition codes on eligibility criteria).
FHIR_SYSTEM_TO_USDM_CODE_SYSTEM: dict[str, str] = {
    "http://snomed.info/sct": "Systematic Nomenclature of Medicine - Clinical Terms (IHTSDO)",
    "http://loinc.org": "Logical Observation Identifiers Names and Codes (LOINC)",
    "http://www.nlm.nih.gov/research/umls/rxnorm": "RxNorm",
}

# LOINC code that marks a "Condition" characteristic inside an eligibility Group.
ELIGIBILITY_CONDITION_LOINC_CODE = "75323-6"

# Eligibility criterion category codes (CDISC)
ELIGIBILITY_CATEGORY_INCLUSION = {"code": "C25532", "decode": "Inclusion Criteria"}
ELIGIBILITY_CATEGORY_EXCLUSION = {"code": "C25370", "decode": "Exclusion Criteria"}

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

# ResearchStudy.studyDesign[].coding[].code (SEVCO)  →  StudyDesign.model Code
# (intervention model / cohort design).
# Mirrors readi_core StudyDesignMappedTypes::getInterventionModelFhirMapping()
# (SEVCO side) joined with ::getInterventionModelMapping() (CDISC side); see
# also app/config/mappings/15_study_design.yaml ("Study Design cohort design"
# row) for the forward direction. Only SINGLE_GROUP/PARALLEL/CROSSOVER have a
# FHIR SEVCO coding in readi_core — FACTORIAL/SEQUENTIAL/UNKNOWN (intervention)
# and the whole observational-model table have none, so they're intentionally
# absent here.
STUDY_DESIGN_MODEL: dict[str, dict] = {
    "SEVCO:01016": {"code": "C82640", "decode": "Single Group Study"},
    "SEVCO:01011": {"code": "C82639", "decode": "Parallel Study"},
    "SEVCO:01012": {"code": "C82637", "decode": "Crossover Study"},
}

# Fallback when studyDesign[] carries none of the STUDY_DESIGN_MODEL SEVCO
# codes above — mirrors readi_core StudyDesignMappedTypes::getInterventionModelMapping()'s
# self::UNKNOWN case (used for CTIS data with no determinable intervention model).
STUDY_DESIGN_MODEL_UNKNOWN: dict = {"code": "C17998", "decode": "Unknown"}

# ResearchStudy.studyDesign[].coding[].code (ClinicalTrials.gov ObservationalModel
# enum, system "https://clinicaltrials.gov/data-about-studies/study-data-structure#enum-ObservationalModel")
# → StudyDesign.model Code (observational model).
# Mirrors readi_core StudyDesignMappedTypes::getObservationalModelMapping() (CDISC
# side) joined with the raw ct.gov enum emitted by ResearchStudyDesignBuilder.php /
# FhirConstants::OBSERVATIONAL_MODEL_DISPLAY_MAP (ct.gov side); see also
# app/config/mappings/15_study_design.yaml ("Study Design observational model" row)
# for the forward direction. DEFINED_POPULATION and NATURAL_HISTORY are
# intentionally absent — readi_core has no CDISC code for them yet, so the
# forward direction never emits a coding for those two values either.
STUDY_DESIGN_OBSERVATIONAL_MODEL: dict[str, dict] = {
    "COHORT":                {"code": "C15208",  "decode": "Cohort Study"},
    "CASE_CONTROL":          {"code": "C15197",  "decode": "Case-Control Study"},
    "CASE_ONLY":             {"code": "C15362",  "decode": "Case Study"},
    "CASE_CROSSOVER":        {"code": "C127779", "decode": "Observational Case-Crossover Study"},
    "ECOLOGIC_OR_COMMUNITY": {"code": "C127780", "decode": "Ecologic or Community Based Study"},
    "FAMILY_BASED":          {"code": "C15407",  "decode": "Family Study"},
    "OTHER":                 {"code": "EXT0011", "decode": "Other Observational model"},
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

# Number of masked roles (from the same MaskingRolesBuilder result reused by
# BlindingSchemaBuilder) → StudyDesign.blindingSchema Code.
# Mirrors readi_core StudyDesignMappedTypes::getBlindingSchemaMapping(), keyed
# there by the internal masking-level constant (NONE/SINGLE/DOUBLE/TRIPLE)
# rather than a count — FHIR has no such level field, only per-role codings,
# so the level is reconstructed from how many roles are masked. QUADRUPLE (4
# masked roles) is intentionally absent: getBlindingSchemaMapping() has no
# case for it either and falls through to `default => null`.
BLINDING_SCHEMA_BY_MASKED_COUNT: dict[int, dict] = {
    0: {"code": "C49659", "decode": "OPEN LABEL"},
    1: {"code": "C28233", "decode": "SINGLE BLIND"},
    2: {"code": "C15228", "decode": "DOUBLE BLIND"},
    3: {"code": "C0012X", "decode": "TRIPLE BLIND"},
}

# contained Group.code.text (referenced by comparisonGroup[].eligibility.reference)
# → StudyArm.type Code.
# readi_core's FHIR export does not emit ArmMappedTypes::getArmTypeMapping()
# anywhere directly; the Group.code.text values below are inferred by
# title-casing the PHP enum constants (EXPERIMENTAL, ACTIVE_COMPARATOR, ...)
# and pairing them with that same table's CDISC code/decode. Only "Experimental"
# is confirmed against Input/pilot_FHIR.json — the rest follow the identical
# naming convention but are unconfirmed against real data.
ARM_TYPE: dict[str, dict] = {
    "Experimental":       {"code": "C174266", "decode": "Investigational Arm"},
    "Active Comparator":  {"code": "C174267", "decode": "Active Comparator Arm"},
    "Placebo Comparator": {"code": "C174268", "decode": "Placebo Comparator Arm"},
    "Sham Comparator":    {"code": "C174269", "decode": "Sham Comparator Arm"},
    "No Intervention":    {"code": "C174270", "decode": "No Intervention Arm"},
    "Other":              {"code": "EXT0013",  "decode": "Other Arm Type"},
    "Unknown":            {"code": "C17998",  "decode": "Unknown"},
}

# StudyArm.dataOriginType — fixed for every arm in readi_core's ArmsSectionBuilder
# (all study arms are "Data Generated Within Study", never external/sourced data).
DATA_ORIGIN_TYPE_WITHIN_STUDY: dict = {"code": "C188866", "decode": "Data Generated Within Study"}

# StudyArm.dataOriginDescription — fixed text paired with DATA_ORIGIN_TYPE_WITHIN_STUDY
# above, same readi_core ArmsSectionBuilder constant.
DATA_ORIGIN_DESCRIPTION_WITHIN_STUDY = "Data collected from subjects"

# ResearchStudy.associatedParty[].role.coding[].code (research-study-party-role system)
# → StudyRole.code Code.
#
# Only the 4 codes that readi_core actually emits and maps back to USDM roles:
#   lead-sponsor        ← RolesSectionBuilder (owner/LEAD)
#                          SponsorsMappedTypes::LEAD_SPONSOR_STUDY_ROLE_CDISC_CODE = 'C70793'
#   sponsor-investigator← RolesSectionBuilder (responsible party SPONSOR_INVESTIGATOR)
#                          StudyDesignMappedTypes::getResponsiblePartyMapping → EXT0003
#   primary-investigator← RolesSectionBuilder (responsible party PRINCIPAL_INVESTIGATOR)
#                          StudyDesignMappedTypes::getResponsiblePartyMapping → C19924
#   collaborator        ← RolesSectionBuilder (COLLABORATOR sponsor)
#                          UsdmBuildContext::getCollaboratorMapping → EXT0004
#
# All other codes from FhirConstants (sponsor, study-chair, recruitment-contact,
# general-contact, sub-investigator, funding-source, irb, data-monitoring) are NOT
# mapped to any USDM StudyRole in readi_core — builders that consume them skip
# unrecognised codes via lookup_code returning None.
ASSOCIATED_PARTY_ROLE: dict[str, dict] = {
    "lead-sponsor":          {"code": "C70793", "decode": "Sponsor"},
    "sponsor-investigator":  {"code": "EXT0003", "decode": "Sponsor-Investigator"},
    "primary-investigator":  {"code": "C19924", "decode": "Principal investigator"},
    "collaborator":          {"code": "EXT0004", "decode": "Collaborator"},
}

# Fixed Organization.type code used when the affiliation type is unknown.
# Mirrors readi_core's Organization::getType() fallback.
ORG_TYPE_UNKNOWN: dict = {"code": "C17998", "decode": "Unknown"}

# StudyIntervention.role codes — mirrors StudyInterventionsSectionBuilder.php
# title contains "placebo" → Placebo; otherwise → Experimental Intervention
INTERVENTION_ROLE_PLACEBO: dict = {"code": "C753", "decode": "Placebo"}
INTERVENTION_ROLE_EXPERIMENTAL: dict = {"code": "C41161", "decode": "Experimental Intervention"}

# ResearchStudy.classifier[].coding[].code (FEvIR CodeSystem 419455)  →
# StudyDesignPopulation.plannedSex Code.
# Confirmed against Input/pilot_FHIR.json + app/config/mappings/04_classifier.yaml.
# Mirrors readi_core StandardCriteriaType::getSexMapping() — FHIR only carries
# the two positive-inclusion flags (no direct "ALL"/"FEMALE"/"MALE" enum), so
# plannedSex is simply the set of Code entries whose flag is present.
CLASSIFIER_SEX: dict[str, dict] = {
    "includes-females": {"code": "C16576", "decode": "Female"},
    "includes-males":   {"code": "C20197", "decode": "Male"},
}

# ResearchStudy.classifier[].coding[].code (FEvIR CodeSystem 419455)  →
# StudyDesignPopulation.includesHealthySubjects boolean.
# Confirmed against Input/pilot_FHIR.json + app/config/mappings/04_classifier.yaml.
CLASSIFIER_HEALTHY_VOLUNTEERS: dict[str, bool] = {
    "includes-healthy-volunteers":     True,
    "does-not-include-healthy-volunteers": False,
}

# contained EvidenceVariable.classifier[].text prefix "Intervention Type: <DECODE>"
# marking a study-intervention EvidenceVariable export (see
# app/config/mappings/18_study_intervention_evidence_variable.yaml and readi_core
# ResearchContainedBuilder::buildInterventionEvidenceVariables()). Used by
# StudyInterventionsBuilder to tell these apart from the biomedical-concept/
# endpoint EvidenceVariable resources (14_evidence_variable.yaml), which carry
# no such classifier.
INTERVENTION_TYPE_CLASSIFIER_PREFIX = "Intervention Type: "

# <DECODE> suffix above (readi_core InterventionMappedTypes constant, e.g. "DRUG")
# → StudyIntervention.type Code. Mirrors readi_core
# InterventionMappedTypes::getInterventionTypeMapping() exactly; OTHER is
# intentionally omitted there too (commented out — no confirmed CDISC code).
INTERVENTION_TYPE: dict[str, dict] = {
    "DRUG":                {"code": "C1909",  "decode": "Pharmacologic Substance"},
    "DEVICE":              {"code": "C16830", "decode": "Medical Device"},
    "PROCEDURE":           {"code": "C98769", "decode": "Physical Medical Procedure"},
    "RADIATION":           {"code": "C15313", "decode": "Radiation Therapy"},
    "BEHAVIORAL":          {"code": "C15184", "decode": "Behavioral Intervention"},
    "GENETIC":             {"code": "C15238", "decode": "Gene Therapy"},
    "DIETARY_SUPPLEMENT":  {"code": "C1505",  "decode": "Dietary Supplement"},
    "COMBINATION_PRODUCT": {"code": "C54696", "decode": "Combination Product"},
    "DIAGNOSTIC_TEST":     {"code": "C18020", "decode": "Diagnostic Test"},
    "BIOLOGICAL":          {"code": "C307",   "decode": "Biological Agent"},
}

# Free-text unit word from ResearchStudy.classifier[].text (e.g. "Minimum Age:
# 18 Years") → StudyDesignPopulation.plannedAge.{min,max}Value.unit Code.
# Mirrors readi_core StandardCriteriaType::getDateUnitMapping(). Keyed by the
# singular lower-cased unit word — the caller strips a trailing "s" first.
AGE_UNIT: dict[str, dict] = {
    "year":   {"code": "C29848", "decode": "Year"},
    "month":  {"code": "C29846", "decode": "Month"},
    "week":   {"code": "C29844", "decode": "Week"},
    "day":    {"code": "C25301", "decode": "Day"},
    "hour":   {"code": "C25529", "decode": "Hour"},
    "minute": {"code": "C48154", "decode": "Minute"},
}

