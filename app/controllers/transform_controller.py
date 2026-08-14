from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse

from app.services.transform_service import transform_usdm_to_fhir, DEFAULT_MAP_FILE
from app.services.usdm_from_fhir.service import FhirToUsdmService

router = APIRouter()


@router.post("/transform", tags=["Transform"])
def transform(
    body: Any = Body(..., description="JSON payload (USDM or FHIR, depending on input_format)"),
    input_format: Literal["usdm", "fhir"] = Query(default="usdm", description="Input format: 'usdm' or 'fhir'"),
    output_format: Literal["usdm", "fhir"] = Query(default="fhir", description="Output format: 'usdm' or 'fhir'"),
    resource_id: str = Query(default="123", alias="id", description="FHIR resource ID (used only for usdm→fhir)"),
    version: str = Query(default="1", description="FHIR versionId (used only for usdm→fhir)"),
    updated: str = Query(default=None, description="FHIR meta.lastUpdated ISO 8601 (used only for usdm→fhir)"),
):
    """
    Transforms a JSON between USDM and FHIR formats.

    - `input_format=usdm` + `output_format=fhir` (default): USDM → FHIR
    - `input_format=fhir` + `output_format=usdm`: FHIR → USDM
    """
    try:
        if input_format == "usdm" and output_format == "fhir":
            result = transform_usdm_to_fhir(
                usdm_data=body,
                map_file=DEFAULT_MAP_FILE,
                resource_id=resource_id,
                version=version,
                updated=updated,
            )
        elif input_format == "fhir" and output_format == "usdm":
            result = FhirToUsdmService().build(body)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported combination: input_format='{input_format}', output_format='{output_format}'. "
                       f"Valid combinations: usdm→fhir, fhir→usdm.",
            )
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

