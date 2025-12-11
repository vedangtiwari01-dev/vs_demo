const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const StressTestScenario = sequelize.define('StressTestScenario', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  name: {
    type: DataTypes.STRING(255),
    allowNull: false,
  },
  description: {
    type: DataTypes.TEXT,
    allowNull: true,
  },
  scenario_type: {
    type: DataTypes.STRING(100),
    allowNull: false,
    comment: 'regulatory_change, officer_shortage, system_downtime, peak_load',
  },
  parameters: {
    type: DataTypes.JSON,
    allowNull: false,
  },
}, {
  tableName: 'stress_test_scenarios',
  timestamps: true,
  createdAt: 'created_at',
  updatedAt: 'updated_at',
});

module.exports = StressTestScenario;
