/**
 * Data Cleaning Service (Layer 1 of 5-Layer Pipeline)
 *
 * Purpose: Remove duplicates and detect garbage values BEFORE database insert
 *
 * Algorithms:
 * 1. Duplicate Detection: O(n) hash map with composite key
 * 2. Garbage Value Detection: Pattern matching for test data, placeholders, invalid values
 */

class DataCleaningService {
  /**
   * Clean data by removing duplicates and garbage rows.
   *
   * @param {Array} rows - Array of row objects from CSV
   * @param {Object} columnMapping - Column mapping to access fields
   * @returns {Object} Cleaning result with cleanRows, duplicates, garbageRows, report
   */
  cleanData(rows, columnMapping) {
    const result = {
      cleanRows: [],
      duplicates: [],
      garbageRows: [],
      report: {
        total_input: rows.length,
        clean_output: 0,
        duplicates_removed: 0,
        garbage_removed: 0,
        success_rate: '0%'
      }
    };

    // Step 1: Duplicate detection
    const seenKeys = new Map();
    const rowsAfterDuplicateCheck = [];

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const duplicateKey = this._generateDuplicateKey(row, columnMapping);

      if (seenKeys.has(duplicateKey)) {
        // Duplicate found
        result.duplicates.push({
          row_index: i,
          row_data: row,
          duplicate_of_index: seenKeys.get(duplicateKey),
          reason: 'Duplicate: Same case_id + timestamp + step_name'
        });
      } else {
        // Not a duplicate
        seenKeys.set(duplicateKey, i);
        rowsAfterDuplicateCheck.push(row);
      }
    }

    // Step 2: Garbage value detection
    for (let i = 0; i < rowsAfterDuplicateCheck.length; i++) {
      const row = rowsAfterDuplicateCheck[i];
      const garbageCheck = this._detectGarbageValues(row, columnMapping);

      if (garbageCheck.isGarbage) {
        // Garbage detected
        result.garbageRows.push({
          row_index: i,
          row_data: row,
          reason: garbageCheck.reason
        });
      } else {
        // Clean row
        result.cleanRows.push(row);
      }
    }

    // Generate report
    result.report.clean_output = result.cleanRows.length;
    result.report.duplicates_removed = result.duplicates.length;
    result.report.garbage_removed = result.garbageRows.length;
    result.report.success_rate = ((result.cleanRows.length / rows.length) * 100).toFixed(1) + '%';

