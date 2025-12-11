const {
  Officer,
  BehavioralProfile,
  BehavioralPattern,
  WorkflowLog,
  Deviation,
} = require('../models');
const aiService = require('../services/ai-integration.service');
const { successResponse, errorResponse } = require('../utils/response');
const { Op } = require('sequelize');
const { sequelize } = require('../config/database');

const listOfficers = async (req, res, next) => {
  try {
    const officers = await Officer.findAll({
      include: [
        {
          model: Deviation,
          as: 'deviations',
          attributes: [],
        },
      ],
      attributes: {
        include: [
          [sequelize.fn('COUNT', sequelize.col('deviations.id')), 'deviation_count'],
        ],
      },
      group: ['Officer.id'],
      order: [[sequelize.fn('COUNT', sequelize.col('deviations.id')), 'DESC']],
    });

    return successResponse(res, officers, 'Officers retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const getOfficerProfile = async (req, res, next) => {
  try {
    const { id } = req.params;

    const officer = await Officer.findByPk(id, {
      include: [
        {
          model: Deviation,
          as: 'deviations',
        },
        {
          model: BehavioralProfile,
          as: 'profiles',
          limit: 1,
          order: [['profile_date', 'DESC']],
        },
        {
          model: BehavioralPattern,
          as: 'patterns',
        },
      ],
    });

    if (!officer) {
      return errorResponse(res, 'Officer not found', 404);
    }

    // Get workflow logs for this officer
    const logs = await WorkflowLog.findAll({
      where: { officer_id: id },
      order: [['timestamp', 'ASC']],
    });

    // Calculate metrics
    const totalCases = new Set(logs.map(l => l.case_id)).size;
    const deviationCount = officer.deviations.length;
    const deviationRate = totalCases > 0 ? (deviationCount / totalCases) * 100 : 0;

    return successResponse(
      res,
      {
        officer,
        metrics: {
          total_cases: totalCases,
          deviation_count: deviationCount,
          deviation_rate: deviationRate.toFixed(2),
        },
      },
      'Officer profile retrieved successfully'
    );
  } catch (error) {
    next(error);
  }
};

const buildOfficerProfile = async (req, res, next) => {
  try {
    const { officer_id } = req.body;

    if (!officer_id) {
      return errorResponse(res, 'Officer ID required', 400);
    }

    const officer = await Officer.findByPk(officer_id);
    if (!officer) {
      return errorResponse(res, 'Officer not found', 404);
    }

    // Get logs and deviations
    const logs = await WorkflowLog.findAll({
      where: { officer_id },
      order: [['timestamp', 'ASC']],
    });

    const deviations = await Deviation.findAll({
      where: { officer_id },
    });

    // Format for AI service
    const formattedLogs = logs.map(log => ({
      case_id: log.case_id,
      officer_id: log.officer_id,
      step_name: log.step_name,
      timestamp: log.timestamp.toISOString(),
    }));

    const formattedDeviations = deviations.map(dev => ({
      case_id: dev.case_id,
      deviation_type: dev.deviation_type,
      severity: dev.severity,
      detected_at: dev.detected_at.toISOString(),
    }));

    // Build profile using AI service
    const profileResult = await aiService.buildBehavioralProfile(
      officer_id,
      formattedLogs,
      formattedDeviations
    );

    // Save profile
    const profile = await BehavioralProfile.create({
      officer_id,
      profile_date: new Date(),
      total_cases: profileResult.total_cases,
      deviation_count: profileResult.deviation_count,
      deviation_rate: profileResult.deviation_rate,
      average_workload: profileResult.average_workload,
      risk_score: profileResult.risk_score,
      patterns: profileResult.patterns || {},
    });

    return successResponse(res, profile, 'Officer profile built successfully', 201);
  } catch (error) {
    next(error);
  }
};

const detectPatterns = async (req, res, next) => {
  try {
    const { officer_id } = req.query;

    let patterns;

    if (officer_id) {
      // Get patterns for specific officer
      patterns = await BehavioralPattern.findAll({
        where: { officer_id },
        include: [
          {
            model: Officer,
            attributes: ['id', 'name', 'role'],
          },
        ],
        order: [['confidence_score', 'DESC']],
      });
    } else {
      // Get all patterns
      patterns = await BehavioralPattern.findAll({
        include: [
          {
            model: Officer,
            attributes: ['id', 'name', 'role'],
          },
        ],
        order: [['confidence_score', 'DESC']],
      });
    }

    return successResponse(res, patterns, 'Behavioral patterns retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const analyzePatterns = async (req, res, next) => {
  try {
    const { officer_id } = req.body;

    const officer = await Officer.findByPk(officer_id);
    if (!officer) {
      return errorResponse(res, 'Officer not found', 404);
    }

    const logs = await WorkflowLog.findAll({
      where: { officer_id },
      order: [['timestamp', 'ASC']],
    });

    const deviations = await Deviation.findAll({
      where: { officer_id },
    });

    const formattedLogs = logs.map(log => ({
      case_id: log.case_id,
      officer_id: log.officer_id,
      step_name: log.step_name,
      timestamp: log.timestamp.toISOString(),
    }));

    const formattedDeviations = deviations.map(dev => ({
      case_id: dev.case_id,
      deviation_type: dev.deviation_type,
      severity: dev.severity,
      detected_at: dev.detected_at.toISOString(),
    }));

    // Detect patterns using AI service
    const patternResult = await aiService.detectPatterns(
      officer_id,
      formattedLogs,
      formattedDeviations
    );

    // Save patterns
    const savedPatterns = [];
    for (const pattern of patternResult.patterns) {
      const saved = await BehavioralPattern.create({
        officer_id,
        pattern_type: pattern.pattern_type,
        description: pattern.description,
        trigger_condition: pattern.trigger_condition,
        frequency: pattern.frequency || 1,
        confidence_score: pattern.confidence_score,
        first_detected: new Date(),
        last_detected: new Date(),
      });
      savedPatterns.push(saved);
    }

    return successResponse(
      res,
      savedPatterns,
      'Behavioral patterns analyzed successfully',
      201
    );
  } catch (error) {
    next(error);
  }
};

const getRiskMatrix = async (req, res, next) => {
  try {
    const officers = await Officer.findAll({
      include: [
        {
          model: Deviation,
          as: 'deviations',
          attributes: ['severity'],
        },
      ],
    });

    const riskMatrix = officers.map(officer => {
      const deviations = officer.deviations || [];
      const criticalCount = deviations.filter(d => d.severity === 'critical').length;
      const highCount = deviations.filter(d => d.severity === 'high').length;
      const mediumCount = deviations.filter(d => d.severity === 'medium').length;
      const lowCount = deviations.filter(d => d.severity === 'low').length;

      const riskScore =
        criticalCount * 10 + highCount * 5 + mediumCount * 2 + lowCount * 1;

      return {
        officer_id: officer.id,
        officer_name: officer.name,
        role: officer.role,
        department: officer.department,
        total_deviations: deviations.length,
        critical: criticalCount,
        high: highCount,
        medium: mediumCount,
        low: lowCount,
        risk_score: riskScore,
      };
    });

    // Sort by risk score
    riskMatrix.sort((a, b) => b.risk_score - a.risk_score);

    return successResponse(res, riskMatrix, 'Risk matrix retrieved successfully');
  } catch (error) {
    next(error);
  }
};

module.exports = {
  listOfficers,
  getOfficerProfile,
  buildOfficerProfile,
  detectPatterns,
  analyzePatterns,
  getRiskMatrix,
};
