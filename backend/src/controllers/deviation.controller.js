const { Deviation, Officer, SOPRule } = require('../models');
const { successResponse, errorResponse } = require('../utils/response');
const { Op } = require('sequelize');
const { sequelize } = require('../config/database');

const listDeviations = async (req, res, next) => {
  try {
    const {
      officer_id,
      deviation_type,
      severity,
      start_date,
      end_date,
      limit = 50,
      offset = 0,
    } = req.query;

    const where = {};
    if (officer_id) where.officer_id = officer_id;
    if (deviation_type) where.deviation_type = deviation_type;
    if (severity) where.severity = severity;
    if (start_date || end_date) {
      where.detected_at = {};
      if (start_date) where.detected_at[Op.gte] = new Date(start_date);
      if (end_date) where.detected_at[Op.lte] = new Date(end_date);
    }

    const deviations = await Deviation.findAll({
      where,
      include: [
        {
          model: Officer,
          attributes: ['id', 'name', 'role', 'department'],
        },
        {
          model: SOPRule,
          attributes: ['id', 'rule_type', 'rule_description'],
        },
      ],
      order: [['detected_at', 'DESC']],
      limit: parseInt(limit),
      offset: parseInt(offset),
    });

    const total = await Deviation.count({ where });

    return successResponse(
      res,
      { deviations, total },
      'Deviations retrieved successfully'
    );
  } catch (error) {
    next(error);
  }
};

const getDeviationById = async (req, res, next) => {
  try {
    const { id } = req.params;

    const deviation = await Deviation.findByPk(id, {
      include: [
        {
          model: Officer,
          attributes: ['id', 'name', 'role', 'department'],
        },
        {
          model: SOPRule,
          attributes: ['id', 'rule_type', 'rule_description', 'severity'],
        },
      ],
    });

    if (!deviation) {
      return errorResponse(res, 'Deviation not found', 404);
    }

    return successResponse(res, deviation, 'Deviation retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const getDeviationSummary = async (req, res, next) => {
  try {
    const total = await Deviation.count();

    const bySeverity = await Deviation.findAll({
      attributes: [
        'severity',
        [sequelize.fn('COUNT', sequelize.col('id')), 'count'],
      ],
      group: ['severity'],
    });

    const byType = await Deviation.findAll({
      attributes: [
        'deviation_type',
        [sequelize.fn('COUNT', sequelize.col('id')), 'count'],
      ],
      group: ['deviation_type'],
    });

    const byOfficer = await Deviation.findAll({
      attributes: [
        'officer_id',
        [sequelize.fn('COUNT', sequelize.col('id')), 'count'],
      ],
      group: ['officer_id'],
      include: [
        {
          model: Officer,
          attributes: ['name', 'role'],
        },
      ],
      limit: 10,
      order: [[sequelize.fn('COUNT', sequelize.col('id')), 'DESC']],
    });

    return successResponse(
      res,
      {
        total,
        by_severity: bySeverity,
        by_type: byType,
        top_officers: byOfficer,
      },
      'Deviation summary retrieved successfully'
    );
  } catch (error) {
    next(error);
  }
};

const getDeviationsByOfficer = async (req, res, next) => {
  try {
    const deviations = await Deviation.findAll({
      attributes: [
        'officer_id',
        [sequelize.fn('COUNT', sequelize.col('Deviation.id')), 'deviation_count'],
        [sequelize.fn('AVG', sequelize.cast(sequelize.col('Deviation.severity'), 'INTEGER')), 'avg_severity'],
      ],
      include: [
        {
          model: Officer,
          attributes: ['id', 'name', 'role', 'department'],
        },
      ],
      group: ['officer_id', 'Officer.id'],
      order: [[sequelize.fn('COUNT', sequelize.col('Deviation.id')), 'DESC']],
    });

    return successResponse(res, deviations, 'Deviations by officer retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const getDeviationsByType = async (req, res, next) => {
  try {
    const deviations = await Deviation.findAll({
      attributes: [
        'deviation_type',
        'severity',
        [sequelize.fn('COUNT', sequelize.col('id')), 'count'],
      ],
      group: ['deviation_type', 'severity'],
      order: [[sequelize.fn('COUNT', sequelize.col('id')), 'DESC']],
    });

    return successResponse(res, deviations, 'Deviations by type retrieved successfully');
  } catch (error) {
    next(error);
  }
};

module.exports = {
  listDeviations,
  getDeviationById,
  getDeviationSummary,
  getDeviationsByOfficer,
  getDeviationsByType,
};
