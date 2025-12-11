const { StressTestScenario, WorkflowLog, Deviation, SOPRule } = require('../models');
const aiService = require('../services/ai-integration.service');
const { successResponse, errorResponse } = require('../utils/response');

const createScenario = async (req, res, next) => {
  try {
    const { name, description, scenario_type, parameters } = req.body;

    if (!name || !scenario_type || !parameters) {
      return errorResponse(res, 'Missing required fields', 400);
    }

    const scenario = await StressTestScenario.create({
      name,
      description,
      scenario_type,
      parameters,
    });

    return successResponse(res, scenario, 'Scenario created successfully', 201);
  } catch (error) {
    next(error);
  }
};

const listScenarios = async (req, res, next) => {
  try {
    const scenarios = await StressTestScenario.findAll({
      order: [['created_at', 'DESC']],
    });

    return successResponse(res, scenarios, 'Scenarios retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const getScenarioById = async (req, res, next) => {
  try {
    const { id } = req.params;

    const scenario = await StressTestScenario.findByPk(id);

    if (!scenario) {
      return errorResponse(res, 'Scenario not found', 404);
    }

    return successResponse(res, scenario, 'Scenario retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const generateSyntheticLogs = async (req, res, next) => {
  try {
    const { scenario_id, scenario_type, parameters } = req.body;

    let scenarioType = scenario_type;
    let scenarioParams = parameters;

    // If scenario_id provided, fetch scenario
    if (scenario_id) {
      const scenario = await StressTestScenario.findByPk(scenario_id);
      if (!scenario) {
        return errorResponse(res, 'Scenario not found', 404);
      }
      scenarioType = scenario.scenario_type;
      scenarioParams = scenario.parameters;
    }

    if (!scenarioType || !scenarioParams) {
      return errorResponse(res, 'Scenario type and parameters required', 400);
    }

    // Generate synthetic logs using AI service
    const result = await aiService.generateSyntheticLogs(scenarioType, scenarioParams);

    // Save synthetic logs to database
    const savedLogs = [];
    for (const log of result.logs) {
      const workflowLog = await WorkflowLog.create({
        case_id: log.case_id,
        officer_id: log.officer_id,
        step_name: log.step_name,
        action: log.action,
        timestamp: new Date(log.timestamp),
        duration_seconds: log.duration_seconds,
        status: log.status || 'completed',
        is_synthetic: true,
        metadata: { scenario_type: scenarioType, scenario_id },
      });
      savedLogs.push(workflowLog);
    }

    // Analyze synthetic logs for deviations
    const rules = await SOPRule.findAll();

    if (rules.length > 0) {
      const formattedLogs = savedLogs.map(log => ({
        case_id: log.case_id,
        officer_id: log.officer_id,
        step_name: log.step_name,
        action: log.action,
        timestamp: log.timestamp.toISOString(),
      }));

      const formattedRules = rules.map(rule => ({
        id: rule.id,
        type: rule.rule_type,
        description: rule.rule_description,
        step_number: rule.step_number,
        severity: rule.severity,
      }));

      const deviationResult = await aiService.detectDeviations(formattedLogs, formattedRules);

      // Save detected deviations
      for (const dev of deviationResult.deviations) {
        await Deviation.create({
          case_id: dev.case_id,
          officer_id: dev.officer_id,
          deviation_type: dev.deviation_type,
          rule_id: dev.rule_id || null,
          severity: dev.severity,
          description: dev.description,
          expected_behavior: dev.expected_behavior,
          actual_behavior: dev.actual_behavior,
          context: { ...dev.context, is_synthetic: true },
        });
      }
    }

    return successResponse(
      res,
      {
        scenario_type: scenarioType,
        total_logs: savedLogs.length,
        unique_cases: new Set(savedLogs.map(l => l.case_id)).size,
        unique_officers: new Set(savedLogs.map(l => l.officer_id)).size,
      },
      'Synthetic logs generated successfully',
      201
    );
  } catch (error) {
    next(error);
  }
};

const deleteScenario = async (req, res, next) => {
  try {
    const { id } = req.params;

    const scenario = await StressTestScenario.findByPk(id);

    if (!scenario) {
      return errorResponse(res, 'Scenario not found', 404);
    }

    await scenario.destroy();

    return successResponse(res, null, 'Scenario deleted successfully');
  } catch (error) {
    next(error);
  }
};

module.exports = {
  createScenario,
  listScenarios,
  getScenarioById,
  generateSyntheticLogs,
  deleteScenario,
};
