# USDM 2 FHIR Tool

**USDM2FHIR** converts JSON files in **USDM** format (Unified Study Definition Model — CDISC standard for clinical studies) into **FHIR** resources (Fast Healthcare Interoperability Resources — HL7 standard).

The transformation is driven by a CSV mapping file (`Map/USDM2FHIR.csv`) that links JSONata paths from USDM to FHIR fields. The output is a `ResearchStudy` FHIR resource with `Group`, `Location`, and `EvidenceVariable` resources embedded in `contained`.

The tool must be seen as an example and starting point. The mappings stored as JSONata queries in the map directory can be adjusted according to the FHIR resource needs.

An example file in USDM format with corresponding expectedResponse extensions is available in the Input directory. 

The tool can be invoked by running the following command:

python CreateFhir.py --map Map/USDM2FHIR.csv --usdm Input/NCT01750580_limited_tagged_resp.json --output Output/MyNewFile.json

