"""
Regulatory Aggregator for Portfolio-Level Compliance

Aggregates across multiple cases to detect:
- Customer exposure limits (single customer exposure)
- Sector concentration risk
- Branch concentration
- Regulatory threshold breaches

These violations can only be detected by looking at multiple cases together.

Author: Claude Code
"""

from typing import List, Dict, Any
from collections import defaultdict


class RegulatoryAggregator:
    """
    Checks regulatory compliance across entire portfolio.

    Detects violations that span multiple cases:
    - Customer total exposure exceeding regulatory limits
    - Sector concentration exceeding safe limits
    - Branch handling too much volume
    - Single borrower limits
    """

    @staticmethod
    def evaluate(
        logs: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        limits: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Main entry point for regulatory aggregation.

        Args:
            logs: All workflow logs across all cases
            rules: Regulatory rules (currently not used, reserved for future)
            limits: Regulatory limits configuration with keys:
                - total_capital: Total capital base for exposure calculations
                - customer_exposure_percent: Max % of capital to single customer
                - group_exposure_percent: Max % to related group
                - sector_concentration_percent: Max % to single sector
                - branch_concentration_percent: Max % handled by single branch

        Returns:
            List of regulatory deviations
        """
        deviations = []

        # CRITICAL FIX: Get fallback officer_id from first log (for foreign key constraint)
        # Never use 'unknown' as it doesn't exist in officers table
        fallback_officer_id = None
        for log in logs:
            if log.get('officer_id'):
                fallback_officer_id = log.get('officer_id')
                break

        # Skip regulatory analysis if no officer_id found in ANY log
        if not fallback_officer_id:
            return deviations

        # Run different aggregation checks
        deviations.extend(
            RegulatoryAggregator._check_customer_exposure(logs, limits, fallback_officer_id)
        )
        deviations.extend(
            RegulatoryAggregator._check_sector_concentration(logs, limits, fallback_officer_id)
        )
        deviations.extend(
            RegulatoryAggregator._check_branch_concentration(logs, limits, fallback_officer_id)
        )

        return deviations

    @staticmethod
    def _check_customer_exposure(
        logs: List[Dict[str, Any]],
        limits: Dict[str, Any],
        fallback_officer_id: str
    ) -> List[Dict[str, Any]]:
        """
        Check if any customer's total exposure exceeds regulatory limit.

        Regulatory Rule: Total exposure to single customer < X% of capital
        Common limit: 25% of capital

        Args:
            logs: All workflow logs
            limits: Configuration with total_capital and customer_exposure_percent
            fallback_officer_id: Valid officer_id to use if none found in logs

        Returns:
            List of customer exposure deviations
        """
        deviations = []

        # Aggregate by customer_id
        customer_totals = defaultdict(lambda: {'total': 0, 'cases': [], 'officer_id': None})

        for log in logs:
            customer_id = log.get('customer_id')
            loan_amount = log.get('loan_amount_sanctioned')

            if customer_id and loan_amount:
                try:
                    loan_amount_float = float(loan_amount)
                    customer_totals[customer_id]['total'] += loan_amount_float
                    if log.get('case_id') not in customer_totals[customer_id]['cases']:
                        customer_totals[customer_id]['cases'].append(log.get('case_id'))
                    # Store first officer_id encountered (for foreign key)
                    if not customer_totals[customer_id]['officer_id']:
                        customer_totals[customer_id]['officer_id'] = log.get('officer_id')
                except (ValueError, TypeError):
                    continue

        # Get limit from configuration
        total_capital = limits.get('total_capital', 10000000)  # Default $10M
        max_exposure_pct = limits.get('customer_exposure_percent', 25)  # 25%
        max_exposure = total_capital * max_exposure_pct / 100

        # Check each customer
        for customer_id, data in customer_totals.items():
            total_exposure = data['total']
            if total_exposure > max_exposure:
                breach_amount = total_exposure - max_exposure
                breach_pct = (total_exposure / total_capital) * 100

                deviations.append({
                    'customer_id': customer_id,
                    'case_id': data['cases'][0] if data['cases'] else 'unknown',  # Use first case (foreign key constraint)
                    'officer_id': data['officer_id'] or fallback_officer_id,  # Use real officer_id (foreign key constraint)
                    'timestamp': None,
                    'deviation_type': 'customer_exposure_limit_exceeded',
                    'severity': 'critical',
                    'description': f'Customer {customer_id} total exposure ${total_exposure:,.0f} exceeds regulatory limit ${max_exposure:,.0f}',
                    'expected_behavior': f'Single customer exposure must not exceed {max_exposure_pct}% of capital (${max_exposure:,.0f})',
                    'actual_behavior': f'Customer exposure is {breach_pct:.1f}% of capital (${total_exposure:,.0f})',
                    'context': {
                        'customer_id': customer_id,
                        'total_exposure': total_exposure,
                        'limit': max_exposure,
                        'breach_amount': breach_amount,
                        'exposure_percent': round(breach_pct, 2),
                        'limit_percent': max_exposure_pct,
                        'number_of_cases': len(data['cases']),
                        'affected_cases': data['cases']
                    }
                })

        return deviations

    @staticmethod
    def _check_sector_concentration(
        logs: List[Dict[str, Any]],
        limits: Dict[str, Any],
        fallback_officer_id: str
    ) -> List[Dict[str, Any]]:
        """
        Check if any sector concentration exceeds limit.

        Regulatory Rule: Sector exposure < X% of total portfolio
        Common limit: 15% of portfolio

        Args:
            logs: All workflow logs
            limits: Configuration with sector_concentration_percent
            fallback_officer_id: Valid officer_id to use if none found in logs

        Returns:
            List of sector concentration deviations
        """
        deviations = []

        # Aggregate by sector
        sector_totals = defaultdict(lambda: {'total': 0, 'cases': [], 'officer_id': None})
        total_portfolio = 0

        for log in logs:
            sector = log.get('sector') or log.get('industry_sector')
            loan_amount = log.get('loan_amount_sanctioned')

            if sector and loan_amount:
                try:
                    loan_amount_float = float(loan_amount)
                    sector_totals[sector]['total'] += loan_amount_float
                    sector_totals[sector]['cases'].append(log.get('case_id'))
                    # Store first officer_id encountered (for foreign key)
                    if not sector_totals[sector]['officer_id']:
                        sector_totals[sector]['officer_id'] = log.get('officer_id')
                    total_portfolio += loan_amount_float
                except (ValueError, TypeError):
                    continue

        if total_portfolio == 0:
            return deviations

        # Get limit
        max_sector_pct = limits.get('sector_concentration_percent', 15)  # 15%
        max_sector_amount = total_portfolio * max_sector_pct / 100

        # Check each sector
        for sector, data in sector_totals.items():
            sector_total = data['total']
            sector_pct = (sector_total / total_portfolio) * 100

            if sector_pct > max_sector_pct:
                breach_pct = sector_pct - max_sector_pct

                deviations.append({
                    'case_id': data['cases'][0] if data['cases'] else 'unknown',  # Use first case (foreign key constraint)
                    'officer_id': data['officer_id'] or fallback_officer_id,  # Use real officer_id (foreign key constraint)
                    'timestamp': None,
                    'deviation_type': 'sector_concentration_risk',
                    'severity': 'high',
                    'description': f'Sector "{sector}" concentration {sector_pct:.1f}% exceeds limit {max_sector_pct}%',
                    'expected_behavior': f'Sector exposure must not exceed {max_sector_pct}% of portfolio',
                    'actual_behavior': f'Sector "{sector}" is {sector_pct:.1f}% of portfolio (${sector_total:,.0f} out of ${total_portfolio:,.0f})',
                    'context': {
                        'sector': sector,
                        'sector_exposure': sector_total,
                        'sector_percent': round(sector_pct, 2),
                        'limit_percent': max_sector_pct,
                        'total_portfolio': total_portfolio,
                        'breach_percent': round(breach_pct, 2),
                        'number_of_cases': len(set(data['cases'])),
                        'sample_cases': list(set(data['cases'][:5]))
                    }
                })

        return deviations

    @staticmethod
    def _check_branch_concentration(
        logs: List[Dict[str, Any]],
        limits: Dict[str, Any],
        fallback_officer_id: str
    ) -> List[Dict[str, Any]]:
        """
        Check if any branch is handling too much volume.

        Operational Rule: Single branch < X% of total volume
        Common limit: 30% of total cases

        Args:
            logs: All workflow logs
            limits: Configuration with branch_concentration_percent
            fallback_officer_id: Valid officer_id to use if none found in logs

        Returns:
            List of branch concentration deviations
        """
        deviations = []

        # Aggregate by branch (count unique cases per branch)
        branch_data = defaultdict(lambda: {'cases': set(), 'officer_id': None})
        all_cases = set()

        for log in logs:
            branch = log.get('branch_code') or log.get('branch_id')
            case_id = log.get('case_id')

            if branch and case_id:
                branch_data[branch]['cases'].add(case_id)
                # Store first officer_id encountered (for foreign key)
                if not branch_data[branch]['officer_id']:
                    branch_data[branch]['officer_id'] = log.get('officer_id')
                all_cases.add(case_id)

        total_cases = len(all_cases)
        if total_cases == 0:
            return deviations

        # Get limit
        max_branch_pct = limits.get('branch_concentration_percent', 30)  # 30%

        # Check each branch
        for branch, data in branch_data.items():
            cases = data['cases']
            branch_count = len(cases)
            branch_pct = (branch_count / total_cases) * 100

            if branch_pct > max_branch_pct:
                breach_pct = branch_pct - max_branch_pct

                deviations.append({
                    'case_id': list(cases)[0] if cases else 'unknown',  # Use first case (foreign key constraint)
                    'officer_id': data['officer_id'] or fallback_officer_id,  # Use real officer_id (foreign key constraint)
                    'timestamp': None,
                    'deviation_type': 'branch_concentration_risk',
                    'severity': 'medium',
                    'description': f'Branch {branch} handling {branch_pct:.1f}% of cases exceeds limit {max_branch_pct}%',
                    'expected_behavior': f'Single branch should not handle more than {max_branch_pct}% of total volume',
                    'actual_behavior': f'Branch {branch} handling {branch_count} cases out of {total_cases} ({branch_pct:.1f}%)',
                    'context': {
                        'branch_code': branch,
                        'branch_case_count': branch_count,
                        'branch_percent': round(branch_pct, 2),
                        'limit_percent': max_branch_pct,
                        'total_cases': total_cases,
                        'breach_percent': round(breach_pct, 2),
                        'sample_cases': list(cases)[:5]
                    }
                })

        return deviations
