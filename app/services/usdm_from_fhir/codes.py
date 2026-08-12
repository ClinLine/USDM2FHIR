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

# ISO 639-1 language names for the locales readi_core supports (see LocaleType::ISO_639_1
# / LocaleType::ALL_TYPES in readi_core). Used as the `decode` of a translation's
# valueCode when reconstructing the USDM "languages" extension from FHIR.
ISO_639_1: dict[str, str] = {
    "bg": "Bulgarian", "hr": "Croatian", "cs": "Czech", "da": "Danish", "nl": "Dutch",
    "en": "English", "et": "Estonian", "fi": "Finnish", "fr": "French", "de": "German",
    "el": "Greek", "hu": "Hungarian", "ga": "Irish", "it": "Italian", "lv": "Latvian",
    "lt": "Lithuanian", "mt": "Maltese", "pl": "Polish", "pt": "Portuguese", "ro": "Romanian",
    "sk": "Slovak", "sl": "Slovenian", "es": "Spanish", "sv": "Swedish",
}

# Default SNOMED CT version used when building condition/indication codes
# (the FHIR payload does not carry a version, so we fall back to this constant).
SNOMED_CODE_SYSTEM = "Systematic Nomenclature of Medicine - Clinical Terms (IHTSDO)"
SNOMED_CODE_SYSTEM_VERSION = "2025-02-01"

