/**
 * Clean and concise logger with aggregation support
 * Provides readable, summarized output with minimal noise
 */

class CleanLogger {
  constructor() {
    this.isVerbose = process.env.LOG_VERBOSE === 'true';

    // ANSI color codes
    this.colors = {
      reset: '\x1b[0m',
      bold: '\x1b[1m',
      gray: '\x1b[90m',
      red: '\x1b[31m',
      green: '\x1b[32m',
      yellow: '\x1b[33m',
      blue: '\x1b[34m',
      cyan: '\x1b[36m',
      white: '\x1b[37m',
    };
  }

  _color(text, color) {
    return `${this.colors[color]}${text}${this.colors.reset}`;
  }

  /**
   * Log an API endpoint call
   */
  endpoint(method, path, { ...meta } = {}) {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`\n${this._color('►', 'cyan')} ${this._color(this.colors.bold + method + this.colors.reset, 'white')} ${path} ${this._color(`[${timestamp}]`, 'gray')}`);

    if (Object.keys(meta).length > 0) {
      Object.entries(meta).forEach(([key, value]) => {
        console.log(`  ${this._color('│', 'gray')} ${key}: ${this._color(value, 'white')}`);
      });
    }
  }

  /**
   * Log a processing step with clean formatting
   */
  step(stepName, details = {}) {
    console.log(`  ${this._color('●', 'blue')} ${this._color(this.colors.bold + stepName + this.colors.reset, 'white')}`);

    Object.entries(details).forEach(([key, value]) => {
      console.log(`    ${this._color('•', 'gray')} ${key}: ${this._color(value, 'white')}`);
    });
  }

  /**
   * Log a success result with summary
   */
  success(message, summary = {}) {
    console.log(`  ${this._color('✓', 'green')} ${this._color(this.colors.bold + message + this.colors.reset, 'green')}`);

    if (Object.keys(summary).length > 0) {
      Object.entries(summary).forEach(([key, value]) => {
        console.log(`    ${this._color('•', 'gray')} ${key}: ${this._color(value, 'green')}`);
      });
    }
  }

  /**
   * Log an error with context
   */
  error(message, error = null) {
    console.log(`  ${this._color('✗', 'red')} ${this._color(this.colors.bold + message + this.colors.reset, 'red')}`);

    if (error && this.isVerbose) {
      console.log(`    ${this._color('•', 'gray')} ${this._color(error.message, 'red')}`);
      if (error.stack) {
        console.log(`    ${this._color(error.stack.split('\n').slice(0, 3).join('\n    '), 'gray')}`);
      }
    }
  }

  /**
   * Log a warning
   */
  warn(message, details = null) {
    console.log(`  ${this._color('⚠', 'yellow')} ${this._color(message, 'yellow')}`);

    if (details && this.isVerbose) {
      console.log(`    ${this._color('•', 'gray')} ${this._color(details, 'gray')}`);
    }
  }

  /**
   * Log aggregated results (e.g., deviation counts by type)
   */
  aggregated(title, items, { showTotal = true, maxItems = 10 } = {}) {
    console.log(`\n  ${this._color('◆', 'cyan')} ${this._color(this.colors.bold + title + this.colors.reset, 'white')}`);

    const entries = Object.entries(items);
    const total = entries.reduce((sum, [, count]) => sum + (typeof count === 'number' ? count : 0), 0);

    const sortedEntries = entries
      .sort((a, b) => (typeof b[1] === 'number' && typeof a[1] === 'number') ? b[1] - a[1] : 0)
      .slice(0, maxItems);

    sortedEntries.forEach(([key, value]) => {
      const bar = this._createBar(value, total);
      console.log(`    ${this._color('│', 'gray')} ${this._color(key.padEnd(25), 'white')} ${this._color(value, 'cyan')} ${bar}`);
    });

    if (entries.length > maxItems) {
      console.log(`    ${this._color('│', 'gray')} ${this._color(`... and ${entries.length - maxItems} more`, 'gray')}`);
    }

    if (showTotal && entries.length > 1) {
      console.log(`    ${this._color('│', 'gray')} ${this._color(this.colors.bold + 'TOTAL'.padEnd(25) + this.colors.reset, 'white')} ${this._color(this.colors.bold + total + this.colors.reset, 'cyan')}`);
    }
  }

  /**
   * Create a simple text-based progress bar
   */
  _createBar(value, total, maxWidth = 15) {
    if (!total || total === 0) return '';

    const percentage = Math.min(value / total, 1);
    const filled = Math.round(percentage * maxWidth);
    const empty = maxWidth - filled;

    return this._color('[', 'gray') +
           this._color('█'.repeat(filled), 'cyan') +
           this._color('░'.repeat(empty), 'gray') +
           this._color(']', 'gray');
  }

  /**
   * Log verbose debug information (only if LOG_VERBOSE=true)
   */
  debug(message, data = null) {
    if (!this.isVerbose) return;

    console.log(`  ${this._color('◯', 'gray')} ${this._color(message, 'gray')}`);
    if (data) {
      console.log(`    ${this._color(JSON.stringify(data, null, 2), 'gray')}`);
    }
  }

  /**
   * Log a clean separator
   */
  separator() {
    console.log(`${this._color('─'.repeat(60), 'gray')}`);
  }

  /**
   * Start timing an operation
   */
  startTimer() {
    return Date.now();
  }

  /**
   * Get elapsed time in human-readable format
   */
  getElapsed(startTime) {
    const elapsed = Date.now() - startTime;

    if (elapsed < 1000) return `${elapsed}ms`;
    if (elapsed < 60000) return `${(elapsed / 1000).toFixed(1)}s`;
    return `${Math.floor(elapsed / 60000)}m ${Math.floor((elapsed % 60000) / 1000)}s`;
  }
}

// Export singleton instance
const cleanLogger = new CleanLogger();

module.exports = cleanLogger;
