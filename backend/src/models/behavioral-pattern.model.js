const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');
const Officer = require('./officer.model');

const BehavioralPattern = sequelize.define('BehavioralPattern', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  officer_id: {
    type: DataTypes.STRING(100),
    allowNull: false,
    references: {
      model: 'officers',
      key: 'id',
    },
  },
  pattern_type: {
    type: DataTypes.STRING(100),
    allowNull: false,
    comment: 'workload_threshold, time_based, step_specific',
  },
  description: {
    type: DataTypes.TEXT,
    allowNull: false,
  },
  trigger_condition: {
    type: DataTypes.JSON,
    allowNull: true,
  },
  frequency: {
    type: DataTypes.INTEGER,
    defaultValue: 1,
  },
  confidence_score: {
    type: DataTypes.DECIMAL(5, 2),
    allowNull: true,
  },
  first_detected: {
    type: DataTypes.DATE,
    allowNull: false,
  },
  last_detected: {
    type: DataTypes.DATE,
    allowNull: false,
  },
}, {
  tableName: 'behavioral_patterns',
  timestamps: true,
  createdAt: 'created_at',
  updatedAt: 'updated_at',
});

// Define associations
Officer.hasMany(BehavioralPattern, { foreignKey: 'officer_id', as: 'patterns' });
BehavioralPattern.belongsTo(Officer, { foreignKey: 'officer_id' });

module.exports = BehavioralPattern;
