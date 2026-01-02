import json
import logging
import re
from typing import Dict, List, Any, Optional
from app.services.claude.client import ClaudeClient
from app.services.claude.prompts import format_batch_pattern_analysis_prompt

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> str:
    """Extract JSON from text that might contain markdown code fences or extra text."""
    text = text.strip()
    json_fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_fence_match:
        return json_fence_match.group(1)
    json_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    return text

class NotesAnalyzer:
    """
    Analyzes patterns, trends, and hidden rules across ALL deviations with notes using Claude LLM.
    This is called AFTER rule-based deviation detection.

    Cost-effective approach:
    - Instead of analyzing each deviation individually (50 API calls for 50 deviations)
    - Makes 1-2 batch API calls to find patterns across ALL deviations together
    - Identifies trends, habits, hidden rules, and systemic issues
    """

    def __init__(self):
        """Initialize notes analyzer with Claude client."""
        try:
            self.claude_client = ClaudeClient()
            logger.info("NotesAnalyzer initialized with Claude")
        except ValueError as e:
            logger.warning(f"Claude client not available: {str(e)}")
            self.claude_client = None

    def analyze_pattern_batch(
        self,
        deviations_with_notes: List[Dict[str, Any]],
        max_batch_size: int = 100,
        statistical_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze patterns across ALL deviations in a single batch API call with statistical context.
        Works with or without notes - analyzes structured data patterns.

        This is the main method - finds trends, habits, hidden rules across all deviations.
        Much more cost-effective than individual analysis.

        Args:
            deviations_with_notes: List of ALL deviations (parameter name kept for compatibility)
            max_batch_size: Max deviations per API call (split if larger)
            statistical_context: Optional statistical analysis results to provide context

        Returns:
            Dict containing:
                - overall_summary: High-level summary
                - behavioral_patterns: Officer behavior patterns
                - hidden_rules: Informal practices discovered
                - systemic_issues: Recurring technical/process issues
                - time_patterns: When deviations spike
                - justification_analysis: Breakdown of reasons
                - risk_insights: Key risk indicators
                - recommendations: Actionable recommendations
                - api_calls_made: Number of API calls (for cost tracking)
        """
        if not self.claude_client:
            logger.warning("Claude client not available, skipping pattern analysis")
            return self._empty_pattern_analysis()

        if not deviations_with_notes:
            logger.info("No deviations to analyze")
            return self._empty_pattern_analysis()

        # Accept ALL deviations, not just ones with notes
        all_deviations = deviations_with_notes  # Keep parameter name for compatibility
        total_deviations = len(all_deviations)

        # Count how many have notes
        with_notes_count = sum(1 for d in all_deviations if d.get('notes'))
        logger.info(f"Analyzing patterns across {total_deviations} deviations ({with_notes_count} with notes, {total_deviations - with_notes_count} without)")

        if statistical_context:
            logger.info("Statistical context provided - enabling enhanced analysis")

        # If dataset is large, split into batches
        if total_deviations > max_batch_size:
            return self._analyze_large_batch(deviations_with_notes, max_batch_size, statistical_context)

        try:
            # Format prompt for batch analysis with optional statistical context
            prompt = format_batch_pattern_analysis_prompt(
                deviations_with_notes,
                statistical_context=statistical_context
            )

            # Single API call for all deviations!
            logger.info(f"Making 1 API call to analyze {total_deviations} deviations with statistical context")
            response = self.claude_client.generate(
                prompt=prompt,
                system="You are an expert at finding patterns and trends in compliance data. "
                       "You have been provided with comprehensive statistical analysis to guide your insights.",
                json_mode=True,
                max_tokens=4096  # Larger response for comprehensive analysis
            )

            # Extract and parse JSON response (handles markdown code fences)
            json_text = extract_json_from_text(response['text'])
            pattern_analysis = json.loads(json_text)

            # Fix recommendations if Claude returned objects instead of strings
            if 'recommendations' in pattern_analysis and isinstance(pattern_analysis['recommendations'], list):
                pattern_analysis['recommendations'] = [
                    rec if isinstance(rec, str) else f"[{rec.get('priority', 'NORMAL')}] {rec.get('recommendation', str(rec))}"
                    for rec in pattern_analysis['recommendations']
                ]

            # Validate response
            if not self._validate_pattern_analysis(pattern_analysis):
                logger.warning("Invalid pattern analysis structure from Claude")
                return self._empty_pattern_analysis()

            # Add metadata
            pattern_analysis['api_calls_made'] = 1
            pattern_analysis['deviations_analyzed'] = total_deviations

            logger.info(f"Pattern analysis complete with 1 API call for {total_deviations} deviations!")
            logger.info(f"Found {len(pattern_analysis.get('behavioral_patterns', []))} behavioral patterns")
            logger.info(f"Found {len(pattern_analysis.get('hidden_rules', []))} hidden rules")

            return pattern_analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {str(e)}")
            return self._empty_pattern_analysis()
        except Exception as e:
            logger.error(f"Error analyzing patterns with Claude: {str(e)}")
            return self._empty_pattern_analysis()

    def _analyze_large_batch(
        self,
        deviations_with_notes: List[Dict[str, Any]],
        batch_size: int,
        statistical_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle large datasets by splitting into multiple batches and aggregating results.

        Args:
            deviations_with_notes: All deviations with notes
            batch_size: Max deviations per API call
            statistical_context: Optional statistical analysis results

        Returns:
            Aggregated pattern analysis
        """
        total = len(deviations_with_notes)
        num_batches = (total + batch_size - 1) // batch_size

        logger.info(f"Large dataset: splitting {total} deviations into {num_batches} batches")

        batch_results = []
        for i in range(0, total, batch_size):
            batch = deviations_with_notes[i:i + batch_size]
            logger.info(f"Analyzing batch {len(batch_results) + 1}/{num_batches}")

            result = self.analyze_pattern_batch(
                batch,
                max_batch_size=batch_size * 2,
                statistical_context=statistical_context
            )
            batch_results.append(result)

        # Aggregate results from all batches
        return self._aggregate_batch_results(batch_results, total)

    def _aggregate_batch_results(
        self,
        batch_results: List[Dict[str, Any]],
        total_deviations: int
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple batches into a single analysis.

        Args:
            batch_results: List of pattern analysis results from each batch
            total_deviations: Total number of deviations analyzed

        Returns:
            Aggregated pattern analysis
        """
        # Combine patterns from all batches
        all_behavioral_patterns = []
        all_hidden_rules = []
        all_systemic_issues = []
        all_time_patterns = []
        all_risk_insights = []
        all_recommendations = []
        total_api_calls = 0

        for result in batch_results:
            all_behavioral_patterns.extend(result.get('behavioral_patterns', []))
            all_hidden_rules.extend(result.get('hidden_rules', []))
            all_systemic_issues.extend(result.get('systemic_issues', []))
            all_time_patterns.extend(result.get('time_patterns', []))
            all_risk_insights.extend(result.get('risk_insights', []))
            all_recommendations.extend(result.get('recommendations', []))
            total_api_calls += result.get('api_calls_made', 1)

        # Deduplicate and rank patterns
        # (In a production system, you'd use more sophisticated deduplication)

        return {
            'overall_summary': f'Aggregated analysis from {len(batch_results)} batches covering {total_deviations} deviations',
            'behavioral_patterns': all_behavioral_patterns[:10],  # Top 10
            'hidden_rules': all_hidden_rules[:5],  # Top 5
            'systemic_issues': all_systemic_issues[:5],
            'time_patterns': all_time_patterns[:5],
            'justification_analysis': {
                'note': 'Aggregated from multiple batches'
            },
            'risk_insights': all_risk_insights[:10],
            'recommendations': all_recommendations[:10],
            'api_calls_made': total_api_calls,
            'deviations_analyzed': total_deviations
        }

    def _validate_pattern_analysis(self, analysis: Dict[str, Any]) -> bool:
        """Validate that pattern analysis has required structure."""
        required_fields = [
            'overall_summary',
            'behavioral_patterns',
            'hidden_rules',
            'systemic_issues',
            'recommendations'
        ]
        return all(field in analysis for field in required_fields)

    def _empty_pattern_analysis(self) -> Dict[str, Any]:
        """Return empty pattern analysis when LLM is unavailable."""
        return {
            'overall_summary': 'Pattern analysis not available',
            'behavioral_patterns': [],
            'hidden_rules': [],
            'systemic_issues': [],
            'time_patterns': [],
            'justification_analysis': {
                'most_common_reasons': [],
                'justified_count': 0,
                'not_justified_count': 0,
                'unclear_count': 0
            },
            'risk_insights': ['LLM analysis unavailable - manual review recommended'],
            'recommendations': ['Enable Claude API for pattern analysis'],
            'api_calls_made': 0,
            'deviations_analyzed': 0
        }
