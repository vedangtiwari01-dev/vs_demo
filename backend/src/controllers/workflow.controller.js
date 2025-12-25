const { WorkflowLog, Officer, Deviation, SOPRule } = require('../models');
const aiService = require('../services/ai-integration.service');
const dataCleaningService = require('../services/data-cleaning.service');
const deviationDetectorService = require('../services/deviation-detector.service');
const statisticalAnalysisService = require('../services/statistical-analysis.service');
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
    // Get all logs (including synthetic logs for stress testing)
    const logs = await WorkflowLog.findAll({
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

    // Calculate overview metrics
    const uniqueCases = new Set(logs.map(l => l.case_id));
    const uniqueOfficers = new Set(logs.map(l => l.officer_id));

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

    // LAYER 1: Data Cleaning (before database insert)
    console.log('[uploadWithMapping] Starting data cleaning...');
    const cleaningResult = dataCleaningService.cleanData(parsed.data, columnMapping);
    const cleaningReport = dataCleaningService.generateReport(cleaningResult);

    console.log('[uploadWithMapping] Data cleaning complete:');
    console.log('  - Total input rows:', cleaningReport.summary.total_input);
    console.log('  - Clean rows:', cleaningReport.summary.clean_output);
    console.log('  - Duplicates removed:', cleaningReport.summary.duplicates_removed);
    console.log('  - Garbage removed:', cleaningReport.summary.garbage_removed);
    console.log('  - Success rate:', cleaningReport.summary.success_rate);

    // Use clean data instead of raw transformedData
    const cleanTransformedData = columnMappingService.applyMapping(cleaningResult.cleanRows, columnMapping);

    // Detect notes column
    const notesColumn = columnMappingService.detectNotesColumn(columnMapping);

    // Debug logging
    console.log('[uploadWithMapping] Column mapping used:', JSON.stringify(columnMapping, null, 2));
    console.log('[uploadWithMapping] Detected notes column:', notesColumn);
    console.log('[uploadWithMapping] CSV has', Object.keys(parsed.data[0] || {}).length, 'columns');
    console.log('[uploadWithMapping] Transformed', cleanTransformedData.length, 'clean rows');

    // Create workflow logs
    const savedLogs = [];
    const officers = new Set();
    const errors = [];

    for (let i = 0; i < cleanTransformedData.length; i++) {
      const row = cleanTransformedData[i];

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

    // Prepare detailed message about upload results
    const totalRows = cleanTransformedData.length;
    const skippedRows = errors.length;
    const successRows = savedLogs.length;

    let message = `Workflow logs uploaded: ${successRows} of ${totalRows} clean rows successful`;
    if (cleaningReport.summary.duplicates_removed > 0 || cleaningReport.summary.garbage_removed > 0) {
      message += ` (${cleaningReport.summary.duplicates_removed} duplicates + ${cleaningReport.summary.garbage_removed} garbage rows removed during cleaning)`;
    }
    if (skippedRows > 0) {
      message += ` (${skippedRows} rows skipped due to validation errors)`;
    }

    console.log(`[uploadWithMapping] Upload complete: ${successRows}/${totalRows} rows saved, ${skippedRows} errors`);
    if (errors.length > 0) {
      console.log('[uploadWithMapping] First 5 errors:', errors.slice(0, 5));
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
        cleaning_report: cleaningReport.summary,  // Include cleaning report
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

/**
 * Comprehensive Analysis Endpoint (5-Layer Pipeline)
 *
 * Orchestrates all 5 layers:
 * - Layer 1: Data Cleaning (already done during upload)
 * - Layer 2: Deviation Detection (batched)
 * - Layer 3: Statistical Analysis (ALL deviations)
 * - Layer 4: ML Intelligent Sampling (compress for LLM)
 * - Layer 5: AI Pattern Analysis (with cluster context)
 *
 * Expected time: ~4 minutes for 3000 applications
 * Cost: ~$0.75 for 1500 deviations (95% savings vs analyzing all)
 */
const analyzeComprehensive = async (req, res, next) => {
  try {
    console.log('[Comprehensive Analysis] Starting 5-layer pipeline...');
    const startTime = Date.now();

    // ==================================================================
    // LAYER 2: Deviation Detection (Batched)
    // ==================================================================
    console.log('[Comprehensive Analysis] Layer 2: Batched deviation detection...');
    const layer2Start = Date.now();

    const deviationResult = await deviationDetectorService.detectDeviations();

    console.log(`[Comprehensive Analysis] Layer 2 complete in ${((Date.now() - layer2Start) / 1000).toFixed(1)}s`);
    console.log(`  - Total deviations found: ${deviationResult.total_deviations}`);

    if (deviationResult.total_deviations === 0) {
      return successResponse(res, {
        message: 'No deviations found - system is compliant!',
        total_deviations: 0,
        statistical_insights: null,
        ml_analysis: null,
        pattern_analysis: null
      });
    }

    // ==================================================================
    // LAYER 3: Statistical Analysis (ALL deviations)
    // ==================================================================
    console.log('[Comprehensive Analysis] Layer 3: Statistical analysis on ALL deviations...');
    const layer3Start = Date.now();

    const statisticalInsights = await statisticalAnalysisService.analyzeAllDeviations(deviationResult.deviations);

    console.log(`[Comprehensive Analysis] Layer 3 complete in ${((Date.now() - layer3Start) / 1000).toFixed(1)}s`);

    // ==================================================================
    // LAYER 4: ML Intelligent Sampling
    // ==================================================================
    console.log('[Comprehensive Analysis] Layer 4: ML intelligent sampling...');
    const layer4Start = Date.now();

    let mlResult;
    try {
      mlResult = await aiService.intelligentSampling(
        deviationResult.deviations,
        statisticalInsights,
        75 // Target 75 representatives
      );
      console.log(`[Comprehensive Analysis] Layer 4 complete in ${((Date.now() - layer4Start) / 1000).toFixed(1)}s`);
      console.log(`  - Compression: ${mlResult.sampling_metadata.compression_ratio}`);
      console.log(`  - Representatives: ${mlResult.sampling_metadata.representatives_selected}`);
    } catch (error) {
      console.warn('[Comprehensive Analysis] ML sampling failed, using all deviations:', error.message);
      // Fallback: use all deviations
      mlResult = {
        representative_sample: deviationResult.deviations.slice(0, 100), // Cap at 100
        cluster_statistics: {},
        sampling_metadata: {
          total_deviations: deviationResult.total_deviations,
          representatives_selected: Math.min(100, deviationResult.total_deviations),
          compression_ratio: '1.0x',
          num_clusters: 0,
          num_anomalies: 0
        }
      };
    }

    // ==================================================================
    // LAYER 5: AI Pattern Analysis (with cluster context)
    // ==================================================================
    console.log('[Comprehensive Analysis] Layer 5: AI pattern analysis with cluster context...');
    const layer5Start = Date.now();

    let patternAnalysis;
    try {
      // Call analyze-patterns with cluster statistics
      const patternResponse = await aiService.client.post(
        '/ai/deviation/analyze-patterns',
        {
          deviations: mlResult.representative_sample,
          cluster_statistics: mlResult.cluster_statistics
        },
        { timeout: 600000 } // 10 minutes
      );
      patternAnalysis = patternResponse.data;
      console.log(`[Comprehensive Analysis] Layer 5 complete in ${((Date.now() - layer5Start) / 1000).toFixed(1)}s`);
    } catch (error) {
      console.warn('[Comprehensive Analysis] Pattern analysis failed:', error.message);
      patternAnalysis = {
        overall_summary: 'Pattern analysis failed - using statistical insights only',
        behavioral_patterns: [],
        hidden_rules: [],
        systemic_issues: [],
        recommendations: ['Manual review recommended']
      };
    }

    const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`[Comprehensive Analysis] Pipeline complete in ${totalTime}s`);

    // Calculate cost savings
    const fullCost = (deviationResult.total_deviations * 0.01).toFixed(2);
    const actualCost = (mlResult.sampling_metadata.representatives_selected * 0.01).toFixed(2);
    const savingsPercent = (((fullCost - actualCost) / fullCost) * 100).toFixed(1);

    return successResponse(res, {
      summary: {
        total_deviations: deviationResult.total_deviations,
        representatives_analyzed: mlResult.sampling_metadata.representatives_selected,
        total_time_seconds: parseFloat(totalTime),
        pipeline_layers_completed: 5
      },
      statistical_insights: statisticalInsights,
      ml_analysis: {
        cluster_statistics: mlResult.cluster_statistics,
        sampling_metadata: mlResult.sampling_metadata
      },
      pattern_analysis: patternAnalysis,
      cost_savings: {
        full_analysis_cost: `$${fullCost}`,
        actual_cost: `$${actualCost}`,
        savings: `${savingsPercent}%`,
        compression_ratio: mlResult.sampling_metadata.compression_ratio
      }
    });
  } catch (error) {
    console.error('[Comprehensive Analysis] Pipeline failed:', error);
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
  analyzeComprehensive,
  listWorkflowFiles,
  deleteWorkflowFile,
};
