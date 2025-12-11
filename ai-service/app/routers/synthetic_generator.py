from fastapi import APIRouter, HTTPException
from app.models.schemas import SyntheticLogRequest, SyntheticLogResponse
from app.services.synthetic.log_generator import LogGenerator

router = APIRouter(prefix='/ai/synthetic', tags=['Synthetic Data'])

@router.post('/generate', response_model=SyntheticLogResponse)
async def generate_synthetic_logs(request: SyntheticLogRequest):
    """Generate synthetic workflow logs based on scenario"""
    try:
        result = LogGenerator.generate(request.scenario_type, request.parameters)
        return SyntheticLogResponse(
            logs=result['logs'],
            metadata=result.get('metadata')
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
