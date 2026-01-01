const { SOP, SOPRule } = require('../models');
const aiService = require('../services/ai-integration.service');
const { successResponse, errorResponse } = require('../utils/response');
const path = require('path');

const uploadSOP = async (req, res, next) => {
  try {
    console.log('[uploadSOP] Starting upload process');
    const { title, version } = req.body;
    const file = req.file;

    console.log('[uploadSOP] Request body:', { title, version });
    console.log('[uploadSOP] File:', file ? { name: file.originalname, size: file.size, path: file.path } : 'No file');

    if (!file) {
      console.log('[uploadSOP] Error: No file uploaded');
      return errorResponse(res, 'No file uploaded', 400);
    }

    console.log('[uploadSOP] Creating SOP record in database...');
    const sop = await SOP.create({
      title: title || file.originalname,
      version: version || '1.0',
      file_path: file.path,
      file_type: path.extname(file.originalname).substring(1),
      status: 'uploaded',
    });

    console.log('[uploadSOP] SOP created successfully:', sop.id);
    console.log('[uploadSOP] Sending success response...');

    const response = successResponse(res, sop, 'SOP uploaded successfully', 201);
    console.log('[uploadSOP] Response sent successfully');
    return response;
  } catch (error) {
    console.log('[uploadSOP] Error caught:', error.message);
    console.log('[uploadSOP] Error stack:', error.stack);
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
    console.log(`[processSOP] Starting SOP processing for ID: ${id}`);

    const sop = await SOP.findByPk(id);

    if (!sop) {
      return errorResponse(res, 'SOP not found', 404);
    }

    if (sop.processed) {
      return errorResponse(res, 'SOP already processed', 400);
    }

    console.log(`[processSOP] SOP file path: ${sop.file_path}`);
    console.log(`[processSOP] SOP file type: ${sop.file_type}`);

    // Update status to processing
    await sop.update({ status: 'processing' });

    // Step 1: Parse SOP document
    currentStep = 'parsing';
    console.log(`[processSOP] Step 1: Parsing SOP document...`);
    const parseStart = Date.now();
    const parseResult = await aiService.parseSOP(sop.file_path, sop.file_type);
    const parseTime = Date.now() - parseStart;
    console.log(`[processSOP] Parsing completed in ${parseTime}ms`);
    console.log(`[processSOP] Extracted text length: ${parseResult.text?.length || 0} characters`);

    if (!parseResult.text || parseResult.text.trim().length === 0) {
      throw new Error('SOP document is empty or could not be parsed. Please check if the file is valid and contains text.');
    }

    // Step 2: Extract rules using Claude AI
    currentStep = 'rule_extraction';
    console.log(`[processSOP] Step 2: Extracting rules from text using Claude AI...`);
    const extractStart = Date.now();
    const rulesResult = await aiService.extractRules(parseResult.text);
    const extractTime = Date.now() - extractStart;
    console.log(`[processSOP] Rule extraction completed in ${extractTime}ms`);
    console.log(`[processSOP] Extracted ${rulesResult.rules?.length || 0} rules`);

    if (!rulesResult.rules || rulesResult.rules.length === 0) {
      throw new Error('No rules could be extracted from the SOP document. The document may not contain structured rules that the AI can identify. Please ensure your SOP has clear requirements, steps, and policies.');
    }

    // Step 3: Validate and save rules
    currentStep = 'saving_rules';
    console.log(`[processSOP] Step 3: Saving ${rulesResult.rules.length} rules to database...`);
    const rules = await Promise.all(
      rulesResult.rules.map(rule =>
        SOPRule.create({
          sop_id: sop.id,
          rule_type: rule.rule_type,
          rule_description: rule.rule_description,
          step_number: rule.step_number ? Math.floor(rule.step_number) : null,
          severity: rule.severity || 'medium',
          condition_logic: rule.condition_logic,
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

    const totalTime = Date.now() - startTime;
    console.log(`[processSOP] ✓ SOP processing completed successfully in ${totalTime}ms`);
    console.log(`[processSOP] Summary: ${rules.length} rules extracted and saved`);

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
