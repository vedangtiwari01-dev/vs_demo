const { WorkflowLog, Officer, Deviation, SOPRule, SOP } = require('../models');
const aiService = require('../services/ai-integration.service');
const { successResponse, errorResponse } = require('../utils/response');
const Papa = require('papaparse');
const fs = require('fs').promises;
const crypto = require('crypto');
const logger = require('../utils/clean-logger');

// Store the current analysis session ID (for filtering in analyzePatterns)
let currentAnalysisSessionId = null;

const uploadWorkflowLogs = async (req, res, next) => {
  try {
    const file = req.file;

    if (!file) {
      return errorResponse(res, 'No file uploaded', 400);
    }

    // Generate single upload timestamp for entire batch
    const uploadTimestamp = new Date();

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
    logger.debug('CSV columns found', columns);

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

        // CRITICAL FIX: Extract ALL extended fields to metadata
        const coreFields = ['case_id', 'officer_id', 'step_name', 'action', 'timestamp', 'duration_seconds', 'status'];
        const metadata = {};

        // Add all non-core fields to metadata
        for (const [key, value] of Object.entries(log)) {
          const lowerKey = key.toLowerCase();
          // Skip core fields and empty values
          if (!coreFields.includes(lowerKey) && value !== null && value !== undefined && value !== '') {
            // Convert numeric strings to numbers where appropriate
            if (key.includes('amount') || key.includes('value') || key.includes('score') || key.includes('ratio')) {
              const numValue = parseFloat(value);
              metadata[key] = isNaN(numValue) ? value : numValue;
            } else {
              metadata[key] = value;
            }
          }
        }

        const workflowLog = await WorkflowLog.create({
          case_id: caseId,
          officer_id: officerId,
          step_name: stepName,
          action: action,
          timestamp: new Date(timestamp),
          duration_seconds: duration ? parseInt(duration) : null,
          status: status,
          metadata: metadata,  // Now contains all extended fields!
          is_synthetic: false,
          uploaded_at: uploadTimestamp,  // Use single timestamp for entire batch
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
    logger.endpoint('POST', '/api/workflows/analyze');
    const timer = logger.startTimer();

    // Get SOP ID from request body
    const sopId = req.body.sopId;

    if (!sopId) {
      logger.error('No SOP ID provided in analyze request');
      return errorResponse(res, 'SOP ID is required. Please select an SOP before analyzing.', 400);
    }

    // Get all logs (including synthetic logs for stress testing)
    const logs = await WorkflowLog.findAll({
      order: [['case_id', 'ASC'], ['timestamp', 'ASC']],
    });

    // Get rules filtered by SOP ID
    const rules = await SOPRule.findAll({
      where: { sop_id: sopId }
    });

    if (rules.length === 0) {
      logger.error(`No SOP rules found for SOP ID: ${sopId}`);
      return errorResponse(res, `No SOP rules found for the selected SOP (ID: ${sopId}). Please upload and process an SOP first.`, 400);
    }

    // Fetch SOP info for response
    const sop = await SOP.findByPk(sopId);
    if (!sop) {
      logger.error(`SOP not found: ${sopId}`);
      return errorResponse(res, `Selected SOP (ID: ${sopId}) not found.`, 404);
    }

    // Rules loaded - info logged in next step

    logger.step('Loading Data', {
      'Workflow logs': logs.length,
      'SOP rules': rules.length,
      'Unique cases': new Set(logs.map(l => l.case_id)).size
    });

    // Format logs for AI service
    // CRITICAL FIX: Merge metadata fields so AI service has access to extended fields
    const formattedLogs = logs.map((log, index) => {
      const baseLog = {
        case_id: log.case_id,
        officer_id: log.officer_id,
        step_name: log.step_name,
        action: log.action,
        timestamp: log.timestamp.toISOString(),
        duration_seconds: log.duration_seconds,
        status: log.status,
      };

      // DEBUG: Check first log's metadata
      if (index === 0 && log.metadata) {
        logger.debug('First log metadata', {
          case_id: log.case_id,
          metadata_keys: Object.keys(log.metadata)
        });
      }

      // Extract and merge metadata fields (for conditional/temporal/regulatory evaluators)
      if (log.metadata && typeof log.metadata === 'object') {
        Object.assign(baseLog, log.metadata);
      }

      return baseLog;
    });

    // Format rules for AI service
    // CRITICAL FIX: Include ALL rule fields (condition_logic, temporal_constraint, etc.)
    const formattedRules = rules.map(rule => ({
      id: rule.id,
      rule_type: rule.rule_type,
      rule_description: rule.rule_description,
      step_number: rule.step_number,
      severity: rule.severity,
      // Include extended fields for new evaluators
      condition_logic: rule.condition_logic,
      temporal_constraint: rule.temporal_constraint,
      required_fields: rule.required_fields,
      timing_constraint: rule.timing_constraint,
      product_types: rule.product_types,
      customer_segments: rule.customer_segments,
      channels: rule.channels,
      geography: rule.geography,
      exceptions: rule.exceptions,
      calculation_formula: rule.calculation_formula,
      threshold_value: rule.threshold_value,
      field_dependencies: rule.field_dependencies,
      regulatory_reference: rule.regulatory_reference,
    }));

    logger.step('Detecting Deviations', {
      'Logs to analyze': formattedLogs.length,
      'Rules to check': formattedRules.length
    });

    // Detect deviations using AI service
    const deviationResult = await aiService.detectDeviations(formattedLogs, formattedRules);

    // Extract notes for all cases with deviations
    const caseIds = [...new Set(deviationResult.deviations.map(d => d.case_id))];
    const notesByCase = await notesService.getNotesForAnalysis(caseIds);

    logger.debug('Notes extracted', {
      cases_with_notes: Object.keys(notesByCase).length,
      total_cases_with_deviations: caseIds.length
    });

    // Generate unique session ID for this analysis run
    const sessionId = crypto.randomUUID();
    currentAnalysisSessionId = sessionId;

    // CRITICAL FIX: Delete all previous deviations to prevent accumulation
    // This ensures pattern analysis only uses current analysis results
    const deletedCount = await Deviation.destroy({ where: {}, truncate: true });
    logger.debug('Cleared old deviations', { count: deletedCount });

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
        analysis_session_id: sessionId,  // ✅ Track which analysis run created this deviation
      });
      savedDeviations.push(deviation);
    }

    // Calculate overview metrics
    const uniqueCases = new Set(logs.map(l => l.case_id));
    const uniqueOfficers = new Set(logs.map(l => l.officer_id));

    // Aggregate deviations by type
    const deviationsByType = {};
    const deviationsBySeverity = {};
    savedDeviations.forEach(d => {
      deviationsByType[d.deviation_type] = (deviationsByType[d.deviation_type] || 0) + 1;
      deviationsBySeverity[d.severity] = (deviationsBySeverity[d.severity] || 0) + 1;
    });

    // Show aggregated results
    if (savedDeviations.length > 0) {
      logger.aggregated('Deviations by Type', deviationsByType, { maxItems: 8 });
      logger.aggregated('Deviations by Severity', deviationsBySeverity, { showTotal: false });
    }

    logger.success('Deviation Detection Complete', {
      'Total deviations': savedDeviations.length,
      'Cases analyzed': uniqueCases.size,
      'Officers': uniqueOfficers.size,
      'Time': logger.getElapsed(timer)
    });

    // Get first log to extract column names (workflow fields)
    const firstLog = logs.length > 0 ? logs[0] : null;
    const internalFields = ['id', 'uploaded_at', 'metadata', 'is_synthetic', 'created_at', 'updated_at'];

    // Extract core fields + metadata fields
    let workflowFields = [];
    if (firstLog) {
      const coreFields = Object.keys(firstLog.toJSON()).filter(f => !internalFields.includes(f));
      const metadataFields = firstLog.metadata && typeof firstLog.metadata === 'object'
        ? Object.keys(firstLog.metadata)
        : [];
      workflowFields = [...coreFields, ...metadataFields];
    }

    // Format SOP rules for frontend
    const sopRulesFormatted = rules.map(rule => ({
      id: rule.id,
      rule_type: rule.rule_type,
      name: `${rule.rule_type} Rule`,
      description: rule.rule_description,
      rule_description: rule.rule_description, // For compatibility
      condition: rule.rule_description,
      severity: rule.severity,
      step_number: rule.step_number,
    }));

    return successResponse(
      res,
      {
        total_deviations: savedDeviations.length,
        deviations: savedDeviations,
        summary: {
          total_cases: uniqueCases.size,
          total_logs: logs.length,
          total_officers: uniqueOfficers.size,
          total_deviations: savedDeviations.length,
          critical: savedDeviations.filter(d => d.severity === 'critical').length,
          high: savedDeviations.filter(d => d.severity === 'high').length,
          medium: savedDeviations.filter(d => d.severity === 'medium').length,
          low: savedDeviations.filter(d => d.severity === 'low').length,
        },
        workflow_metadata: {
          fields: workflowFields,
          total_logs: logs.length,
        },
        sop_rules: sopRulesFormatted,
        sop_info: {
          id: sop.id,
          title: sop.title,
          description: sop.description,
          rules_count: rules.length
        },
        // Include log cleaning report and quality score from AI service
        log_cleaning_report: deviationResult.log_cleaning_report || null,
        log_quality: deviationResult.log_quality || null,
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

    // Generate single upload timestamp for entire batch
    const uploadTimestamp = new Date();

    logger.endpoint('POST', '/api/workflows/upload-with-mapping', {
      'Filename': file?.originalname || 'none',
      'Size': file ? `${Math.round(file.size / 1024)}KB` : 'N/A'
    });

    if (!file) {
      logger.error('No file uploaded');
      return errorResponse(res, 'No file uploaded', 400);
    }

    if (!mapping || mapping === 'undefined' || mapping === 'null') {
      logger.error('Invalid column mapping');
      return errorResponse(res, 'Column mapping not provided or invalid', 400);
    }

    // Parse mapping from JSON string if needed
    let columnMapping;
    try {
      columnMapping = typeof mapping === 'string' ? JSON.parse(mapping) : mapping;
    } catch (parseError) {
      logger.error('JSON parse error in column mapping', parseError);
      return errorResponse(res, 'Invalid JSON in column mapping', 400);
    }

    logger.debug('Column mapping parsed', {
      columns: Object.keys(columnMapping).length
    });

    // Validate mapping format (should be simple strings: { "CSV_Col": "system_field" })
    for (const [csvColumn, mappingValue] of Object.entries(columnMapping)) {
      if (typeof mappingValue !== 'string') {
        logger.error(`Invalid mapping format for column: ${csvColumn}`);
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

    logger.step('Processing Upload', {
      'CSV columns': Object.keys(parsed.data[0] || {}).length,
      'Mapped fields': Object.keys(columnMapping).length,
      'Total rows': transformedData.length,
      'Notes column': notesColumn || 'none'
    });

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

        // CRITICAL FIX: Separate core fields from extended fields
        // Core fields are stored as columns, extended fields go in metadata JSON
        const coreFields = ['case_id', 'officer_id', 'step_name', 'action', 'timestamp', 'duration_seconds', 'status'];

        // Build metadata object with ALL extended fields
        const metadata = {
          original_filename: file.originalname
        };

        // Add all non-core fields to metadata
        for (const [key, value] of Object.entries(row)) {
          if (!coreFields.includes(key) && value !== null && value !== undefined && value !== '') {
            // Convert numeric strings to numbers where appropriate
            if (key.includes('amount') || key.includes('value') || key.includes('score') || key.includes('ratio')) {
              const numValue = parseFloat(value);
              metadata[key] = isNaN(numValue) ? value : numValue;
            } else {
              metadata[key] = value;
            }
          }
        }

        const workflowLog = await WorkflowLog.create({
          case_id: row.case_id,
          officer_id: row.officer_id,
          step_name: row.step_name,
          action: row.action || 'completed',
          timestamp: new Date(row.timestamp),
          duration_seconds: row.duration_seconds ? parseInt(row.duration_seconds) : null,
          status: row.status || 'completed',
          metadata: metadata,  // Now contains all extended fields!
          is_synthetic: false,
          uploaded_at: uploadTimestamp,  // Use single timestamp for entire batch
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
      notesCount = await notesService.extractAndStoreNotesFromCSV(
        savedLogs,
        parsed.data,
        notesColumn
      );
      logger.debug('Notes extracted', { count: notesCount });
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

    // Prepare detailed message about upload results
    const totalRows = transformedData.length;
    const skippedRows = errors.length;
    const successRows = savedLogs.length;

    if (errors.length > 0) {
      logger.warn(`${skippedRows} rows skipped`, errors.slice(0, 3).join('; '));
    }

    logger.success('Upload Complete', {
      'Rows saved': successRows,
      'Cases': new Set(savedLogs.map(l => l.case_id)).size,
      'Officers': officers.size,
      'Notes imported': notesCount,
      'Errors': skippedRows
    });

    let message = `Workflow logs uploaded: ${successRows} of ${totalRows} rows successful`;
    if (skippedRows > 0) {
      message += ` (${skippedRows} rows skipped due to validation errors)`;
    }

    return successResponse(
      res,
      {
        total_rows_processed: totalRows,
        total_logs: savedLogs.length,
        rows_skipped: skippedRows,
        unique_cases: new Set(savedLogs.map(l => l.case_id)).size,
        unique_officers: officers.size,
        notes_imported: notesCount,
        errors: errors.length > 0 ? errors.slice(0, 10) : [],  // Show first 10 errors
        has_more_errors: errors.length > 10,
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
    logger.endpoint('POST', '/api/workflows/analyze-patterns');
    const timer = logger.startTimer();

    // CRITICAL FIX: Filter by current session ID to prevent analyzing accumulated deviations
    // This ensures we only analyze deviations from the most recent workflow analysis
    const whereClause = currentAnalysisSessionId
      ? { analysis_session_id: currentAnalysisSessionId }
      : {}; // Fallback to all deviations if no session ID (shouldn't happen in normal flow)

    // Get deviations for current analysis session - now using layered approach with data cleaning & statistical analysis
    // The AI service will:
    // 1. Clean the data (remove duplicates, validate, normalize)
    // 2. Perform statistical analysis on session deviations
    // 3. Use statistical context to enhance AI pattern analysis
    const deviations = await Deviation.findAll({
      where: whereClause,
      order: [['detected_at', 'DESC']],
    });

    if (deviations.length === 0) {
      logger.warn('No deviations found for pattern analysis');
      return successResponse(res, {
        message: 'No deviations found for pattern analysis'
      });
    }

    logger.step('Pattern Analysis Pipeline', {
      'Deviations': deviations.length,
      'Session': currentAnalysisSessionId?.slice(0, 8) || 'unknown',
      'Approach': 'layered (cleaning + stats + ML + AI)'
    });

    // Format deviations for AI analysis (include timestamp for temporal analysis)
    const deviationsWithNotes = deviations.map(dev => ({
      case_id: dev.case_id,
      officer_id: dev.officer_id,
      deviation_type: dev.deviation_type,
      severity: dev.severity,
      description: dev.description,
      expected_behavior: dev.expected_behavior,
      actual_behavior: dev.actual_behavior,
      notes: dev.notes || null,
      detected_at: dev.detected_at, // Include for temporal analysis
      created_at: dev.created_at
    }));

    // Query workflow logs for deviation cases (enables temporal analysis)
    const deviationCaseIds = [...new Set(deviations.map(d => d.case_id))];

    const workflowLogs = await WorkflowLog.findAll({
      where: { case_id: deviationCaseIds },
      order: [['case_id', 'ASC'], ['timestamp', 'ASC']],
    });

    // Format workflow logs for AI service (same format as deviation detection)
    const formattedLogs = workflowLogs.map(log => ({
      case_id: log.case_id,
      officer_id: log.officer_id,
      step_name: log.step_name,
      action: log.action,
      timestamp: log.timestamp.toISOString(),
      duration_seconds: log.duration_seconds,
      status: log.status,
    }));

    logger.debug('Data prepared for AI service', {
      deviations: deviations.length,
      workflow_logs: workflowLogs.length,
      cases: deviationCaseIds.length
    });

    // Call AI service for layered pattern analysis
    const patternAnalysis = await aiService.analyzeDeviationPatterns(deviationsWithNotes, formattedLogs);

    logger.success('Pattern Analysis Complete', {
      'Behavioral patterns': patternAnalysis.behavioral_patterns?.length || 0,
      'Hidden rules': patternAnalysis.hidden_rules?.length || 0,
      'Recommendations': patternAnalysis.recommendations?.length || 0,
      'ML clusters': patternAnalysis.ml_summary?.cluster_summary?.length || 0,
      'Time': logger.getElapsed(timer)
    });

    return successResponse(
      res,
      {
        total_deviations: deviations.length,
        deviations_analyzed: patternAnalysis.deviations_analyzed || deviations.length,
        api_calls_made: patternAnalysis.api_calls_made || 1,
        data_quality: patternAnalysis.data_quality || null,
        log_cleaning_report: patternAnalysis.log_cleaning_report || null,
        log_quality: patternAnalysis.log_quality || null,
        statistical_summary: patternAnalysis.statistical_summary || null,
        ml_summary: patternAnalysis.ml_summary || null,
        ml_metadata: patternAnalysis.ml_metadata || null, // Add ml_metadata
        overall_summary: patternAnalysis.overall_summary || '',
        behavioral_patterns: patternAnalysis.behavioral_patterns || [],
        hidden_rules: patternAnalysis.hidden_rules || [],
        systemic_issues: patternAnalysis.systemic_issues || [],
        time_patterns: patternAnalysis.time_patterns || [],
        justification_analysis: patternAnalysis.justification_analysis || {},
        risk_insights: patternAnalysis.risk_insights || [],
        recommendations: patternAnalysis.recommendations || []
      },
      'Layered pattern analysis completed successfully'
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
    // Using minute-level precision to group files uploaded in the same batch
    const uploadSessions = await WorkflowLog.findAll({
      attributes: [
        [sequelize.fn('strftime', '%Y-%m-%d %H:%M', sequelize.col('uploaded_at')), 'upload_timestamp'],
        [sequelize.fn('COUNT', sequelize.col('id')), 'total_logs'],
        [sequelize.fn('COUNT', sequelize.fn('DISTINCT', sequelize.col('case_id'))), 'unique_cases'],
        [sequelize.fn('MAX', sequelize.col('is_synthetic')), 'is_generated'],
        [sequelize.fn('MAX', sequelize.col('uploaded_at')), 'uploaded_at'],
        [sequelize.fn('MAX', sequelize.col('metadata')), 'metadata'],
      ],
      group: [sequelize.fn('strftime', '%Y-%m-%d %H:%M', sequelize.col('uploaded_at'))],
      order: [[sequelize.fn('MAX', sequelize.col('uploaded_at')), 'DESC']],
      raw: true,
    });

    // Transform to frontend-expected format
    const files = await Promise.all(uploadSessions.map(async (session, index) => {
      const uploadDate = new Date(session.uploaded_at);
      const dateStr = uploadDate.toISOString().replace(/[-:]/g, '').replace('T', '_').substring(0, 15);

      // Try to get original filename from metadata
      let filename;
      let parsedMetadata = null;
      if (session.metadata) {
        try {
          parsedMetadata = typeof session.metadata === 'string'
            ? JSON.parse(session.metadata)
            : session.metadata;

          // Use original filename if available
          if (parsedMetadata.original_filename) {
            filename = parsedMetadata.original_filename;
          } else if (session.is_generated && parsedMetadata.scenario_type) {
            filename = `synthetic_${parsedMetadata.scenario_type}_${dateStr}.csv`;
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

      // Get column names from first log in this session
      const firstLog = await WorkflowLog.findOne({
        where: sequelize.where(
          sequelize.fn('strftime', '%Y-%m-%d %H:%M', sequelize.col('uploaded_at')),
          session.upload_timestamp
        ),
        limit: 1
      });

      // Extract column names (exclude internal fields)
      const internalFields = ['id', 'uploaded_at', 'metadata', 'is_synthetic', 'created_at', 'updated_at'];
      const fields = firstLog ? Object.keys(firstLog.toJSON()).filter(f => !internalFields.includes(f)) : [];

      return {
        id: session.upload_timestamp, // Use timestamp as unique ID
        filename: filename,
        uploaded_at: session.uploaded_at,
        total_logs: parseInt(session.total_logs),
        unique_cases: parseInt(session.unique_cases),
        is_generated: Boolean(session.is_generated),
        fields: fields, // Add fields here
        columns: fields, // Alias for compatibility
      };
    }));

    return successResponse(res, { files }, 'Workflow files retrieved successfully');
  } catch (error) {
    next(error);
  }
};

const deleteWorkflowFile = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { sequelize } = require('../config/database');

    // Get case IDs from workflow logs to be deleted
    const logsToDelete = await WorkflowLog.findAll({
      where: sequelize.where(
        sequelize.fn('strftime', '%Y-%m-%d %H:%M', sequelize.col('uploaded_at')),
        id
      ),
      attributes: ['case_id'],
    });

    const caseIds = [...new Set(logsToDelete.map(log => log.case_id))];

    // The ID is the upload_timestamp in format 'YYYY-MM-DD HH:MM'
    // Delete all logs with this upload timestamp
    const deleted = await WorkflowLog.destroy({
      where: sequelize.where(
        sequelize.fn('strftime', '%Y-%m-%d %H:%M', sequelize.col('uploaded_at')),
        id
      ),
    });

    if (deleted === 0) {
      return errorResponse(res, 'Workflow file not found', 404);
    }

    // CASCADE DELETE: Remove deviations associated with deleted workflow logs
    // This prevents orphaned deviations from accumulating when workflow files are deleted
    if (caseIds.length > 0) {
      const deviationsDeleted = await Deviation.destroy({
        where: {
          case_id: caseIds
        }
      });
      console.log(`[deleteWorkflowFile] Cascade deleted ${deviationsDeleted} deviations for ${caseIds.length} cases`);
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