# Maps FHIR coding.system URIs → USDM codeSystem display names.
# Used by builders that construct Code objects from non-CDISC FHIR codings
# (e.g. SNOMED CT condition codes on eligibility criteria).
FHIR_SYSTEM_TO_USDM_CODE_SYSTEM: dict[str, str] = {
    # --- Terminology systems ---
    "http://snomed.info/sct":                                                         "Systematic Nomenclature of Medicine - Clinical Terms (IHTSDO)",
    "http://loinc.org":                                                               "Logical Observation Identifiers Names and Codes (LOINC)",
    "http://www.nlm.nih.gov/research/umls/rxnorm":                                   "RxNorm",
    # --- ICD families ---
    "http://hl7.org/fhir/sid/icd-10-cm":                                             "International Classification of Diseases, 10th Revision, Clinical Modification (ICD-10-CM)",
    "http://hl7.org/fhir/sid/icd-10-pcs":                                            "International Classification of Diseases, 10th Revision, Procedure Coding System (ICD-10-PCS)",
    "http://hl7.org/fhir/sid/icd-9-cm":                                              "International Classification of Diseases, 9th Revision, Clinical Modification (ICD-9-CM)",
    "urn:oid:2.16.840.1.113883.6.43.1":                                              "International Classification of Diseases for Oncology, Third Edition (ICD-O-3)",
    # --- CMS / payer code sets ---
    "https://www.cms.gov/Medicare/Coding/HCPCSReleaseCodeSets":                      "Healthcare Common Procedure Coding System (HCPCS)",
    "https://www.cms.gov/Medicare/Medicare-Fee-for-Service-Payment/HospitalOutpatientPPS": "Ambulatory Payment Classification (APC)",
    "https://www.cms.gov/Medicare/Medicare-Fee-for-Service-Payment/AcuteInpatientPPS":     "Diagnosis-Related Group (DRG)",
    # --- Research / registry / national code sets ---
    "https://www.naaccr.org":                "North American Association of Central Cancer Registries (NAACCR)",
    "https://ohdsi.org":                     "Observational Medical Outcomes Partnership Extension (OMOP)",
    "https://allofus.nih.gov":               "All of Us Research Program Participant-Provided Information (PPI)",
    "https://biobank.ctsu.ox.ac.uk":         "UK Biobank",
    "https://classbrowser.nhs.uk":           "OPCS Classification of Interventions and Procedures Version 4 (OPCS-4)",
    "http://read.info/readv2":               "Read Codes Version 2 (CTV2)",
    "https://www.unmc.edu/nebraska-lexicon": "Nebraska Lexicon",
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
    "short-title":    {"code": "C207615", "decode": "Brief Study Title"},
#     "primary":       {"code": "C207616", "decode": "Official Study Title"},
    "official":       {"code": "C207616", "decode": "Official Study Title"},
    "plain-language": {"code": "C207617", "decode": "Public Study Title"},
    "scientific":     {"code": "C207618", "decode": "Scientific Study Title"},
    "acronym":        {"code": "C207646", "decode": "Study Acronym"},
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
    "SEVCO:01005": {"code": "C93043", "decode": "Non-Randomized"},
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

# ResearchStudy.associatedParty[].classifier[].text (sponsor subtype, upper-cased)
# → Organization.type Code.
# Mirrors readi_core SponsorsMappedTypes::getStudyTypeMapping():
#   OTHER          → C17998  Unknown
#   FED / NIH      → C199144 Government Institute
#   INDUSTRY       → EXT0015 Industry
# Any other / absent classifier → falls back to ORG_TYPE_UNKNOWN above.
ORG_TYPE_BY_SPONSOR_SUBTYPE: dict[str, dict] = {
    "OTHER":    {"code": "C17998",  "decode": "Unknown"},
    "FED":      {"code": "C199144", "decode": "Government Institute"},
    "NIH":      {"code": "C199144", "decode": "Government Institute"},
    "INDUSTRY": {"code": "EXT0015", "decode": "Industry"},
}

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



# ---------------------------------------------------------------------------
# Country name → ISO 3166-1 alpha-3 code (managedSites.country)
# ---------------------------------------------------------------------------

# Ported 1:1 from readi_core's CountryType::COUNTRY_ALPHA3_MAP
# (src/Doctrine/ORM/Type/CountryType.php) — country_name → alpha3, mirrors
# UsdmBuildContext::buildManagedSites() / CountryType::getAlpha3ForCountry()
# (name → alpha3, the same direction, since FHIR only carries the free-text
# country name and USDM's managedSites[].country needs both the alpha3 code
# and the decode). Matched case-insensitively via resolve_country_alpha3().
COUNTRY_NAME_TO_ALPHA3: dict[str, str] = {
    'Afghanistan': 'AFG',
    'Åland Islands': 'ALA',
    'Albania': 'ALB',
    'Algeria': 'DZA',
    'American Samoa': 'ASM',
    'Andorra': 'AND',
    'Angola': 'AGO',
    'Anguilla': 'AIA',
    'Antarctica': 'ATA',
    'Antigua and Barbuda': 'ATG',
    'Argentina': 'ARG',
    'Armenia': 'ARM',
    'Aruba': 'ABW',
    'Australia': 'AUS',
    'Austria': 'AUT',
    'Azerbaijan': 'AZE',
    'Bahamas (the)': 'BHS',
    'Bahrain': 'BHR',
    'Bangladesh': 'BGD',
    'Barbados': 'BRB',
    'Belarus': 'BLR',
    'Belgium': 'BEL',
    'Belize': 'BLZ',
    'Benin': 'BEN',
    'Bermuda': 'BMU',
    'Bhutan': 'BTN',
    'Bolivia (Plurinational State of)': 'BOL',
    'Bonaire, Sint Eustatius and Saba': 'BES',
    'Bosnia and Herzegovina': 'BIH',
    'Botswana': 'BWA',
    'Bouvet Island': 'BVT',
    'Brazil': 'BRA',
    'British Indian Ocean Territory (the)': 'IOT',
    'Brunei Darussalam': 'BRN',
    'Bulgaria': 'BGR',
    'Burkina Faso': 'BFA',
    'Burundi': 'BDI',
    'Cabo Verde': 'CPV',
    'Cambodia': 'KHM',
    'Cameroon': 'CMR',
    'Canada': 'CAN',
    'Cayman Islands (the)': 'CYM',
    'Central African Republic (the)': 'CAF',
    'Chad': 'TCD',
    'Chile': 'CHL',
    'China': 'CHN',
    'Christmas Island': 'CXR',
    'Cocos (Keeling) Islands (the)': 'CCK',
    'Colombia': 'COL',
    'Comoros (the)': 'COM',
    'Congo (the Democratic Republic of the)': 'COD',
    'Congo (the)': 'COG',
    'Cook Islands (the)': 'COK',
    'Costa Rica': 'CRI',
    "Côte d'Ivoire": 'CIV',
    'Croatia': 'HRV',
    'Cuba': 'CUB',
    'Curaçao': 'CUW',
    'Cyprus': 'CYP',
    'Czechia': 'CZE',
    'Denmark': 'DNK',
    'Djibouti': 'DJI',
    'Dominica': 'DMA',
    'Dominican Republic (the)': 'DOM',
    'Ecuador': 'ECU',
    'Egypt': 'EGY',
    'El Salvador': 'SLV',
    'Equatorial Guinea': 'GNQ',
    'Eritrea': 'ERI',
    'Estonia': 'EST',
    'Eswatini': 'SWZ',
    'Ethiopia': 'ETH',
    'Falkland Islands (the) [Malvinas]': 'FLK',
    'Faroe Islands (the)': 'FRO',
    'Fiji': 'FJI',
    'Finland': 'FIN',
    'France': 'FRA',
    'French Guiana': 'GUF',
    'French Polynesia': 'PYF',
    'French Southern Territories (the)': 'ATF',
    'Gabon': 'GAB',
    'Gambia (the)': 'GMB',
    'Georgia': 'GEO',
    'Germany': 'DEU',
    'Ghana': 'GHA',
    'Gibraltar': 'GIB',
    'Greece': 'GRC',
    'Greenland': 'GRL',
    'Grenada': 'GRD',
    'Guadeloupe': 'GLP',
    'Guam': 'GUM',
    'Guatemala': 'GTM',
    'Guernsey': 'GGY',
    'Guinea': 'GIN',
    'Guinea-Bissau': 'GNB',
    'Guyana': 'GUY',
    'Haiti': 'HTI',
    'Heard Island and McDonald Islands': 'HMD',
    'Holy See (the)': 'VAT',
    'Honduras': 'HND',
    'Hong Kong': 'HKG',
    'Hungary': 'HUN',
    'Iceland': 'ISL',
    'India': 'IND',
    'Indonesia': 'IDN',
    'Iran (Islamic Republic of)': 'IRN',
    'Iraq': 'IRQ',
    'Ireland': 'IRL',
    'Isle of Man': 'IMN',
    'Israel': 'ISR',
    'Italy': 'ITA',
    'Jamaica': 'JAM',
    'Japan': 'JPN',
    'Jersey': 'JEY',
    'Jordan': 'JOR',
    'Kazakhstan': 'KAZ',
    'Kenya': 'KEN',
    'Kiribati': 'KIR',
    "Korea (the Democratic People's Republic of)": 'PRK',
    'Korea (the Republic of)': 'KOR',
    'Kuwait': 'KWT',
    'Kyrgyzstan': 'KGZ',
    "Lao People's Democratic Republic (the)": 'LAO',
    'Latvia': 'LVA',
    'Lebanon': 'LBN',
    'Lesotho': 'LSO',
    'Liberia': 'LBR',
    'Libya': 'LBY',
    'Liechtenstein': 'LIE',
    'Lithuania': 'LTU',
    'Luxembourg': 'LUX',
    'Macao': 'MAC',
    'Republic of North Macedonia': 'MKD',
    'Madagascar': 'MDG',
    'Malawi': 'MWI',
    'Malaysia': 'MYS',
    'Maldives': 'MDV',
    'Mali': 'MLI',
    'Malta': 'MLT',
    'Marshall Islands (the)': 'MHL',
    'Martinique': 'MTQ',
    'Mauritania': 'MRT',
    'Mauritius': 'MUS',
    'Mayotte': 'MYT',
    'Mexico': 'MEX',
    'Micronesia (Federated States of)': 'FSM',
    'Moldova (the Republic of)': 'MDA',
    'Monaco': 'MCO',
    'Mongolia': 'MNG',
    'Montenegro': 'MNE',
    'Montserrat': 'MSR',
    'Morocco': 'MAR',
    'Mozambique': 'MOZ',
    'Myanmar': 'MMR',
    'Namibia': 'NAM',
    'Nauru': 'NRU',
    'Nepal': 'NPL',
    'Netherlands (the)': 'NLD',
    'New Caledonia': 'NCL',
    'New Zealand': 'NZL',
    'Nicaragua': 'NIC',
    'Niger (the)': 'NER',
    'Nigeria': 'NGA',
    'Niue': 'NIU',
    'Norfolk Island': 'NFK',
    'Northern Mariana Islands (the)': 'MNP',
    'Norway': 'NOR',
    'Oman': 'OMN',
    'Pakistan': 'PAK',
    'Palau': 'PLW',
    'Palestine, State of': 'PSE',
    'Panama': 'PAN',
    'Papua New Guinea': 'PNG',
    'Paraguay': 'PRY',
    'Peru': 'PER',
    'Philippines (the)': 'PHL',
    'Pitcairn': 'PCN',
    'Poland': 'POL',
    'Portugal': 'PRT',
    'Puerto Rico': 'PRI',
    'Qatar': 'QAT',
    'Réunion': 'REU',
    'Romania': 'ROU',
    'Russian Federation (the)': 'RUS',
    'Rwanda': 'RWA',
    'Saint Barthélemy': 'BLM',
    'Saint Helena, Ascension and Tristan da Cunha': 'SHN',
    'Saint Kitts and Nevis': 'KNA',
    'Saint Lucia': 'LCA',
    'Saint Martin (French part)': 'MAF',
    'Saint Pierre and Miquelon': 'SPM',
    'Saint Vincent and the Grenadines': 'VCT',
    'Samoa': 'WSM',
    'San Marino': 'SMR',
    'Sao Tome and Principe': 'STP',
    'Saudi Arabia': 'SAU',
    'Senegal': 'SEN',
    'Serbia': 'SRB',
    'Seychelles': 'SYC',
    'Sierra Leone': 'SLE',
    'Singapore': 'SGP',
    'Sint Maarten (Dutch part)': 'SXM',
    'Slovakia': 'SVK',
    'Slovenia': 'SVN',
    'Solomon Islands': 'SLB',
    'Somalia': 'SOM',
    'South Africa': 'ZAF',
    'South Georgia and the South Sandwich Islands': 'SGS',
    'South Sudan': 'SSD',
    'Spain': 'ESP',
    'Sri Lanka': 'LKA',
    'Sudan (the)': 'SDN',
    'Suriname': 'SUR',
    'Svalbard and Jan Mayen': 'SJM',
    'Sweden': 'SWE',
    'Switzerland': 'CHE',
    'Syrian Arab Republic': 'SYR',
    'Taiwan (Province of China)': 'TWN',
    'Tajikistan': 'TJK',
    'Tanzania, United Republic of': 'TZA',
    'Thailand': 'THA',
    'Timor-Leste': 'TLS',
    'Togo': 'TGO',
    'Tokelau': 'TKL',
    'Tonga': 'TON',
    'Trinidad and Tobago': 'TTO',
    'Tunisia': 'TUN',
    'Turkey': 'TUR',
    'Turkmenistan': 'TKM',
    'Turks and Caicos Islands (the)': 'TCA',
    'Tuvalu': 'TUV',
    'Uganda': 'UGA',
    'Ukraine': 'UKR',
    'United Arab Emirates (the)': 'ARE',
    'United Kingdom of Great Britain and Northern Ireland (the)': 'GBR',
    'United States Minor Outlying Islands (the)': 'UMI',
    'United States of America (the)': 'USA',
    'Uruguay': 'URY',
    'Uzbekistan': 'UZB',
    'Vanuatu': 'VUT',
    'Venezuela (Bolivarian Republic of)': 'VEN',
    'Viet Nam': 'VNM',
    'Virgin Islands (British)': 'VGB',
    'Virgin Islands (U.S.)': 'VIR',
    'Wallis and Futuna': 'WLF',
    'Western Sahara': 'ESH',
    'Yemen': 'YEM',
    'Zambia': 'ZMB',
    'Zimbabwe': 'ZWE',
}

# Short country names as they actually appear in real-world FHIR
# Location.address.country (e.g. readi_core's Address::getCountry(), sourced
# from ClinicalTrials.gov/CTIS) that don't exact-match the official ISO
# long-form names above (confirmed mismatches from Input/pilot_FHIR.json:
# "United States", "United Kingdom", "South Korea" — the rest are reasonable
# extensions of the same pattern, not individually confirmed against data).
# Not exhaustive by design — resolve_country_alpha3() falls back to None
# (managedSites skipped for that org) rather than guessing.
COUNTRY_NAME_ALIASES: dict[str, str] = {
    "united states":     "United States of America (the)",
    "usa":               "United States of America (the)",
    "uk":                "United Kingdom of Great Britain and Northern Ireland (the)",
    "united kingdom":    "United Kingdom of Great Britain and Northern Ireland (the)",
    "south korea":       "Korea (the Republic of)",
    "north korea":       "Korea (the Democratic People's Republic of)",
    "russia":            "Russian Federation (the)",
    "vietnam":           "Viet Nam",
    "laos":              "Lao People's Democratic Republic (the)",
    "iran":              "Iran (Islamic Republic of)",
    "syria":             "Syrian Arab Republic",
    "ivory coast":       "Côte d'Ivoire",
    "bolivia":           "Bolivia (Plurinational State of)",
    "moldova":           "Moldova (the Republic of)",
    "venezuela":         "Venezuela (Bolivarian Republic of)",
    "tanzania":          "Tanzania, United Republic of",
    "north macedonia":   "Republic of North Macedonia",
    "macedonia":         "Republic of North Macedonia",
    "czech republic":    "Czechia",
    "netherlands":       "Netherlands (the)",
    "philippines":       "Philippines (the)",
    "brunei":            "Brunei Darussalam",
}

_COUNTRY_NAME_TO_ALPHA3_LOWER: dict[str, str] = {
    name.lower(): alpha3 for name, alpha3 in COUNTRY_NAME_TO_ALPHA3.items()
}


def resolve_country_alpha3(country_name: str | None) -> str | None:
    """
    FHIR Location.address.country (free-text country name) → ISO alpha-3 code.
    Mirrors CountryType::getAlpha3ForCountry() (case-insensitive exact match
    against the official ISO long-form name), plus COUNTRY_NAME_ALIASES for
    the short forms real FHIR data actually uses. Returns None when nothing
    matches — callers should skip the field, not guess.
    """
    if not country_name:
        return None
    key = country_name.strip().lower()
    alpha3 = _COUNTRY_NAME_TO_ALPHA3_LOWER.get(key)
    if alpha3 is not None:
        return alpha3
    alias = COUNTRY_NAME_ALIASES.get(key)
    if alias is not None:
        return _COUNTRY_NAME_TO_ALPHA3_LOWER.get(alias.lower())
    return None


# Organization.type Code for a study-site organization whose name matches the
# "research hospital" / "research institute" heuristic — mirrors readi_core
# OrganizationsSectionBuilder::buildLocationOrganizations() (and the identical
# inline C18240 array in buildOwnerOrganization() / createOrganizationObjectFromSponsor()).
ORG_TYPE_ACADEMIC_INSTITUTION: dict = {"code": "C18240", "decode": "Academic Institution"}
