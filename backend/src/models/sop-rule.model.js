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
    comment: 'Conditional IF-THEN logic for dynamic rule evaluation',
  },
  severity: {
    type: DataTypes.STRING(20),
    defaultValue: 'medium',
    comment: 'low, medium, high, critical',
  },
  // NEW FIELDS FOR ENHANCED FEATURES (2025 Q1)
  temporal_constraint: {
    type: DataTypes.JSON,
    allowNull: true,
    comment: 'Step-to-step timing constraints (e.g., {"step_a": "Risk Assessment", "step_b": "Manager Approval", "max_hours": 48})',
  },
  product_types: {
    type: DataTypes.JSON,
    allowNull: true,
    comment: 'Product types this rule applies to (e.g., ["Home Loan", "Gold Loan"] or ["All"])',
  },
  customer_segments: {
    type: DataTypes.JSON,
    allowNull: true,
    comment: 'Customer segments this rule applies to (e.g., ["Priority", "VIP"] or ["All"])',
  },
  channels: {
    type: DataTypes.JSON,
    allowNull: true,
    comment: 'Channels this rule applies to (e.g., ["Digital", "Branch"] or ["All"])',
  },
  geography: {
    type: DataTypes.JSON,
    allowNull: true,
    comment: 'Geographic regions this rule applies to (e.g., ["Urban", "Rural"] or ["All"])',
  },
  exceptions: {
    type: DataTypes.JSON,
    allowNull: true,
    comment: 'Exception cases for this rule',
  },
  calculation_formula: {
    type: DataTypes.TEXT,
    allowNull: true,
    comment: 'Mathematical formula for calculation-based rules (e.g., "LTV = loan_amount / collateral_value")',
  },
  threshold_value: {
    type: DataTypes.FLOAT,
    allowNull: true,
    comment: 'Numeric threshold value (e.g., 10000 for "$10,000+", 0.8 for "80%")',
  },
  field_dependencies: {
    type: DataTypes.JSON,
    allowNull: true,
    comment: 'List of fields this rule depends on (e.g., ["loan_amount", "collateral_value"])',
  },
  regulatory_reference: {
    type: DataTypes.STRING(500),
    allowNull: true,
    comment: 'Legal/regulatory reference (e.g., "RBI Master Circular", "Basel III")',
  },
  timing_constraint: {
    type: DataTypes.STRING(200),
    allowNull: true,
    comment: 'Human-readable timing requirement (e.g., "within 48 hours", "same business day")',
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
