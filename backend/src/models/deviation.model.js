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
    comment: 'missing_step, wrong_sequence, unauthorized_approval, timing_violation',
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
