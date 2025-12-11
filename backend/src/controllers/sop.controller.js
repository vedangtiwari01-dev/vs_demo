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
  try {
    const { id } = req.params;

    const sop = await SOP.findByPk(id);

    if (!sop) {
      return errorResponse(res, 'SOP not found', 404);
    }

    if (sop.processed) {
      return errorResponse(res, 'SOP already processed', 400);
    }

    // Update status to processing
    await sop.update({ status: 'processing' });

    // Parse SOP using AI service
    const parseResult = await aiService.parseSOP(sop.file_path, sop.file_type);

    // Extract rules
    const rulesResult = await aiService.extractRules(parseResult.text);

    // Save rules to database
    const rules = await Promise.all(
      rulesResult.rules.map(rule =>
        SOPRule.create({
          sop_id: sop.id,
          rule_type: rule.type,
          rule_description: rule.description,
          step_number: rule.step_number,
          severity: rule.severity || 'medium',
          condition_logic: rule.condition_logic,
        })
      )
    );

    // Update SOP status
    await sop.update({
      processed: true,
      status: 'completed',
      metadata: { rules_count: rules.length, processed_at: new Date() },
    });

    return successResponse(res, { sop, rules }, 'SOP processed successfully');
  } catch (error) {
    const sop = await SOP.findByPk(req.params.id);
    if (sop) {
      await sop.update({ status: 'failed' });
    }
    next(error);
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
