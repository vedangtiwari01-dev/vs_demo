const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const SOP = sequelize.define('SOP', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  title: {
    type: DataTypes.STRING(255),
    allowNull: false,
  },
  version: {
    type: DataTypes.STRING(50),
    allowNull: true,
  },
  file_path: {
    type: DataTypes.STRING(500),
    allowNull: false,
  },
  file_type: {
    type: DataTypes.STRING(10),
    allowNull: false,
  },
  uploaded_at: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW,
  },
  processed: {
    type: DataTypes.BOOLEAN,
    defaultValue: false,
  },
  status: {
    type: DataTypes.STRING(50),
    defaultValue: 'pending',
  },
  metadata: {
    type: DataTypes.JSON,
    allowNull: true,
  },
}, {
  tableName: 'sops',
  timestamps: true,
  createdAt: 'created_at',
  updatedAt: 'updated_at',
});

module.exports = SOP;
