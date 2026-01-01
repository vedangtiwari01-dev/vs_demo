const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');
const SOP = require('./sop.model');

const SOPRule = sequelize.define('SOPRule', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  sop_id: {
    type: DataTypes.INTEGER,
    allowNull: false,
    references: {
      model: 'sops',
      key: 'id',
    },
  },
  rule_type: {
    type: DataTypes.STRING(100),
    allowNull: false,
    comment: 'sequence, approval, timing, eligibility, credit_risk, kyc, aml, documentation, collateral, disbursement, post_disbursement_qc, collection, restructuring, regulatory, data_quality, operational',
  },
  rule_description: {
    type: DataTypes.TEXT,
    allowNull: false,
  },
  step_number: {
    type: DataTypes.INTEGER,
    allowNull: true,
  },
  required_fields: {
    type: DataTypes.JSON,
    allowNull: true,
  },
  condition_logic: {
    type: DataTypes.JSON,
    allowNull: true,
  },
  severity: {
    type: DataTypes.STRING(20),
    defaultValue: 'medium',
    comment: 'low, medium, high, critical',
  },
}, {
  tableName: 'sop_rules',
  timestamps: true,
  createdAt: 'created_at',
  updatedAt: 'updated_at',
});

// Define associations
SOP.hasMany(SOPRule, { foreignKey: 'sop_id', as: 'rules' });
SOPRule.belongsTo(SOP, { foreignKey: 'sop_id' });

module.exports = SOPRule;
