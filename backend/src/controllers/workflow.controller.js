const { WorkflowLog, Officer, Deviation, SOPRule } = require('../models');
const aiService = require('../services/ai-integration.service');
const { successResponse, errorResponse } = require('../utils/response');
const Papa = require('papaparse');
const fs = require('fs').promises;

const uploadWorkflowLogs = async (req, res, next) => {
  try {
    const file = req.file;

    if (!file) {
      return errorResponse(res, 'No file uploaded', 400);
    }

    // Read and parse file
    const fileContent = await fs.readFile(file.path, 'utf8');
    let logs;

    if (file.originalname.endsWith('.csv')) {
      const parsed = Papa.parse(fileContent, {
        header: true,
        skipEmptyLines: true,
      });
      logs = parsed.data;
    } else if (file.originalname.endsWith('.json')) {
      logs = JSON.parse(fileContent);
    } else {
      return errorResponse(res, 'Unsupported file format', 400);
    }

    // Validate that we have data
    if (logs.length === 0) {
      return errorResponse(res, 'CSV file is empty or invalid', 400);
    }

    // Check first row for column names
    const firstRow = logs[0];
    const columns = Object.keys(firstRow);
    console.log('CSV columns found:', columns);

    // Flexible column mapping
    const getColumnValue = (log, possibleNames) => {
      for (const name of possibleNames) {
        // Check exact match
        if (log[name] !== undefined && log[name] !== null && log[name] !== '') {
          return log[name];
        }
        // Check case-insensitive match
        const lowerName = name.toLowerCase();
        const matchingKey = Object.keys(log).find(k => k.toLowerCase() === lowerName);
        if (matchingKey && log[matchingKey] !== undefined && log[matchingKey] !== null && log[matchingKey] !== '') {
          return log[matchingKey];
        }
      }
      return null;
    };

    // Transform and save logs
    const savedLogs = [];
    const officers = new Set();
    const errors = [];

    for (let i = 0; i < logs.length; i++) {
      const log = logs[i];

      try {
        const caseId = getColumnValue(log, ['case_id', 'caseId', 'CaseID', 'Case ID', 'case', 'Loan_ID', 'LoanID', 'loan_id']);
        const officerId = getColumnValue(log, ['officer_id', 'officerId', 'OfficerID', 'Officer ID', 'officer', 'User', 'user', 'user_id']);
        const stepName = getColumnValue(log, ['step_name', 'stepName', 'StepName', 'Step Name', 'step', 'Step', 'Activity', 'activity', 'action']);
        const action = getColumnValue(log, ['action', 'Action', 'Decision', 'decision']) || 'completed';
        const timestamp = getColumnValue(log, ['timestamp', 'Timestamp', 'date', 'Date', 'time', 'Time']);
        const duration = getColumnValue(log, ['duration_seconds', 'duration', 'Duration']);
        const status = getColumnValue(log, ['status', 'Status', 'Decision', 'decision']) || 'completed';

        // Validate required fields
        if (!caseId) {
          errors.push(`Row ${i + 2}: Missing case_id`);
          continue;
        }
        if (!officerId) {
          errors.push(`Row ${i + 2}: Missing officer_id`);
          continue;
        }
        if (!stepName) {
          errors.push(`Row ${i + 2}: Missing step_name`);
          continue;
        }
        if (!timestamp) {
          errors.push(`Row ${i + 2}: Missing timestamp`);
          continue;
        }

        const workflowLog = await WorkflowLog.create({
          case_id: caseId,
          officer_id: officerId,
          step_name: stepName,
          action: action,
          timestamp: new Date(timestamp),
          duration_seconds: duration ? parseInt(duration) : null,
          status: status,
          metadata: {},
          is_synthetic: false,
        });

        savedLogs.push(workflowLog);
        officers.add(officerId);
      } catch (err) {
        errors.push(`Row ${i + 2}: ${err.message}`);
      }
    }

    // Return error if no logs were saved
    if (savedLogs.length === 0) {
      return errorResponse(res, `Failed to import any logs. Errors:\n${errors.join('\n')}`, 400);
    }

    // Create officer records if they don't exist
    for (const officerId of officers) {
      await Officer.findOrCreate({
        where: { id: officerId },
        defaults: {
          id: officerId,
          name: `Officer ${officerId}`,
          role: 'Loan Officer',
        },
      });
    }

    const message = errors.length > 0
      ? `Workflow logs uploaded with ${errors.length} error(s)`
      : 'Workflow logs uploaded successfully';

    return successResponse(
      res,
      {
        total_logs: savedLogs.length,
        unique_cases: new Set(savedLogs.map(l => l.case_id)).size,
        unique_officers: officers.size,
        errors: errors.length > 0 ? errors : undefined,
      },
      message,
      201
    );
  } catch (error) {
    next(error);
  }
};

