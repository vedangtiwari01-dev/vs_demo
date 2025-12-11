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
  const requiredFields = ['case_id', 'officer_id', 'step_name', 'action', 'timestamp'];
  const mappedFields = Object.values(mapping);
  const missingFields = requiredFields.filter(field => !mappedFields.includes(field));

  return {
    isValid: missingFields.length === 0,
    missingFields,
    message: missingFields.length > 0
      ? `Missing required fields: ${missingFields.join(', ')}`
      : 'All required fields mapped'
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
