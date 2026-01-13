const { SOP, SOPRule } = require('../models');
const aiService = require('../services/ai-integration.service');
const { successResponse, errorResponse } = require('../utils/response');
const path = require('path');
const logger = require('../utils/clean-logger');

const uploadSOP = async (req, res, next) => {
  try {
    const { title, version } = req.body;
    const file = req.file;

    logger.endpoint('POST', '/api/sops/upload', {
      'Filename': file?.originalname || 'none',
      'Title': title || 'auto',
      'Version': version || '1.0'
    });

    if (!file) {
      logger.error('No file uploaded');
      return errorResponse(res, 'No file uploaded', 400);
    }

    const sop = await SOP.create({
      title: title || file.originalname,
      version: version || '1.0',
      file_path: file.path,
      file_type: path.extname(file.originalname).substring(1),
      status: 'uploaded',
    });

    logger.success('SOP Uploaded', {
      'ID': sop.id,
      'Title': sop.title,
      'Type': sop.file_type
    });

    return successResponse(res, sop, 'SOP uploaded successfully', 201);
  } catch (error) {
    logger.error('SOP upload failed', error);
    next(error);
  }
};

const listSOPs = async (req, res, next) => {
  try {
    const sops = await SOP.findAll({
      order: [['uploaded_at', 'DESC']],
      include: [
        {
          model: SOPRule,
          as: 'rules',
          attributes: ['id', 'rule_type', 'severity'],
        },
      ],
    });

    return successResponse(res, sops, 'SOPs retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const getSOPById = async (req, res, next) => {
  try {
    const { id } = req.params;

    const sop = await SOP.findByPk(id, {
      include: [
        {
          model: SOPRule,
          as: 'rules',
        },
      ],
    });

    if (!sop) {
      return errorResponse(res, 'SOP not found', 404);
    }

    return successResponse(res, sop, 'SOP retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const processSOP = async (req, res, next) => {
  const startTime = Date.now();
  let currentStep = 'initialization';

  try {
    const { id } = req.params;

    logger.endpoint('POST', `/api/sops/${id}/process`);
    const timer = logger.startTimer();

    const sop = await SOP.findByPk(id);

    if (!sop) {
      logger.error('SOP not found');
      return errorResponse(res, 'SOP not found', 404);
    }

    if (sop.processed) {
      logger.warn('SOP already processed');
      return errorResponse(res, 'SOP already processed', 400);
    }

    logger.step('Loading SOP', {
      'Title': sop.title,
      'Type': sop.file_type,
      'Version': sop.version
    });

    // Update status to processing
    await sop.update({ status: 'processing' });

    // Step 1: Parse SOP document
    currentStep = 'parsing';
    const parseStart = Date.now();
    const parseResult = await aiService.parseSOP(sop.file_path, sop.file_type);
    const parseTime = Date.now() - parseStart;

    if (!parseResult.text || parseResult.text.trim().length === 0) {
      throw new Error('SOP document is empty or could not be parsed. Please check if the file is valid and contains text.');
    }

    logger.step('Document Parsed', {
      'Characters': parseResult.text.length,
      'Time': `${parseTime}ms`
    });

    // Step 2: Extract rules using Claude AI
    currentStep = 'rule_extraction';
    const extractStart = Date.now();
    const rulesResult = await aiService.extractRules(parseResult.text);
    const extractTime = Date.now() - extractStart;

    if (!rulesResult.rules || rulesResult.rules.length === 0) {
      throw new Error('No rules could be extracted from the SOP document. The document may not contain structured rules that the AI can identify. Please ensure your SOP has clear requirements, steps, and policies.');
    }

    logger.step('Rules Extracted', {
      'Count': rulesResult.rules.length,
      'Time': `${extractTime}ms`,
      'Model': 'Claude Sonnet 4.5'
    });

    // Step 3: Validate and save rules
    currentStep = 'saving_rules';
    const rules = await Promise.all(
      rulesResult.rules.map(rule =>
        SOPRule.create({
          sop_id: sop.id,
          rule_type: rule.rule_type,
          rule_description: rule.rule_description,
          step_number: rule.step_number ? Math.floor(rule.step_number) : null,
          severity: rule.severity || 'medium',
          required_fields: rule.required_fields,
          condition_logic: rule.condition_logic,

          // NEW FIELDS FOR ENHANCED FEATURES (2025 Q1)
          temporal_constraint: rule.temporal_constraint,
          product_types: rule.product_types,
          customer_segments: rule.customer_segments,
          channels: rule.channels,
          geography: rule.geography,
          exceptions: rule.exceptions,
          calculation_formula: rule.calculation_formula,
          threshold_value: rule.threshold_value,
          field_dependencies: rule.field_dependencies,
          regulatory_reference: rule.regulatory_reference,
          timing_constraint: rule.timing_constraint,
        })
      )
    );

    // Step 4: Update SOP status
    currentStep = 'finalizing';
    await sop.update({
      processed: true,
      status: 'completed',
      metadata: {
        rules_count: rules.length,
        processed_at: new Date(),
        processing_time_ms: Date.now() - startTime,
        parse_time_ms: parseTime,
        extract_time_ms: extractTime
      },
    });

    // Aggregate rules by type
    const rulesByType = {};
    const rulesBySeverity = {};
    rules.forEach(r => {
      rulesByType[r.rule_type] = (rulesByType[r.rule_type] || 0) + 1;
      rulesBySeverity[r.severity] = (rulesBySeverity[r.severity] || 0) + 1;
    });

    logger.aggregated('Rules by Type', rulesByType, { maxItems: 8 });

    logger.success('SOP Processing Complete', {
      'Total rules': rules.length,
      'Parse time': `${parseTime}ms`,
      'Extract time': `${extractTime}ms`,
      'Total time': logger.getElapsed(timer)
    });

    return successResponse(res, { sop, rules }, 'SOP processed successfully');
  } catch (error) {
    const totalTime = Date.now() - startTime;
    console.error(`[processSOP] ✗ Processing failed at step: ${currentStep}`);
    console.error(`[processSOP] Error after ${totalTime}ms:`, error.message);
    console.error(`[processSOP] Error stack:`, error.stack);

    // Update SOP status with detailed error info
    try {
      const sop = await SOP.findByPk(req.params.id);
      if (sop) {
        await sop.update({
          status: 'failed',
          metadata: {
            ...sop.metadata,
            last_error: {
              step: currentStep,
              message: error.message,
              timestamp: new Date(),
              processing_time_ms: totalTime
            }
          }
        });
      }
    } catch (updateError) {
      console.error(`[processSOP] Failed to update SOP status:`, updateError.message);
    }

    // Return user-friendly error message
    let userMessage = `SOP processing failed during ${currentStep} step: ${error.message}`;

    if (currentStep === 'parsing') {
      userMessage += '\n\nPossible causes:\n• File format is not supported or corrupted\n• File path is incorrect\n• Python-docx library not installed in AI service\n\nPlease check your SOP file and try again.';
    } else if (currentStep === 'rule_extraction') {
      userMessage += '\n\nPossible causes:\n• Claude API quota exceeded or API key invalid\n• SOP text is too long (exceeds token limit)\n• No structured rules found in the document\n• Network timeout to Claude API\n\nPlease check your SOP document structure and Claude API configuration.';
    }

    return errorResponse(res, userMessage, 500);
  }
};

const getSOPRules = async (req, res, next) => {
  try {
    const { id } = req.params;

    const rules = await SOPRule.findAll({
      where: { sop_id: id },
      order: [['step_number', 'ASC']],
    });

    return successResponse(res, rules, 'SOP rules retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const deleteSOP = async (req, res, next) => {
  try {
    const { id } = req.params;

    const sop = await SOP.findByPk(id);

    if (!sop) {
      return errorResponse(res, 'SOP not found', 404);
    }

    // Delete associated rules first
    await SOPRule.destroy({ where: { sop_id: id } });

    // Delete SOP
    await sop.destroy();

    return successResponse(res, null, 'SOP deleted successfully');
  } catch (error) {
    next(error);
  }
};

module.exports = {
  uploadSOP,
  listSOPs,
  getSOPById,
  processSOP,
  getSOPRules,
  deleteSOP,
};
