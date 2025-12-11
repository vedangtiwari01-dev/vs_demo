from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.models.schemas import ColumnMappingRequest, ColumnMappingResponse
from app.services.mapping.column_mapper import ColumnMapper
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/mapping", tags=["Column Mapping"])

# Initialize column mapper
column_mapper = ColumnMapper()

@router.post("/analyze-headers", response_model=ColumnMappingResponse)
async def analyze_headers(request: ColumnMappingRequest):
    """
    Analyze CSV headers and suggest column mappings using Claude LLM.

    This endpoint uses AI to understand the semantic meaning of CSV column names
    and maps them to standardized system fields for workflow log processing.
    """
    try:
        logger.info(f"Analyzing {len(request.headers)} headers for column mapping")

        # Call column mapper service
        mapping_result = column_mapper.analyze_headers(
            headers=request.headers,
            sample_rows=request.sample_rows if request.sample_rows else None
        )

        # Log summary
        mapped_count = len(mapping_result.get('mappings', {}))
        logger.info(f"Column mapping complete: {mapped_count} columns mapped")

        return ColumnMappingResponse(**mapping_result)

    except Exception as e:
        logger.error(f"Error analyzing headers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze column headers: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Check if column mapping service is healthy."""
    return {
        "status": "healthy",
        "service": "column_mapping",
        "claude_available": column_mapper.claude_client is not None
    }
