const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const WorkflowLog = sequelize.define('WorkflowLog', {
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
  step_name: {
    type: DataTypes.STRING(255),
    allowNull: false,
  },
  action: {
    type: DataTypes.STRING(100),
    allowNull: false,
  },
  timestamp: {
    type: DataTypes.DATE,
    allowNull: false,
  },
  duration_seconds: {
    type: DataTypes.INTEGER,
    allowNull: true,
  },
  status: {
    type: DataTypes.STRING(50),
    allowNull: true,
  },
  metadata: {
    type: DataTypes.JSON,
    allowNull: true,
  },
  is_synthetic: {
    type: DataTypes.BOOLEAN,
    defaultValue: false,
  },
  uploaded_at: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW,
  },
}, {
  tableName: 'workflow_logs',
  timestamps: true,
  createdAt: 'created_at',
  updatedAt: 'updated_at',
  indexes: [
    { fields: ['case_id'] },
    { fields: ['officer_id'] },
    { fields: ['timestamp'] },
  ],
});

// Instance methods for notes handling
WorkflowLog.prototype.getNotes = function() {
  /**
   * Extract notes from metadata JSON field
   * @returns {string|null} Notes text or null if not present
   */
  if (this.metadata && this.metadata.notes) {
    return this.metadata.notes;
  }
  return null;
};

WorkflowLog.prototype.setNotes = function(notes) {
  /**
   * Store notes in metadata JSON field
   * @param {string} notes - Notes text to store
   */
  if (!this.metadata) {
    this.metadata = {};
  }
  this.metadata.notes = notes;
};

WorkflowLog.prototype.hasNotes = function() {
  /**
   * Check if this log entry has notes
   * @returns {boolean} True if notes exist
   */
  return !!(this.metadata && this.metadata.notes);
};

module.exports = WorkflowLog;
