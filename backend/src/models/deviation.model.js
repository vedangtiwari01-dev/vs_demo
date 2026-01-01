const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');
const Officer = require('./officer.model');
const SOPRule = require('./sop-rule.model');

const Deviation = sequelize.define('Deviation', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  case_id: {
    type: DataTypes.STRING(100),
    allowNull: false,
  },
  officer_id: {
    type: DataTypes.STRING(100),
    allowNull: false,
  },
  deviation_type: {
    type: DataTypes.STRING(100),
    allowNull: false,
    comment: 'missing_step, wrong_sequence, unexpected_step, duplicate_step, skipped_mandatory_subprocess, missing_approval, insufficient_approval_hierarchy, unauthorized_approver, self_approval_violation, escalation_missing, timing_violation, tat_breach, cutoff_breach, post_disbursement_qc_delay, ineligible_age, ineligible_tenor, emi_to_income_breach, low_score_approved_without_exception, kyc_incomplete_progression, sanctions_hit_not_rejected, pep_no_edd_or_extra_approval, missing_mandatory_document, expired_document_used, legal_clearance_missing, collateral_docs_incomplete, ltv_breach, valuation_missing_or_stale, security_not_created, pre_disbursement_condition_unmet, mandate_not_set_before_disbursement, incorrect_disbursement_amount, post_disbursement_qc_missing, collection_escalation_delay, unauthorized_restructure, unauthorized_writeoff, classification_mismatch, provisioning_shortfall, regulatory_report_missing_or_late, missing_core_field, invalid_format, inconsistent_value_across_steps, duplicate_active_case, audit_trail_missing',
  },
  rule_id: {
    type: DataTypes.INTEGER,
    allowNull: true,
    references: {
      model: 'sop_rules',
      key: 'id',
    },
  },
  severity: {
    type: DataTypes.STRING(20),
    allowNull: false,
    comment: 'low, medium, high, critical',
  },
  description: {
    type: DataTypes.TEXT,
    allowNull: false,
  },
  expected_behavior: {
    type: DataTypes.TEXT,
    allowNull: true,
  },
  actual_behavior: {
    type: DataTypes.TEXT,
    allowNull: true,
  },
  notes: {
    type: DataTypes.TEXT,
    allowNull: true,
    comment: 'User/analyst notes and comments about the deviation',
  },
  llm_reasoning: {
    type: DataTypes.TEXT,
    allowNull: true,
    comment: 'Claude AI reasoning and explanation for this deviation',
  },
  detected_at: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW,
  },
  context: {
    type: DataTypes.JSON,
    allowNull: true,
  },
}, {
  tableName: 'deviations',
  timestamps: true,
  createdAt: 'created_at',
  updatedAt: 'updated_at',
  indexes: [
    { fields: ['officer_id'] },
    { fields: ['deviation_type'] },
    { fields: ['detected_at'] },
  ],
});

// Define associations
Officer.hasMany(Deviation, { foreignKey: 'officer_id', as: 'deviations' });
Deviation.belongsTo(Officer, { foreignKey: 'officer_id' });

SOPRule.hasMany(Deviation, { foreignKey: 'rule_id', as: 'deviations' });
Deviation.belongsTo(SOPRule, { foreignKey: 'rule_id' });

module.exports = Deviation;
