const aiService = require('./ai-integration.service');
const { SOP } = require('../models');
const logger = require('../utils/logger');

/**
 * Column Mapping Service
 * Handles intelligent CSV column mapping using AI
 */

/**
 * Analyze CSV headers and get AI mapping suggestions
 * @param {Array<string>} headers - CSV column headers
 * @param {Array<Object>} sampleRows - First few rows of data for context
 * @returns {Promise<Object>} Mapping suggestions from AI
 */
const analyzeHeaders = async (headers, sampleRows = []) => {
  try {
    logger.info(`Analyzing ${headers.length} CSV headers`);

    // Call AI service for intelligent mapping
    const mappingSuggestions = await aiService.analyzeColumnMapping(headers, sampleRows);

    return mappingSuggestions;
  } catch (error) {
    logger.error(`Error analyzing headers: ${error.message}`);
    throw error;
  }
};

/**
 * Store confirmed column mapping in SOP metadata for reuse
 * @param {number|null} sopId - SOP ID to associate mapping with (optional)
 * @param {Object} mapping - Confirmed column mapping
 * @param {Array<string>} headers - Original CSV headers
 * @returns {Promise<Object>} Saved mapping info
 */
const saveMapping = async (sopId, mapping, headers) => {
  try {
    const mappingData = {
      column_mappings: mapping,
      mapping_confirmed: true,
      mapped_at: new Date().toISOString(),
      original_headers: headers
    };

    if (sopId) {
      // Associate with specific SOP
      const sop = await SOP.findByPk(sopId);
      if (sop) {
        const currentMetadata = sop.metadata || {};
        sop.metadata = {
          ...currentMetadata,
          ...mappingData
        };
        await sop.save();
        logger.info(`Saved column mapping to SOP ${sopId}`);
      }
    }

    return mappingData;
  } catch (error) {
    logger.error(`Error saving mapping: ${error.message}`);
    throw error;
  }
};

/**
 * Get saved column mapping for an SOP
 * @param {number} sopId - SOP ID
 * @returns {Promise<Object|null>} Saved mapping or null
 */
const getSavedMapping = async (sopId) => {
  try {
    const sop = await SOP.findByPk(sopId);
    if (!sop || !sop.metadata || !sop.metadata.column_mappings) {
      return null;
    }

    return {
      mapping: sop.metadata.column_mappings,
      mapped_at: sop.metadata.mapped_at,
      original_headers: sop.metadata.original_headers
    };
  } catch (error) {
    logger.error(`Error retrieving saved mapping: ${error.message}`);
    return null;
  }
};

/**
 * Apply column mapping to transform CSV data
 * @param {Array<Object>} data - Raw CSV data
 * @param {Object} mapping - Column mapping (csv_column -> system_field)
 * @returns {Array<Object>} Transformed data with system field names
 */
const applyMapping = (data, mapping) => {
  try {
    const transformedData = data.map(row => {
      const transformedRow = {};

      // Apply mapping for each field
      for (const [csvColumn, systemField] of Object.entries(mapping)) {
        if (row[csvColumn] !== undefined) {
          transformedRow[systemField] = row[csvColumn];
        }
      }

      return transformedRow;
    });

    logger.info(`Applied mapping to ${transformedData.length} rows`);
    return transformedData;
  } catch (error) {
    logger.error(`Error applying mapping: ${error.message}`);
    throw error;
  }
};

/**
 * Detect notes column from mapping
 * @param {Object} mapping - Column mapping
 * @returns {string|null} Name of notes column or null
 */
const detectNotesColumn = (mapping) => {
  // Find which CSV column maps to 'notes' or 'comments'
  for (const [csvColumn, systemField] of Object.entries(mapping)) {
    if (systemField === 'notes' || systemField === 'comments') {
      return csvColumn;
    }
  }
  return null;
};

/**
 * Validate that mapping includes all required fields
 * @param {Object} mapping - Column mapping
 * @returns {Object} Validation result with isValid and missing fields
 */
