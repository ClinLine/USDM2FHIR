PYTHON = venv/bin/python
PIP = venv/bin/pip
IMAGE_NAME = usdm2fhir
REGISTRY = ghcr.io/efrosionelu/usdm2fhir
PORT = 8000
FHIR_VALIDATOR = $(shell which fhir-validator 2>/dev/null || echo /Users/fybromania/Library/Python/3.9/bin/fhir-validator)

.PHONY: setup execute_example execute_example_fhir_to_usdm run jsonata-inspect jsonata-query yaml_to_csv docker-build docker-run docker-stop docker-push validate validate-usdm run

setup:
	python3 -m venv venv
	$(PIP) install -r requirements.txt
	@echo "✅ venv creat si dependentele instalate! Ruleaza: source venv/bin/activate"

execute_example:
	$(PYTHON) CreateFhir.py --map Map/USDM2FHIR.csv --usdm Input/NCT01750580_limited_tagged_resp.json --output Output/MyNewFile.json

execute_example_fhir_to_usdm:
	$(PYTHON) -m app.command.fhir_to_usdm --fhir Input/pilot_FHIR.json --output Output/USDM_output.json

# Validate Output/USDM_output.json against the SDR conformance service (URL from .env)
# Usage: make validate-usdm
# Optional: make validate-usdm FILE=Output/USDM_output.json FLAGS="--json"
validate_usdm:
	$(PYTHON) -m app.command.validate_usdm --file $(or $(FILE),Output/USDM_output.json) $(FLAGS)
# Merge all YAML mapping files into Map/USDM2FHIR.csv
# Usage: make yaml_to_csv
# Optional: make yaml_to_csv MAPPINGS_DIR=app/config/mappings OUTPUT=Map/USDM2FHIR.csv
yaml_to_csv:
	$(PYTHON) -m app.command.yaml_to_csv \
		--mappings-dir $(or $(MAPPINGS_DIR),app/config/mappings) \
		--output $(or $(OUTPUT),Map/USDM2FHIR.csv)

run:
	$(PYTHON) -m uvicorn main:app --reload --host 0.0.0.0 --port $(PORT)

# Evaluează o expresie JSONata și afișează metadata rezultatului.
# Utilizare: make jsonata-inspect EXPR="study.versions"
# Flags opționali: FLAGS="--json"  sau  FLAGS="--raw"
jsonata-inspect:
	$(PYTHON) -m app.command.jsonata_inspect "$(EXPR)" $(FLAGS)

# Evaluează o expresie JSONata și returnează rezultatul real (truncat la 250 chars dacă e prea mare).
# Utilizare: make jsonata-query EXPR="study.versions[0].versionIdentifier"
# Flags opționali: FLAGS="--json"
jsonata-query:
	$(PYTHON) -m app.command.jsonata_query "$(EXPR)" $(FLAGS)

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run:
	docker run --rm -p $(PORT):8000 --name $(IMAGE_NAME) $(IMAGE_NAME)

docker-stop:
	docker stop $(IMAGE_NAME)

docker-push:
	docker build -t $(REGISTRY):latest .
	docker push $(REGISTRY):latest
# Requires fhir-validator installed locally (Python <3.12 only):
#   pip3 install fhir-validator
# Also requires the FHIR R4 schema in schemas/r4/fhir.schema.json — download with:
#   mkdir -p schemas/r4 && curl -L https://www.hl7.org/fhir/R4/fhir.schema.json.zip -o /tmp/fhir.schema.json.zip && unzip -o /tmp/fhir.schema.json.zip -d schemas/r4/
validate:
	$(FHIR_VALIDATOR) --path ./Output/MyNewFile.json --action validate
claude_unsafe:
	claude --allow-dangerously-skip-permissions;