    return result;
  }

  /**
   * Generate composite key for duplicate detection.
   * Key: case_id|timestamp|step_name
   *
   * @private
   * @param {Object} row - Row object
   * @param {Object} columnMapping - Column mapping
   * @returns {string} Composite key
   */
  _generateDuplicateKey(row, columnMapping) {
    const caseId = this._getFieldValue(row, columnMapping, 'case_id') || '';
    const timestamp = this._getFieldValue(row, columnMapping, 'timestamp') || '';
    const stepName = this._getFieldValue(row, columnMapping, 'step_name') || '';

    return `${caseId}|${timestamp}|${stepName}`.toLowerCase().trim();
  }

  /**
   * Detect garbage values using pattern matching.
   *
   * Checks for:
   * - Test data patterns (test, dummy, sample, test123)
   * - Placeholder values (N/A, TBD, null, pending, unknown)
   * - Nonsense patterns (single letters, repeated characters)
   * - Invalid timestamps (before 2000, future dates)
   * - Invalid amounts (negative, zero, > 100M)
   *
   * @private
   * @param {Object} row - Row object
   * @param {Object} columnMapping - Column mapping
   * @returns {Object} { isGarbage: boolean, reason: string }
   */
  _detectGarbageValues(row, columnMapping) {
    // Get key fields for validation
    const caseId = this._getFieldValue(row, columnMapping, 'case_id');
    const stepName = this._getFieldValue(row, columnMapping, 'step_name');
    const timestamp = this._getFieldValue(row, columnMapping, 'timestamp');
    const loanAmount = this._getFieldValue(row, columnMapping, 'loan_amount');
    const customerName = this._getFieldValue(row, columnMapping, 'customer_name');

    // 1. Check for test data patterns
    const testPatterns = /test|dummy|sample|fake|example|xxx|zzz/i;
    if (caseId && testPatterns.test(String(caseId))) {
      return { isGarbage: true, reason: 'Test data pattern detected in case_id' };
    }
    if (customerName && testPatterns.test(String(customerName))) {
      return { isGarbage: true, reason: 'Test data pattern detected in customer_name' };
    }

    // 2. Check for placeholder values
    const placeholderPatterns = /^(n\/a|tbd|null|pending|unknown|none|empty|-)$/i;
    if (caseId && placeholderPatterns.test(String(caseId).trim())) {
      return { isGarbage: true, reason: 'Placeholder value in case_id' };
    }
    if (stepName && placeholderPatterns.test(String(stepName).trim())) {
      return { isGarbage: true, reason: 'Placeholder value in step_name' };
    }

    // 3. Check for nonsense patterns (single letters, repeated characters)
    if (caseId && this._isNonsenseString(String(caseId))) {
      return { isGarbage: true, reason: 'Nonsense pattern in case_id' };
    }

    // 4. Check for invalid timestamps
    if (timestamp) {
      const timestampCheck = this._validateTimestamp(String(timestamp));
      if (!timestampCheck.valid) {
        return { isGarbage: true, reason: `Invalid timestamp: ${timestampCheck.reason}` };
      }
    }

    // 5. Check for invalid loan amounts
    if (loanAmount !== null && loanAmount !== undefined && loanAmount !== '') {
      const amount = parseFloat(loanAmount);
      if (!isNaN(amount)) {
        if (amount < 0) {
          return { isGarbage: true, reason: 'Negative loan amount' };
        }
        if (amount === 0) {
          return { isGarbage: true, reason: 'Zero loan amount' };
        }
        if (amount > 100000000) {
          return { isGarbage: true, reason: 'Loan amount exceeds 100M (unrealistic)' };
        }
      }
    }

    // All checks passed
    return { isGarbage: false, reason: '' };
  }

  /**
   * Check if string is nonsense (single letter or repeated characters).
   *
   * @private
   * @param {string} str - String to check
   * @returns {boolean} True if nonsense
   */
  _isNonsenseString(str) {
    const trimmed = str.trim();

    // Single letter (excluding valid single-letter IDs)
    if (trimmed.length === 1) {
      return true;
    }

    // Repeated characters (e.g., "aaaa", "1111")
    const repeatedPattern = /^(.)\1{3,}$/;
    if (repeatedPattern.test(trimmed)) {
      return true;
    }

    return false;
  }

  /**
   * Validate timestamp.
   *
   * @private
   * @param {string} timestamp - Timestamp string
   * @returns {Object} { valid: boolean, reason: string }
   */
  _validateTimestamp(timestamp) {
    try {
      const date = new Date(timestamp);

      // Check if valid date
      if (isNaN(date.getTime())) {
        return { valid: false, reason: 'Invalid date format' };
      }

      // Check if before year 2000
      if (date.getFullYear() < 2000) {
        return { valid: false, reason: 'Date before year 2000' };
      }

      // Check if future date (more than 1 day ahead)
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      if (date > tomorrow) {
        return { valid: false, reason: 'Future date' };
      }

      return { valid: true, reason: '' };
    } catch (error) {
      return { valid: false, reason: 'Error parsing date' };
    }
  }

  /**
   * Get field value from row using column mapping.
   *
   * @private
   * @param {Object} row - Row object
   * @param {Object} columnMapping - Column mapping
   * @param {string} targetField - Target field name
   * @returns {*} Field value or null
   */
  _getFieldValue(row, columnMapping, targetField) {
    if (!columnMapping || !columnMapping.mappings) {
      // No column mapping, try direct access
      return row[targetField];
    }

    // Find mapping for target field
    const mapping = columnMapping.mappings.find(m => m.target_field === targetField);
    if (!mapping) {
      return null;
    }

    return row[mapping.source_field];
  }

  /**
   * Generate cleaning report for display.
   *
   * @param {Object} cleaningResult - Result from cleanData()
   * @returns {Object} Formatted report
   */
  generateReport(cleaningResult) {
    const { report, duplicates, garbageRows } = cleaningResult;

    return {
      summary: {
        total_input: report.total_input,
        clean_output: report.clean_output,
        duplicates_removed: report.duplicates_removed,
        garbage_removed: report.garbage_removed,
        success_rate: report.success_rate
      },
      duplicate_details: duplicates.map(d => ({
        row_index: d.row_index,
        duplicate_of: d.duplicate_of_index,
        reason: d.reason
      })),
      garbage_details: garbageRows.map(g => ({
        row_index: g.row_index,
        reason: g.reason
      }))
    };
  }
}

module.exports = new DataCleaningService();
