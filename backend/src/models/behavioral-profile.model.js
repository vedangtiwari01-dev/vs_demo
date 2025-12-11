const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');
const Officer = require('./officer.model');

const BehavioralProfile = sequelize.define('BehavioralProfile', {
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
  profile_date: {
    type: DataTypes.DATEONLY,
    allowNull: false,
  },
  total_cases: {
    type: DataTypes.INTEGER,
    defaultValue: 0,
  },
  deviation_count: {
    type: DataTypes.INTEGER,
    defaultValue: 0,
  },
  deviation_rate: {
    type: DataTypes.DECIMAL(5, 2),
    allowNull: true,
  },
  average_workload: {
    type: DataTypes.DECIMAL(10, 2),
    allowNull: true,
  },
  risk_score: {
    type: DataTypes.DECIMAL(5, 2),
    allowNull: true,
  },
  patterns: {
    type: DataTypes.JSON,
    allowNull: true,
  },
}, {
  tableName: 'behavioral_profiles',
  timestamps: true,
  createdAt: 'created_at',
  updatedAt: 'updated_at',
});

// Define associations
Officer.hasMany(BehavioralProfile, { foreignKey: 'officer_id', as: 'profiles' });
BehavioralProfile.belongsTo(Officer, { foreignKey: 'officer_id' });

module.exports = BehavioralProfile;
