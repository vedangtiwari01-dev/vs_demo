from fastapi import APIRouter, HTTPException
from app.models.schemas import SOPParseRequest, SOPParseResponse, RuleExtractionRequest, RuleExtractionResponse
from app.services.nlp.sop_extractor import SOPExtractor
from app.services.nlp.rule_parser import RuleParser

router = APIRouter(prefix='/ai/sop', tags=['SOP Processing'])

@router.post('/parse', response_model=SOPParseResponse)
async def parse_sop(request: SOPParseRequest):
    """Parse SOP document and extract text"""
    try:
        result = SOPExtractor.extract(request.file_path, request.file_type)
        return SOPParseResponse(
            text=result['text'],
            metadata=result.get('metadata')
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post('/extract-rules', response_model=RuleExtractionResponse)
async def extract_rules(request: RuleExtractionRequest):
    """Extract rules from SOP text"""
    try:
        parser = RuleParser()
        rules = parser.extract_rules(request.text)
        return RuleExtractionResponse(rules=rules)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
