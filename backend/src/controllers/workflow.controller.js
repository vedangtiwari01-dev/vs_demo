const { WorkflowLog, Officer, Deviation, SOPRule } = require('../models');
const aiService = require('../services/ai-integration.service');
const { successResponse, errorResponse } = require('../utils/response');
const Papa = require('papaparse');
const fs = require('fs').promises;

const uploadWorkflowLogs = async (req, res, next) => {
  try {
    const file = req.file;

    if (!file) {
      return errorResponse(res, 'No file uploaded', 400);
    }

    // Read and parse file
    const fileContent = await fs.readFile(file.path, 'utf8');
    let logs;

    if (file.originalname.endsWith('.csv')) {
      const parsed = Papa.parse(fileContent, {
        header: true,
        skipEmptyLines: true,
      });
      logs = parsed.data;
    } else if (file.originalname.endsWith('.json')) {
      logs = JSON.parse(fileContent);
    } else {
      return errorResponse(res, 'Unsupported file format', 400);
    }

    // Transform and save logs
    const savedLogs = [];
    const officers = new Set();

    for (const log of logs) {
      const workflowLog = await WorkflowLog.create({
        case_id: log.case_id || log.caseId,
        officer_id: log.officer_id || log.officerId,
        step_name: log.step_name || log.stepName || log.step,
        action: log.action || 'completed',
        timestamp: new Date(log.timestamp || log.date),
        duration_seconds: log.duration_seconds || log.duration || null,
        status: log.status || 'completed',
        metadata: log.metadata || {},
        is_synthetic: false,
      });

      savedLogs.push(workflowLog);
      officers.add(log.officer_id || log.officerId);
    }

    // Create officer records if they don't exist
    for (const officerId of officers) {
      await Officer.findOrCreate({
        where: { id: officerId },
        defaults: {
          id: officerId,
          name: `Officer ${officerId}`,
          role: 'Loan Officer',
        },
      });
    }

    return successResponse(
      res,
      {
        total_logs: savedLogs.length,
        unique_cases: new Set(savedLogs.map(l => l.case_id)).size,
        unique_officers: officers.size,
      },
      'Workflow logs uploaded successfully',
      201
    );
  } catch (error) {
    next(error);
  }
};

const listWorkflowLogs = async (req, res, next) => {
  try {
    const { case_id, officer_id, limit = 100, offset = 0 } = req.query;

    const where = {};
    if (case_id) where.case_id = case_id;
    if (officer_id) where.officer_id = officer_id;

    const logs = await WorkflowLog.findAll({
      where,
      order: [['timestamp', 'DESC']],
      limit: parseInt(limit),
      offset: parseInt(offset),
    });

    const total = await WorkflowLog.count({ where });

    return successResponse(res, { logs, total }, 'Workflow logs retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const getWorkflowByCase = async (req, res, next) => {
  try {
    const { caseId } = req.params;

    const logs = await WorkflowLog.findAll({
      where: { case_id: caseId },
      order: [['timestamp', 'ASC']],
    });

    if (logs.length === 0) {
      return errorResponse(res, 'No workflow found for this case', 404);
    }

    return successResponse(res, logs, 'Case workflow retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const analyzeWorkflow = async (req, res, next) => {
  try {
    // Get all logs
    const logs = await WorkflowLog.findAll({
      where: { is_synthetic: false },
      order: [['case_id', 'ASC'], ['timestamp', 'ASC']],
    });

    // Get all rules
    const rules = await SOPRule.findAll();

    if (rules.length === 0) {
      return errorResponse(res, 'No SOP rules found. Please upload and process an SOP first.', 400);
    }

    // Format logs for AI service
    const formattedLogs = logs.map(log => ({
      case_id: log.case_id,
      officer_id: log.officer_id,
      step_name: log.step_name,
      action: log.action,
      timestamp: log.timestamp.toISOString(),
      duration_seconds: log.duration_seconds,
      status: log.status,
    }));

    // Format rules for AI service
    const formattedRules = rules.map(rule => ({
      id: rule.id,
      type: rule.rule_type,
      description: rule.rule_description,
      step_number: rule.step_number,
      severity: rule.severity,
    }));

    // Detect deviations using AI service
    const deviationResult = await aiService.detectDeviations(formattedLogs, formattedRules);

    // Save deviations to database
    const savedDeviations = [];
    for (const dev of deviationResult.deviations) {
      const deviation = await Deviation.create({
        case_id: dev.case_id,
        officer_id: dev.officer_id,
        deviation_type: dev.deviation_type,
        rule_id: dev.rule_id || null,
        severity: dev.severity,
        description: dev.description,
        expected_behavior: dev.expected_behavior,
        actual_behavior: dev.actual_behavior,
        context: dev.context || {},
      });
      savedDeviations.push(deviation);
    }

    return successResponse(
      res,
      {
        total_deviations: savedDeviations.length,
        deviations: savedDeviations,
        summary: {
          critical: savedDeviations.filter(d => d.severity === 'critical').length,
          high: savedDeviations.filter(d => d.severity === 'high').length,
          medium: savedDeviations.filter(d => d.severity === 'medium').length,
          low: savedDeviations.filter(d => d.severity === 'low').length,
        },
      },
      'Workflow analysis completed'
    );
  } catch (error) {
    next(error);
  }
};

module.exports = {
  uploadWorkflowLogs,
  listWorkflowLogs,
  getWorkflowByCase,
  analyzeWorkflow,
};
