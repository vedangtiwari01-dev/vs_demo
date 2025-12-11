const {
  WorkflowLog,
  Deviation,
  Officer,
  SOP,
  SOPRule,
} = require('../models');
const { successResponse, errorResponse } = require('../utils/response');
const { Op } = require('sequelize');
const { sequelize } = require('../config/database');

const getDashboard = async (req, res, next) => {
  try {
    // Total cases
    const totalCases = await WorkflowLog.findAll({
      attributes: [[sequelize.fn('COUNT', sequelize.fn('DISTINCT', sequelize.col('case_id'))), 'count']],
    });

    // Total deviations
    const totalDeviations = await Deviation.count();

    // Total officers
    const totalOfficers = await Officer.count();

    // Total SOPs
    const totalSOPs = await SOP.count();

    // Deviation rate
    const deviationRate = totalCases[0].dataValues.count > 0
      ? ((totalDeviations / totalCases[0].dataValues.count) * 100).toFixed(2)
      : 0;

    // Recent deviations
    const recentDeviations = await Deviation.findAll({
      limit: 10,
      order: [['detected_at', 'DESC']],
      include: [
        {
          model: Officer,
          attributes: ['id', 'name', 'role'],
        },
      ],
    });

    // High-risk officers (with most deviations)
    const highRiskOfficers = await Deviation.findAll({
      attributes: [
        'officer_id',
        [sequelize.fn('COUNT', sequelize.col('Deviation.id')), 'deviation_count'],
      ],
      include: [
        {
          model: Officer,
          attributes: ['id', 'name', 'role'],
        },
      ],
      group: ['officer_id', 'Officer.id'],
      order: [[sequelize.fn('COUNT', sequelize.col('Deviation.id')), 'DESC']],
      limit: 5,
    });

    // Deviation by severity
    const deviationsBySeverity = await Deviation.findAll({
      attributes: [
        'severity',
        [sequelize.fn('COUNT', sequelize.col('id')), 'count'],
      ],
      group: ['severity'],
    });

    return successResponse(
      res,
      {
        summary: {
          total_cases: parseInt(totalCases[0].dataValues.count),
          total_deviations: totalDeviations,
          total_officers: totalOfficers,
          total_sops: totalSOPs,
          deviation_rate: parseFloat(deviationRate),
        },
        recent_deviations: recentDeviations,
        high_risk_officers: highRiskOfficers,
        deviations_by_severity: deviationsBySeverity,
      },
      'Dashboard data retrieved successfully'
    );
  } catch (error) {
    next(error);
  }
};

const getComplianceRate = async (req, res, next) => {
  try {
    const { start_date, end_date } = req.query;

    const dateFilter = {};
    if (start_date) dateFilter[Op.gte] = new Date(start_date);
    if (end_date) dateFilter[Op.lte] = new Date(end_date);

    const logWhere = Object.keys(dateFilter).length > 0 ? { timestamp: dateFilter } : {};
    const devWhere = Object.keys(dateFilter).length > 0 ? { detected_at: dateFilter } : {};

    const totalCases = await WorkflowLog.findAll({
      where: logWhere,
      attributes: [[sequelize.fn('COUNT', sequelize.fn('DISTINCT', sequelize.col('case_id'))), 'count']],
    });

    const casesWithDeviations = await Deviation.findAll({
      where: devWhere,
      attributes: [[sequelize.fn('COUNT', sequelize.fn('DISTINCT', sequelize.col('case_id'))), 'count']],
    });

    const totalCaseCount = parseInt(totalCases[0].dataValues.count);
    const deviatedCaseCount = parseInt(casesWithDeviations[0].dataValues.count);
    const compliantCaseCount = totalCaseCount - deviatedCaseCount;

    const complianceRate = totalCaseCount > 0
      ? ((compliantCaseCount / totalCaseCount) * 100).toFixed(2)
      : 100;

    return successResponse(
      res,
      {
        total_cases: totalCaseCount,
        compliant_cases: compliantCaseCount,
        deviated_cases: deviatedCaseCount,
        compliance_rate: parseFloat(complianceRate),
      },
      'Compliance rate calculated successfully'
    );
  } catch (error) {
    next(error);
  }
};

const getTrends = async (req, res, next) => {
  try {
    const { days = 30 } = req.query;

    const startDate = new Date();
    startDate.setDate(startDate.getDate() - parseInt(days));

    const deviations = await Deviation.findAll({
      where: {
        detected_at: {
          [Op.gte]: startDate,
        },
      },
      attributes: [
        [sequelize.fn('DATE', sequelize.col('detected_at')), 'date'],
        'severity',
        [sequelize.fn('COUNT', sequelize.col('id')), 'count'],
      ],
      group: [sequelize.fn('DATE', sequelize.col('detected_at')), 'severity'],
      order: [[sequelize.fn('DATE', sequelize.col('detected_at')), 'ASC']],
    });

    return successResponse(res, deviations, 'Deviation trends retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const getProcessFlow = async (req, res, next) => {
  try {
    // Get all workflow steps with frequency
    const steps = await WorkflowLog.findAll({
      attributes: [
        'step_name',
        [sequelize.fn('COUNT', sequelize.col('id')), 'frequency'],
      ],
      group: ['step_name'],
      order: [[sequelize.fn('COUNT', sequelize.col('id')), 'DESC']],
    });

    // Get step sequences (edges)
    const logs = await WorkflowLog.findAll({
      attributes: ['case_id', 'step_name', 'timestamp'],
      order: [['case_id', 'ASC'], ['timestamp', 'ASC']],
    });

    // Build edges from sequential steps
    const edges = {};
    const caseSteps = {};

    logs.forEach(log => {
      if (!caseSteps[log.case_id]) {
        caseSteps[log.case_id] = [];
      }
      caseSteps[log.case_id].push(log.step_name);
    });

    Object.values(caseSteps).forEach(steps => {
      for (let i = 0; i < steps.length - 1; i++) {
        const edge = `${steps[i]} -> ${steps[i + 1]}`;
        edges[edge] = (edges[edge] || 0) + 1;
      }
    });

    const edgeList = Object.entries(edges).map(([edge, count]) => {
      const [from, to] = edge.split(' -> ');
      return { from, to, count };
    });

    return successResponse(
      res,
      {
        nodes: steps,
        edges: edgeList,
      },
      'Process flow data retrieved successfully'
    );
  } catch (error) {
    next(error);
  }
};

module.exports = {
  getDashboard,
  getComplianceRate,
  getTrends,
  getProcessFlow,
};
