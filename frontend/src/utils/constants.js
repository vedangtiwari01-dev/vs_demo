export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

export const SEVERITY_COLORS = {
  critical: 'text-red-600 bg-red-100',
  high: 'text-orange-600 bg-orange-100',
  medium: 'text-yellow-600 bg-yellow-100',
  low: 'text-green-600 bg-green-100',
};

export const DEVIATION_TYPES = {
  missing_step: 'Missing Step',
  wrong_sequence: 'Wrong Sequence',
  unexpected_step: 'Unexpected Step',
  missing_approval: 'Missing Approval',
  timing_violation: 'Timing Violation',
};

export const SCENARIO_TYPES = {
  officer_shortage: 'Officer Shortage',
  peak_load: 'Peak Load',
  system_downtime: 'System Downtime',
  regulatory_change: 'Regulatory Change',
};