const listWorkflowLogs = async (req, res, next) => {
  try {
    const { case_id, officer_id, limit = 100, offset = 0 } = req.query;

    const where = {};
    if (case_id) where.case_id = case_id;
    if (officer_id) where.officer_id = officer_id;

    const logs = await WorkflowLog.findAll({
      where,
      order: [['timestamp', 'DESC']],
      limit: parseInt(limit),
      offset: parseInt(offset),
    });

    const total = await WorkflowLog.count({ where });

    return successResponse(res, { logs, total }, 'Workflow logs retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const getWorkflowByCase = async (req, res, next) => {
  try {
    const { caseId } = req.params;

    const logs = await WorkflowLog.findAll({
      where: { case_id: caseId },
      order: [['timestamp', 'ASC']],
    });

    if (logs.length === 0) {
      return errorResponse(res, 'No workflow found for this case', 404);
    }

    return successResponse(res, logs, 'Case workflow retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const analyzeWorkflow = async (req, res, next) => {
  try {
    // Get all logs
    const logs = await WorkflowLog.findAll({
      where: { is_synthetic: false },
      order: [['case_id', 'ASC'], ['timestamp', 'ASC']],
    });

    // Get all rules
    const rules = await SOPRule.findAll();

    if (rules.length === 0) {
      return errorResponse(res, 'No SOP rules found. Please upload and process an SOP first.', 400);
    }

    // Format logs for AI service
    const formattedLogs = logs.map(log => ({
      case_id: log.case_id,
      officer_id: log.officer_id,
      step_name: log.step_name,
      action: log.action,
      timestamp: log.timestamp.toISOString(),
      duration_seconds: log.duration_seconds,
      status: log.status,
    }));

    // Format rules for AI service
    const formattedRules = rules.map(rule => ({
      id: rule.id,
      type: rule.rule_type,
      description: rule.rule_description,
      step_number: rule.step_number,
      severity: rule.severity,
    }));

    // Detect deviations using AI service
    const deviationResult = await aiService.detectDeviations(formattedLogs, formattedRules);

    // Extract notes for all cases with deviations
    const caseIds = [...new Set(deviationResult.deviations.map(d => d.case_id))];
    console.log('[analyzeWorkflow] Detected deviations for cases:', caseIds);

    const notesByCase = await notesService.getNotesForAnalysis(caseIds);
    console.log('[analyzeWorkflow] Notes retrieved for cases:', Object.keys(notesByCase));
    console.log('[analyzeWorkflow] Sample notes:', Object.values(notesByCase)[0] || 'No notes found');

    // Save deviations to database with notes attached
    const savedDeviations = [];
    for (const dev of deviationResult.deviations) {
      const deviation = await Deviation.create({
        case_id: dev.case_id,
        officer_id: dev.officer_id,
        deviation_type: dev.deviation_type,
        rule_id: dev.rule_id || null,
        severity: dev.severity,
        description: dev.description,
        expected_behavior: dev.expected_behavior,
        actual_behavior: dev.actual_behavior,
        context: dev.context || {},
        notes: notesByCase[dev.case_id] || null,  // ✅ Attach notes from WorkflowLog
      });
      savedDeviations.push(deviation);
    }

    return successResponse(
      res,
      {
        total_deviations: savedDeviations.length,
        deviations: savedDeviations,
        summary: {
          critical: savedDeviations.filter(d => d.severity === 'critical').length,
          high: savedDeviations.filter(d => d.severity === 'high').length,
          medium: savedDeviations.filter(d => d.severity === 'medium').length,
          low: savedDeviations.filter(d => d.severity === 'low').length,
        },
      },
      'Workflow analysis completed'
    );
  } catch (error) {
    next(error);
  }
};

const columnMappingService = require('../services/column-mapping.service');
const notesService = require('../services/notes.service');

const analyzeHeaders = async (req, res, next) => {
  try {
    const file = req.file;

    if (!file) {
      return errorResponse(res, 'No file uploaded', 400);
    }

    // Read and parse CSV file
    const fileContent = await fs.readFile(file.path, 'utf8');
    const parsed = Papa.parse(fileContent, {
      header: true,
      skipEmptyLines: true,
    });

    if (parsed.data.length === 0) {
      return errorResponse(res, 'CSV file is empty', 400);
    }

    // Get headers and first 3 rows for AI analysis
    const headers = Object.keys(parsed.data[0]);
    const sampleRows = parsed.data.slice(0, 3);

    console.log('[analyzeHeaders] CSV headers:', headers);
    console.log('[analyzeHeaders] Sample rows:', JSON.stringify(sampleRows).substring(0, 200));

    // Call AI service for intelligent mapping
    const mappingResult = await columnMappingService.analyzeHeaders(headers, sampleRows);

    console.log('[analyzeHeaders] Mapping result:', JSON.stringify(mappingResult).substring(0, 500));

    // Validate that we got mappings
    if (!mappingResult || !mappingResult.mappings) {
      console.error('[analyzeHeaders] AI service returned no mappings:', mappingResult);
      return errorResponse(res, 'AI service failed to generate column mappings', 500);
    }

    return successResponse(
      res,
      {
        headers,
        mapping_suggestions: mappingResult.mappings,
        notes_column: mappingResult.notes_column || null,
        unmapped_columns: mappingResult.unmapped_columns || [],
        warnings: mappingResult.warnings || []
      },
      'CSV headers analyzed successfully'
    );
  } catch (error) {
    console.error('[analyzeHeaders] Error:', error);
    next(error);
  }
};

const uploadWithMapping = async (req, res, next) => {
  try {
    const file = req.file;
    const { mapping, sop_id } = req.body;

    console.log('[uploadWithMapping] Received mapping field type:', typeof mapping);
    console.log('[uploadWithMapping] Mapping value:', typeof mapping === 'string' ? mapping.substring(0, 200) : mapping);

    if (!file) {
      return errorResponse(res, 'No file uploaded', 400);
    }

    if (!mapping || mapping === 'undefined' || mapping === 'null') {
      console.error('[uploadWithMapping] Invalid mapping received:', mapping);
      return errorResponse(res, 'Column mapping not provided or invalid', 400);
    }

    // Parse mapping from JSON string if needed
    let columnMapping;
    try {
      columnMapping = typeof mapping === 'string' ? JSON.parse(mapping) : mapping;
    } catch (parseError) {
      console.error('[uploadWithMapping] JSON parse error:', parseError.message);
      return errorResponse(res, 'Invalid JSON in column mapping', 400);
    }

    console.log('[uploadWithMapping] Parsed column mapping:', JSON.stringify(columnMapping).substring(0, 300));

    // Validate mapping format (should be simple strings: { "CSV_Col": "system_field" })
    for (const [csvColumn, mappingValue] of Object.entries(columnMapping)) {
      if (typeof mappingValue !== 'string') {
        console.error(`[uploadWithMapping] Invalid mapping format for ${csvColumn}:`, mappingValue);
        return errorResponse(res, `Invalid mapping format: ${csvColumn} must map to a string value`, 400);
      }
    }

    // Validate mapping has all required fields
    const validation = columnMappingService.validateMapping(columnMapping);
    if (!validation.isValid) {
      return errorResponse(res, validation.message, 400);
    }

    // Read and parse file
    const fileContent = await fs.readFile(file.path, 'utf8');
    const parsed = Papa.parse(fileContent, {
      header: true,
      skipEmptyLines: true,
    });

    if (parsed.data.length === 0) {
      return errorResponse(res, 'CSV file is empty', 400);
    }

    // Apply mapping to transform data
    const transformedData = columnMappingService.applyMapping(parsed.data, columnMapping);

    // Detect notes column
    const notesColumn = columnMappingService.detectNotesColumn(columnMapping);

    // Debug logging
    console.log('[uploadWithMapping] Column mapping used:', JSON.stringify(columnMapping, null, 2));
    console.log('[uploadWithMapping] Detected notes column:', notesColumn);
    console.log('[uploadWithMapping] CSV has', Object.keys(parsed.data[0] || {}).length, 'columns');
    console.log('[uploadWithMapping] Transformed', transformedData.length, 'rows');

    // Create workflow logs
    const savedLogs = [];
    const officers = new Set();
    const errors = [];

    for (let i = 0; i < transformedData.length; i++) {
      const row = transformedData[i];

      try {
        // Validate required fields
        if (!row.case_id || !row.officer_id || !row.step_name || !row.timestamp) {
          errors.push(`Row ${i + 2}: Missing required field`);
          continue;
        }

        const workflowLog = await WorkflowLog.create({
          case_id: row.case_id,
          officer_id: row.officer_id,
          step_name: row.step_name,
          action: row.action || 'completed',
          timestamp: new Date(row.timestamp),
          duration_seconds: row.duration_seconds ? parseInt(row.duration_seconds) : null,
          status: row.status || 'completed',
          metadata: {
            original_filename: file.originalname
          },
          is_synthetic: false,
        });

        savedLogs.push(workflowLog);
        officers.add(row.officer_id);
      } catch (err) {
        errors.push(`Row ${i + 2}: ${err.message}`);
      }
    }

    if (savedLogs.length === 0) {
      return errorResponse(res, `Failed to import any logs. Errors:\n${errors.join('\n')}`, 400);
    }

    // Extract and store notes if notes column exists
    let notesCount = 0;
    if (notesColumn) {
      console.log('[uploadWithMapping] Extracting notes from column:', notesColumn);
      console.log('[uploadWithMapping] Sample CSV row:', JSON.stringify(parsed.data[0], null, 2));
      console.log('[uploadWithMapping] Number of logs to process:', savedLogs.length);

      notesCount = await notesService.extractAndStoreNotesFromCSV(
        savedLogs,
        parsed.data,
        notesColumn
      );

      console.log('[uploadWithMapping] Notes extraction complete. Count:', notesCount);
    } else {
      console.log('[uploadWithMapping] No notes column detected in mapping');
    }

    // Create officer records
    for (const officerId of officers) {
      await Officer.findOrCreate({
        where: { id: officerId },
        defaults: {
          id: officerId,
          name: `Officer ${officerId}`,
          role: 'Loan Officer',
        },
      });
    }

    // Save mapping for reuse
    if (sop_id) {
      await columnMappingService.saveMapping(sop_id, columnMapping, Object.keys(parsed.data[0]));
    }

    const message = errors.length > 0
      ? `Workflow logs uploaded with ${errors.length} error(s)`
      : 'Workflow logs uploaded successfully';

    return successResponse(
      res,
      {
        total_logs: savedLogs.length,
        unique_cases: new Set(savedLogs.map(l => l.case_id)).size,
        unique_officers: officers.size,
        notes_imported: notesCount,
        errors: errors.length > 0 ? errors : undefined,
      },
      message,
      201
    );
  } catch (error) {
    next(error);
  }
};

const analyzePatterns = async (req, res, next) => {
  try {
    // Get recent deviations (limit to 50 to avoid timeouts)
    const deviations = await Deviation.findAll({
      order: [['detected_at', 'DESC']],
      limit: 50,
    });

    if (deviations.length === 0) {
      return successResponse(res, {
        message: 'No deviations found for pattern analysis'
      });
    }

    console.log(`[analyzePatterns] Analyzing ${deviations.length} deviations`);

    // Format deviations for AI analysis
    const deviationsWithNotes = deviations.map(dev => ({
      case_id: dev.case_id,
      officer_id: dev.officer_id,
      deviation_type: dev.deviation_type,
      severity: dev.severity,
      description: dev.description,
      expected_behavior: dev.expected_behavior,
      actual_behavior: dev.actual_behavior,
      notes: dev.notes || null
    }));

    // Call AI service for pattern analysis
    console.log('[analyzePatterns] Sending to AI service...');
    const patternAnalysis = await aiService.analyzeDeviationPatterns(deviationsWithNotes);
    console.log('[analyzePatterns] AI analysis complete');

    return successResponse(
      res,
      {
        deviations_analyzed: deviations.length,
        api_calls_made: patternAnalysis.api_calls_made || 1,
        patterns: patternAnalysis
      },
      'Pattern analysis completed'
    );
  } catch (error) {
    next(error);
  }
};

const listWorkflowFiles = async (req, res, next) => {
  try {
    const { sequelize } = require('../config/database');

    // Group workflow logs by upload session (uploaded_at)
    // Each upload session represents one file
    const uploadSessions = await WorkflowLog.findAll({
      attributes: [
        [sequelize.fn('strftime', '%Y-%m-%d %H:%M:%S', sequelize.col('uploaded_at')), 'upload_timestamp'],
        [sequelize.fn('COUNT', sequelize.col('id')), 'total_logs'],
        [sequelize.fn('COUNT', sequelize.fn('DISTINCT', sequelize.col('case_id'))), 'unique_cases'],
        [sequelize.fn('MAX', sequelize.col('is_synthetic')), 'is_generated'],
        [sequelize.fn('MAX', sequelize.col('uploaded_at')), 'uploaded_at'],
        [sequelize.fn('MAX', sequelize.col('metadata')), 'metadata'],
      ],
      group: [sequelize.fn('strftime', '%Y-%m-%d %H:%M:%S', sequelize.col('uploaded_at'))],
      order: [[sequelize.fn('MAX', sequelize.col('uploaded_at')), 'DESC']],
      raw: true,
    });

    // Transform to frontend-expected format
    const files = uploadSessions.map((session, index) => {
      const uploadDate = new Date(session.uploaded_at);
      const dateStr = uploadDate.toISOString().replace(/[-:]/g, '').replace('T', '_').substring(0, 15);

      // Try to get original filename from metadata
      let filename;
      if (session.metadata) {
        try {
          const metadata = typeof session.metadata === 'string'
            ? JSON.parse(session.metadata)
            : session.metadata;

          // Use original filename if available
          if (metadata.original_filename) {
            filename = metadata.original_filename;
          } else if (session.is_generated && metadata.scenario_type) {
            filename = `synthetic_${metadata.scenario_type}_${dateStr}.csv`;
          }
        } catch (e) {
          // If parsing fails, use default
        }
      }

      // Fallback to generated name if no filename found
      if (!filename) {
        filename = session.is_generated
          ? `synthetic_${dateStr}.csv`
          : `workflow_${dateStr}.csv`;
      }

      return {
        id: session.upload_timestamp, // Use timestamp as unique ID
        filename: filename,
        uploaded_at: session.uploaded_at,
        total_logs: parseInt(session.total_logs),
        unique_cases: parseInt(session.unique_cases),
        is_generated: Boolean(session.is_generated),
      };
    });

    return successResponse(res, { files }, 'Workflow files retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const deleteWorkflowFile = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { sequelize } = require('../config/database');

    // The ID is the upload_timestamp in format 'YYYY-MM-DD HH:MM:SS'
    // Delete all logs with this upload timestamp
    const deleted = await WorkflowLog.destroy({
      where: sequelize.where(
        sequelize.fn('strftime', '%Y-%m-%d %H:%M:%S', sequelize.col('uploaded_at')),
        id
      ),
    });

    if (deleted === 0) {
      return errorResponse(res, 'Workflow file not found', 404);
    }

    return successResponse(res, { deleted_count: deleted }, 'Workflow file deleted successfully');
  } catch (error) {
    next(error);
  }
};

module.exports = {
  uploadWorkflowLogs,
  listWorkflowLogs,
  getWorkflowByCase,
  analyzeWorkflow,
  analyzeHeaders,
  uploadWithMapping,
  analyzePatterns,
  listWorkflowFiles,
  deleteWorkflowFile,
};
