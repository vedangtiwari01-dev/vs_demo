from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta
from .rule_parser import RuleParser

class DocumentationChecker:
    """
    Checks documentation compliance deviations.

    DEVIATION TYPES DETECTED:
    - missing_mandatory_document: Required document not submitted
    - expired_document_used: Document used beyond expiry date
    - legal_clearance_missing: Legal/title clearance not completed
    - collateral_docs_incomplete: Collateral documentation incomplete

    STRICT MODE: Only validates if SOP explicitly defines documentation requirements.
    If no documentation rules exist, returns empty list (no validation, no false positives).
    """

    @staticmethod
    def check_documentation(logs: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check documentation compliance deviations.

        STRICT MODE: Only validates based on explicit SOP requirements.
        If no documentation rules defined, skips validation entirely.

        Args:
            logs: Workflow logs with optional fields (document_type, document_status, document_expiry_date)
            rules: SOP rules (documentation type)

        Returns:
            List of documentation deviations detected
        """
        deviations = []

        # Extract documentation requirements from SOP
        doc_requirements = RuleParser.extract_document_requirements(rules)

        # STRICT MODE: If no documentation rules defined in SOP, skip validation
        if not doc_requirements['mandatory_docs'] and not doc_requirements['product_specific']:
            return deviations

        # Get mandatory documents
        mandatory_docs = doc_requirements['mandatory_docs']

        # Group logs by case_id
        cases = defaultdict(list)
        for log in logs:
            if 'case_id' in log:  # DEFENSIVE: Skip logs without case_id
                cases[log['case_id']].append(log)

        # Check each case
        for case_id, case_logs in cases.items():
            officer_id = case_logs[0].get('officer_id', 'unknown')
            timestamp = case_logs[0].get('timestamp')

            # Collect documentation data
            documents_submitted = set()
            expired_docs = []
            step_names = []

            for log in case_logs:
                step_names.append(log.get('step_name', ''))

                # Track documents
                if 'document_type' in log and log['document_type']:
                    doc_type = str(log['document_type']).lower().replace(' ', '_')
                    doc_status = str(log.get('document_status', '')).lower()

                    if doc_status in ['submitted', 'verified', 'approved', 'received']:
                        documents_submitted.add(doc_type)

                    # Check expiry
                    if 'document_expiry_date' in log and log['document_expiry_date']:
                        try:
                            expiry_str = log['document_expiry_date']
                            # Try multiple date formats
                            expiry_date = None
                            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S']:
                                try:
                                    expiry_date = datetime.strptime(expiry_str.split()[0], fmt)
                                    break
                                except (ValueError, AttributeError):
                                    continue

                            if expiry_date:
                                log_date = datetime.fromisoformat(log.get('timestamp', '').split('.')[0].replace('Z', ''))
                                if expiry_date < log_date:
                                    expired_docs.append({
                                        'doc_type': doc_type,
                                        'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                                        'used_date': log_date.strftime('%Y-%m-%d')
                                    })
                        except Exception:
                            # Date parsing failed - skip expiry check
                            pass

                # Track legal clearance
                if 'legal_clearance_status' in log:
                    legal_status = str(log['legal_clearance_status']).lower()
                    if legal_status in ['completed', 'cleared', 'approved']:
                        documents_submitted.add('legal_clearance')

                # Track collateral docs
                if 'collateral_docs_status' in log:
                    collateral_status = str(log['collateral_docs_status']).lower()
                    if collateral_status in ['completed', 'verified', 'approved']:
                        documents_submitted.add('collateral_docs')

            # Determine if case progressed to approvals
            has_approval_step = any('approval' in step.lower() for step in step_names)
            has_disbursement_step = any('disbursement' in step.lower() or 'disburse' in step.lower() for step in step_names)

            # Check 1: Missing mandatory documents (if case progressed)
            if has_approval_step or has_disbursement_step:
                missing_docs = mandatory_docs - documents_submitted

                if missing_docs:
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': timestamp,
                        'deviation_type': 'missing_mandatory_document',
                        'severity': 'high',
                        'description': f'Case progressed with missing mandatory documents: {", ".join(missing_docs)}',
                        'expected_behavior': f'All mandatory documents required: {", ".join(mandatory_docs)}',
                        'actual_behavior': f'Missing: {", ".join(missing_docs)}',
                        'context': {
                            'missing_docs': list(missing_docs),
                            'submitted_docs': list(documents_submitted),
                            'has_approval': has_approval_step
                        }
                    })

            # Check 2: Expired documents used
            if expired_docs:
                for expired in expired_docs:
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': timestamp,
                        'deviation_type': 'expired_document_used',
                        'severity': 'high',
                        'description': f'Expired document used: {expired["doc_type"]} (expired: {expired["expiry_date"]}, used: {expired["used_date"]})',
                        'expected_behavior': 'Only valid, non-expired documents should be accepted',
                        'actual_behavior': f'Document expired on {expired["expiry_date"]} but used on {expired["used_date"]}',
                        'context': expired
                    })

            # Check 3: Legal clearance missing (only if SOP explicitly requires it)
            if 'legal_clearance' in mandatory_docs:
                if has_disbursement_step and 'legal_clearance' not in documents_submitted:
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': timestamp,
                        'deviation_type': 'legal_clearance_missing',
                        'severity': 'critical',
                        'description': 'Loan disbursed without required legal/title clearance',
                        'expected_behavior': 'Legal clearance required before disbursement (per SOP)',
                        'actual_behavior': 'Disbursement step completed without legal clearance',
                        'context': {
                            'legal_clearance_completed': False
                        }
                    })

            # Check 4: Collateral documentation incomplete (only if SOP explicitly requires it)
            if 'collateral_docs' in mandatory_docs:
                if has_disbursement_step and 'collateral_docs' not in documents_submitted:
                    deviations.append({
                        'case_id': case_id,
                        'officer_id': officer_id,
                        'timestamp': timestamp,
                        'deviation_type': 'collateral_docs_incomplete',
                        'severity': 'critical',
                        'description': 'Loan disbursed with incomplete collateral documentation',
                        'expected_behavior': 'Complete collateral documentation required before disbursement (per SOP)',
                        'actual_behavior': 'Disbursement completed without verified collateral docs',
                        'context': {
                            'collateral_docs_complete': False
                        }
                    })

        return deviations
