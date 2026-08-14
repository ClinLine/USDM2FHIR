"""
fhir_to_usdm.py
---------------
CLI command that converts a FHIR ResearchStudy JSON file to USDM format.

Usage
-----
python -m app.command.fhir_to_usdm --fhir Input/pilot_FHIR.json --output Output/USDM_output.json

Via Makefile:
    make execute_example_fhir_to_usdm
"""

import json

import click

from app.services.usdm_from_fhir.service import FhirToUsdmService


@click.command()
@click.option(
    "--fhir",
    required=True,
    type=click.Path(exists=True, readable=True),
    help="Path to the input FHIR ResearchStudy JSON file.",
)
@click.option(
    "--output",
    required=True,
    type=click.Path(writable=True),
    help="Path for the output USDM JSON file.",
)
def fhir_to_usdm(fhir: str, output: str) -> None:
    """Convert a FHIR ResearchStudy JSON to USDM format."""
    with open(fhir, "r") as f:
        fhir_data = json.load(f)

    usdm_data = FhirToUsdmService().build(fhir_data)

    with open(output, "w") as f:
        json.dump(usdm_data, f, indent=2)

    click.echo(f"USDM output saved to {output}")


if __name__ == "__main__":
    fhir_to_usdm()

