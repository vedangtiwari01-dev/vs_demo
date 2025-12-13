const { WorkflowLog, Deviation } = require('../models');
const logger = require('../utils/logger');

/**
 * Notes Service
 * Handles extraction and management of notes/comments
 */

/**
 * Extract notes from CSV data and store in WorkflowLog metadata
 * @param {Array<Object>} logs - WorkflowLog records (already created)
 * @param {Array<Object>} csvData - Original CSV data with notes column
 * @param {string} notesColumn - Name of the column containing notes
 * @returns {Promise<number>} Count of logs updated with notes
 */
const extractAndStoreNotesFromCSV = async (logs, csvData, notesColumn) => {
  if (!notesColumn) {
    logger.info('No notes column specified, skipping notes extraction');
    return 0;
  }

  try {
    let notesCount = 0;

    for (let i = 0; i < logs.length && i < csvData.length; i++) {
      const log = logs[i];
      const csvRow = csvData[i];

      const notes = csvRow[notesColumn];
      if (notes && notes.trim() !== '') {
        // Use the helper method to store notes
        log.setNotes(notes.trim());
        // CRITICAL: Mark metadata as changed so Sequelize saves nested JSON changes
        log.changed('metadata', true);
        await log.save();
        notesCount++;
      }
    }

    logger.info(`Extracted and stored notes for ${notesCount} workflow logs`);
    return notesCount;
  } catch (error) {
    logger.error(`Error extracting notes from CSV: ${error.message}`);
    throw error;
  }
};

/**
 * Get notes for all logs in a specific case
 * @param {string} caseId - Case ID
 * @returns {Promise<Object>} Map of log IDs to notes
 */
const getNotesForCase = async (caseId) => {
  try {
    const logs = await WorkflowLog.findAll({
      where: { case_id: caseId },
      order: [['timestamp', 'ASC']]
    });

    const notesMap = {};
    logs.forEach(log => {
      const notes = log.getNotes();
      if (notes) {
        notesMap[log.id] = notes;
      }
    });

    return notesMap;
  } catch (error) {
    logger.error(`Error getting notes for case ${caseId}: ${error.message}`);
    throw error;
  }
};

/**
 * Get notes for workflow analysis (grouped by case_id)
 * @param {Array<string>} caseIds - List of case IDs
 * @returns {Promise<Object>} Map of case_id to combined notes
 */
const getNotesForAnalysis = async (caseIds) => {
  try {
    logger.info(`[getNotesForAnalysis] Fetching logs for ${caseIds.length} case IDs`);

    const logs = await WorkflowLog.findAll({
      where: { case_id: caseIds },
      order: [['case_id', 'ASC'], ['timestamp', 'ASC']]
    });

    logger.info(`[getNotesForAnalysis] Found ${logs.length} workflow logs`);

    // Debug: Check first few logs
    if (logs.length > 0) {
      const sampleLog = logs[0];
      logger.info(`[getNotesForAnalysis] Sample log metadata: ${JSON.stringify(sampleLog.metadata)}`);
      logger.info(`[getNotesForAnalysis] Sample log getNotes(): ${sampleLog.getNotes()}`);
    }

    // Group notes by case_id
    const notesByCase = {};
    let logsWithNotes = 0;
    logs.forEach(log => {
      const notes = log.getNotes();
      if (notes) {
        logsWithNotes++;
        if (!notesByCase[log.case_id]) {
          notesByCase[log.case_id] = [];
        }
        notesByCase[log.case_id].push(`[${log.step_name}] ${notes}`);
      }
    });

    logger.info(`[getNotesForAnalysis] Found ${logsWithNotes} logs with notes out of ${logs.length} total`);

    // Combine multiple notes for each case
    const combinedNotes = {};
    Object.keys(notesByCase).forEach(caseId => {
      combinedNotes[caseId] = notesByCase[caseId].join(' | ');
    });

    logger.info(`Retrieved notes for ${Object.keys(combinedNotes).length} cases`);
    return combinedNotes;
  } catch (error) {
    logger.error(`Error getting notes for analysis: ${error.message}`);
    throw error;
  }
};

/**
 * Update notes for a deviation (manual entry)
 * @param {number} deviationId - Deviation ID
 * @param {string} notes - Notes text
 * @param {string} userId - User who added the notes (optional)
 * @returns {Promise<Object>} Updated deviation
 */
const updateDeviationNotes = async (deviationId, notes, userId = null) => {
  try {
    const deviation = await Deviation.findByPk(deviationId);
    if (!deviation) {
      throw new Error('Deviation not found');
    }

    deviation.notes = notes;

    // Update context metadata if user info provided
    if (userId) {
      const context = deviation.context || {};
      context.notes_added_by = userId;
      context.notes_added_at = new Date().toISOString();
      deviation.context = context;
    }

    await deviation.save();

    logger.info(`Updated notes for deviation ${deviationId}`);
    return deviation;
  } catch (error) {
    logger.error(`Error updating deviation notes: ${error.message}`);
    throw error;
  }
};

/**
 * Get statistics about notes coverage
 * @returns {Promise<Object>} Notes statistics
 */
const getNotesStatistics = async () => {
  try {
    const totalLogs = await WorkflowLog.count();
    const logsWithNotes = await WorkflowLog.count({
      where: {
        metadata: {
          notes: {
            $ne: null
          }
        }
      }
    });

    const totalDeviations = await Deviation.count();
    const deviationsWithNotes = await Deviation.count({
      where: {
        notes: {
          $ne: null
        }
      }
    });

    return {
      workflow_logs: {
        total: totalLogs,
        with_notes: logsWithNotes,
        percentage: totalLogs > 0 ? Math.round((logsWithNotes / totalLogs) * 100) : 0
      },
      deviations: {
        total: totalDeviations,
        with_notes: deviationsWithNotes,
        percentage: totalDeviations > 0 ? Math.round((deviationsWithNotes / totalDeviations) * 100) : 0
      }
    };
  } catch (error) {
    logger.error(`Error getting notes statistics: ${error.message}`);
    throw error;
  }
};

module.exports = {
  extractAndStoreNotesFromCSV,
  getNotesForCase,
  getNotesForAnalysis,
  updateDeviationNotes,
  getNotesStatistics
};
