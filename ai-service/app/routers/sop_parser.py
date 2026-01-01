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

@router.post('/extract-rules', response_model=RuleExtractionResponse, response_model_by_alias=False)
async def extract_rules(request: RuleExtractionRequest, use_llm: bool = True):
    """
    Extract rules from SOP text.

    IMPORTANT: response_model_by_alias=False ensures the response is serialized
    using field names (rule_type, rule_description) NOT aliases (type, description),
    so the backend receives the correct field names.

    Args:
        use_llm: If True, uses Claude LLM for intelligent extraction (default).
                 If False, uses regex-based parser.
    """
    try:
        from app.services.nlp.llm_rule_parser import LLMRuleParser

        if use_llm:
            # Use LLM-based parser (recommended)
            parser = LLMRuleParser()
            result = parser.extract_rules(request.text, use_llm=True, fallback_on_error=True)
            return RuleExtractionResponse(rules=result['rules'])
        else:
            # Use regex-based parser
            parser = RuleParser()
            rules = parser.extract_rules(request.text)
            return RuleExtractionResponse(rules=rules)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