const validateMapping = (mapping) => {
  // Core required fields - must be present
  const requiredFields = ['case_id', 'officer_id', 'step_name', 'action', 'timestamp'];

  // Extended optional fields - improve analysis quality when present
  const optionalFields = [
    // Core workflow
    'duration_seconds', 'status', 'notes', 'comments',
    // Entity identifiers
    'application_id', 'loan_id', 'customer_id', 'customer_name', 'customer_segment', 'customer_type', 'customer_risk_rating',
    'group_id', 'related_party_flag', 'staff_flag', 'portfolio_id',
    // Product & channel
    'product_type', 'sub_product_type', 'scheme_code', 'secured_unsecured_flag',
    'channel', 'branch_code', 'branch_name', 'region', 'geo_code',
    // Amounts & terms
    'loan_amount_requested', 'loan_amount_sanctioned', 'loan_amount_disbursed',
    'interest_rate', 'interest_type', 'processing_fee', 'other_charges',
    'tenor_months', 'tenor_days', 'repayment_frequency', 'emi_amount',
    'ltv_ratio', 'margin_pct', 'total_group_exposure', 'customer_total_exposure',
    // Risk & credit
    'credit_score_bureau', 'credit_score_internal', 'scorecard_version', 'score_band',
    'emi_to_income_ratio', 'dti_ratio', 'risk_grade', 'risk_category',
    // Collateral & security
    'collateral_type', 'collateral_description', 'collateral_value', 'collateral_value_date',
    'valuation_status', 'valuation_firm_id', 'security_created_flag', 'security_perfected_flag',
    // KYC / AML
    'kyc_status', 'kyc_completed_flag', 'kyc_date', 'kyc_mode',
    'sanctions_hit_flag', 'watchlist_hit_flag', 'pep_flag', 'aml_risk_rating',
    // Workflow detail
    'step_id', 'stage_name', 'workflow_version', 'action_type', 'sub_status',
    'officer_name', 'officer_role', 'approval_role', 'approval_level',
    'timestamp_start', 'timestamp_end', 'step_time', 'business_date',
    'queue_name', 'queue_priority', 'sla_target_timestamp', 'sla_breach_flag',
    // Approvals & exceptions
    'approver_id', 'approver_role', 'approval_decision', 'approval_timestamp',
    'exception_flag', 'exception_reason', 'exception_approver_id',
    'override_flag', 'override_reason', 'override_approver_id',
    // Disbursement
    'disbursement_date', 'disbursement_amount', 'disbursement_mode',
    'mandate_status', 'first_emi_date', 'statement_generated_flag',
    'post_disbursement_qc_flag', 'post_disbursement_qc_date', 'qc_findings',
    // Collections & restructuring
    'overdue_days', 'bucket', 'collection_status', 'collection_agent_id',
    'restructure_flag', 'restructure_date', 'restructure_type',
    'writeoff_flag', 'writeoff_amount', 'writeoff_date',
    // Audit & data quality
    'created_by', 'created_at', 'updated_by', 'updated_at',
    'source_system', 'source_file_name', 'import_batch_id',
    'audit_trail_id', 'log_level', 'error_code', 'error_message'
  ];

  const mappedFields = Object.values(mapping);
  const missingFields = requiredFields.filter(field => !mappedFields.includes(field));
  const presentOptionalFields = optionalFields.filter(field => mappedFields.includes(field));

  return {
    isValid: missingFields.length === 0,
    missingFields,
    presentOptionalFields,
    optionalFieldCount: presentOptionalFields.length,
    totalSupportedFields: requiredFields.length + optionalFields.length,
    message: missingFields.length > 0
      ? `Missing required fields: ${missingFields.join(', ')}`
      : `All required fields mapped. ${presentOptionalFields.length} optional fields detected for enhanced analysis.`
  };
};

module.exports = {
  analyzeHeaders,
  saveMapping,
  getSavedMapping,
  applyMapping,
  detectNotesColumn,
  validateMapping
};
