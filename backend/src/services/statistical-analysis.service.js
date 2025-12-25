/**
 * Statistical Analysis Service (Layer 3 of 5-Layer Pipeline)
 *
 * Purpose: Comprehensive statistics on ALL deviations
 * Critical Requirement: "no hidden patterns must get lost in this step"
 *
 * 6 Analysis Types (all run in parallel):
 * 1. Distribution Analysis (by severity, type, hour, officer)
 * 2. Correlation Analysis (workload vs deviation rate, officer vs type)
 * 3. Time-Series Analysis (daily trend 30d, weekly pattern)
 * 4. Frequency Analysis (common descriptions, officer-type pairs)
 * 5. Officer-Level Analysis (counts, types, severity)
 * 6. Deviation Type Analysis (counts, officers, severity scores)
 *
 * Expected Time: <10 seconds for 3000 deviations
 */

class StatisticalAnalysisService {
  /**
   * Analyze all deviations comprehensively.
   *
   * @param {Array} deviations - All deviations from deviation detector
   * @returns {Promise<Object>} Comprehensive statistical insights
   */
  async analyzeAllDeviations(deviations) {
    const startTime = Date.now();
    console.log(`[Statistical Analysis] Analyzing ${deviations.length} deviations...`);

    // Run all analyses in parallel for speed
    const [
      distributions,
      correlations,
      timeSeries,
      frequencies,
      officerAnalysis,
      typeAnalysis
    ] = await Promise.all([
      this.computeDistributions(deviations),
      this.computeCorrelations(deviations),
      this.computeTimeSeries(deviations),
      this.computeFrequencies(deviations),
      this.analyzeByOfficer(deviations),
      this.analyzeByType(deviations)
    ]);

    const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`[Statistical Analysis] Complete in ${elapsedTime}s`);

    return {
      summary: {
        total_deviations: deviations.length,
        analysis_time_seconds: parseFloat(elapsedTime)
      },
      distributions,
      correlations,
      time_series: timeSeries,
      frequencies,
      officer_analysis: officerAnalysis,
      type_analysis: typeAnalysis
    };
  }

  /**
   * 1. Distribution Analysis
   * Analyze distributions by severity, type, hour, officer.
   *
   * @param {Array} deviations - All deviations
   * @returns {Promise<Object>} Distribution statistics
   */
  async computeDistributions(deviations) {
    const bySeverity = this._groupAndCount(deviations, 'severity');
    const byType = this._groupAndCount(deviations, 'deviation_type');
    const byHour = this._groupAndCount(
      deviations.map(d => ({
        ...d,
        hour: d.timestamp ? new Date(d.timestamp).getHours() : null
      })),
      'hour'
    );
    const byOfficer = this._groupAndCount(deviations, 'officer_id');

    return {
      by_severity: bySeverity,
      by_type: byType,
      by_hour: byHour,
      by_officer: byOfficer,
      insights: this._generateDistributionInsights(bySeverity, byType, byHour)
    };
  }

  /**
   * 2. Correlation Analysis
   * Find correlations between workload and deviation rate, officer and type preference.
   *
   * @param {Array} deviations - All deviations
   * @returns {Promise<Object>} Correlation statistics
   */
  async computeCorrelations(deviations) {
    // Officer workload vs deviation rate
    const officerStats = new Map();
    deviations.forEach(d => {
      const officer = d.officer_id || 'unknown';
      if (!officerStats.has(officer)) {
        officerStats.set(officer, { count: 0, severitySum: 0 });
      }
      const stats = officerStats.get(officer);
      stats.count++;
      stats.severitySum += this._severityToScore(d.severity);
    });

    const workloadCorrelation = Array.from(officerStats.entries()).map(([officer, stats]) => ({
      officer_id: officer,
      deviation_count: stats.count,
      avg_severity_score: (stats.severitySum / stats.count).toFixed(2)
    })).sort((a, b) => b.deviation_count - a.deviation_count);

    // Officer vs type preference
    const officerTypeMatrix = new Map();
    deviations.forEach(d => {
      const officer = d.officer_id || 'unknown';
      const type = d.deviation_type || 'unknown';
      const key = `${officer}|${type}`;
      officerTypeMatrix.set(key, (officerTypeMatrix.get(key) || 0) + 1);
    });

    const topOfficerTypePairs = Array.from(officerTypeMatrix.entries())
      .map(([key, count]) => {
        const [officer, type] = key.split('|');
        return { officer_id: officer, deviation_type: type, count };
      })
      .sort((a, b) => b.count - a.count)
      .slice(0, 20);

    return {
      workload_vs_deviation: workloadCorrelation,
      officer_type_preferences: topOfficerTypePairs,
      insights: this._generateCorrelationInsights(workloadCorrelation)
    };
  }

  /**
   * 3. Time-Series Analysis
   * Analyze daily trends (last 30 days) and weekly patterns.
   *
   * @param {Array} deviations - All deviations
   * @returns {Promise<Object>} Time-series statistics
   */
  async computeTimeSeries(deviations) {
    // Daily trend (last 30 days)
    const dailyCounts = new Map();
    const now = new Date();
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    deviations.forEach(d => {
      if (!d.timestamp) return;
      const date = new Date(d.timestamp);
      if (date < thirtyDaysAgo) return;

      const dateKey = date.toISOString().split('T')[0];
      dailyCounts.set(dateKey, (dailyCounts.get(dateKey) || 0) + 1);
    });

    const dailyTrend = Array.from(dailyCounts.entries())
      .map(([date, count]) => ({ date, count }))
      .sort((a, b) => a.date.localeCompare(b.date));

    // Weekly pattern (day of week)
    const weekdayCounts = new Array(7).fill(0);
    const weekdayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

    deviations.forEach(d => {
      if (!d.timestamp) return;
      const dayOfWeek = new Date(d.timestamp).getDay();
      weekdayCounts[dayOfWeek]++;
    });

    const weeklyPattern = weekdayNames.map((day, index) => ({
      day,
      count: weekdayCounts[index]
    }));

    return {
      daily_trend_30d: dailyTrend,
      weekly_pattern: weeklyPattern,
      insights: this._generateTimeSeriesInsights(dailyTrend, weeklyPattern)
    };
  }

  /**
   * 4. Frequency Analysis
   * Find most common descriptions and officer-type pairs.
   *
   * @param {Array} deviations - All deviations
   * @returns {Promise<Object>} Frequency statistics
   */
  async computeFrequencies(deviations) {
    // Most common descriptions
    const descriptionCounts = new Map();
    deviations.forEach(d => {
      const desc = (d.description || 'No description').substring(0, 100);
      descriptionCounts.set(desc, (descriptionCounts.get(desc) || 0) + 1);
    });

    const topDescriptions = Array.from(descriptionCounts.entries())
      .map(([description, count]) => ({ description, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    // Most common officer-type pairs (already computed in correlations, but simplified here)
    const officerTypeCounts = new Map();
    deviations.forEach(d => {
      const key = `${d.officer_id || 'unknown'}|${d.deviation_type || 'unknown'}`;
      officerTypeCounts.set(key, (officerTypeCounts.get(key) || 0) + 1);
    });

    const topOfficerTypePairs = Array.from(officerTypeCounts.entries())
      .map(([key, count]) => {
        const [officer, type] = key.split('|');
        return { officer_id: officer, deviation_type: type, count };
      })
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    return {
      top_descriptions: topDescriptions,
      top_officer_type_pairs: topOfficerTypePairs
    };
  }

  /**
   * 5. Officer-Level Analysis
   * Analyze deviations per officer (counts, types, severity distribution).
   *
   * @param {Array} deviations - All deviations
   * @returns {Promise<Object>} Officer-level statistics
   */
  async analyzeByOfficer(deviations) {
    const officerMap = new Map();

    deviations.forEach(d => {
      const officer = d.officer_id || 'unknown';
      if (!officerMap.has(officer)) {
        officerMap.set(officer, {
          officer_id: officer,
          total_deviations: 0,
          types: new Map(),
          severities: { critical: 0, high: 0, medium: 0, low: 0 }
        });
      }

      const stats = officerMap.get(officer);
      stats.total_deviations++;

      const type = d.deviation_type || 'unknown';
      stats.types.set(type, (stats.types.get(type) || 0) + 1);

      const severity = d.severity || 'low';
      if (severity in stats.severities) {
        stats.severities[severity]++;
      }
    });

    const officerAnalysis = Array.from(officerMap.values())
      .map(stats => ({
        officer_id: stats.officer_id,
        total_deviations: stats.total_deviations,
        top_types: Array.from(stats.types.entries())
          .map(([type, count]) => ({ type, count }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 5),
        severity_distribution: stats.severities,
        avg_severity_score: this._calculateAvgSeverity(stats.severities)
      }))
      .sort((a, b) => b.total_deviations - a.total_deviations);

    return {
      by_officer: officerAnalysis,
      top_10_officers: officerAnalysis.slice(0, 10)
    };
  }

  /**
   * 6. Deviation Type Analysis
   * Analyze deviations by type (counts, officers involved, severity scores).
   *
   * @param {Array} deviations - All deviations
   * @returns {Promise<Object>} Type-level statistics
   */
  async analyzeByType(deviations) {
    const typeMap = new Map();

    deviations.forEach(d => {
      const type = d.deviation_type || 'unknown';
      if (!typeMap.has(type)) {
        typeMap.set(type, {
          deviation_type: type,
          total_count: 0,
          officers: new Set(),
          severities: { critical: 0, high: 0, medium: 0, low: 0 }
        });
      }

      const stats = typeMap.get(type);
      stats.total_count++;

      if (d.officer_id) {
        stats.officers.add(d.officer_id);
      }

      const severity = d.severity || 'low';
      if (severity in stats.severities) {
        stats.severities[severity]++;
      }
    });

    const typeAnalysis = Array.from(typeMap.values())
      .map(stats => ({
        deviation_type: stats.deviation_type,
        total_count: stats.total_count,
        unique_officers: stats.officers.size,
        severity_distribution: stats.severities,
        avg_severity_score: this._calculateAvgSeverity(stats.severities)
      }))
      .sort((a, b) => b.total_count - a.total_count);

    return {
      by_type: typeAnalysis,
      top_10_types: typeAnalysis.slice(0, 10)
    };
  }

  /**
   * Helper: Group and count by field.
   *
   * @private
   */
  _groupAndCount(items, field) {
    const counts = new Map();
    items.forEach(item => {
      const value = item[field] || 'unknown';
      counts.set(value, (counts.get(value) || 0) + 1);
    });

    return Array.from(counts.entries())
      .map(([value, count]) => ({ [field]: value, count }))
      .sort((a, b) => b.count - a.count);
  }

  /**
   * Helper: Convert severity to numeric score.
   *
   * @private
   */
  _severityToScore(severity) {
    const scores = { critical: 4, high: 3, medium: 2, low: 1 };
    return scores[severity] || 1;
  }

  /**
   * Helper: Calculate average severity from distribution.
   *
   * @private
   */
  _calculateAvgSeverity(severities) {
    const total = severities.critical + severities.high + severities.medium + severities.low;
    if (total === 0) return 0;

    const weighted = severities.critical * 4 + severities.high * 3 + severities.medium * 2 + severities.low * 1;
    return (weighted / total).toFixed(2);
  }

  /**
   * Helper: Generate insights from distribution analysis.
   *
   * @private
   */
  _generateDistributionInsights(bySeverity, byType, byHour) {
    const insights = [];

    // Severity insight
    const criticalCount = bySeverity.find(s => s.severity === 'critical')?.count || 0;
    if (criticalCount > 0) {
      insights.push(`${criticalCount} critical deviations require immediate attention`);
    }

    // Type insight
    if (byType.length > 0) {
      const topType = byType[0];
      insights.push(`Most common deviation type: ${topType.deviation_type} (${topType.count} occurrences)`);
    }

    // Hour insight
    if (byHour.length > 0) {
      const peakHour = byHour.reduce((max, curr) => curr.count > max.count ? curr : max);
      insights.push(`Peak deviation hour: ${peakHour.hour}:00 (${peakHour.count} deviations)`);
    }

    return insights;
  }

  /**
   * Helper: Generate insights from correlation analysis.
   *
   * @private
   */
  _generateCorrelationInsights(workloadCorrelation) {
    const insights = [];

    if (workloadCorrelation.length > 0) {
      const topOfficer = workloadCorrelation[0];
      insights.push(`Officer ${topOfficer.officer_id} has highest deviation count: ${topOfficer.deviation_count}`);

      // Check for high severity correlation
      const highSeverityOfficers = workloadCorrelation.filter(o => parseFloat(o.avg_severity_score) >= 3.0);
      if (highSeverityOfficers.length > 0) {
        insights.push(`${highSeverityOfficers.length} officers have avg severity score >= 3.0 (high/critical)`);
      }
    }

    return insights;
  }

  /**
   * Helper: Generate insights from time-series analysis.
   *
   * @private
   */
  _generateTimeSeriesInsights(dailyTrend, weeklyPattern) {
    const insights = [];

    // Daily trend insight
    if (dailyTrend.length > 0) {
      const recentDays = dailyTrend.slice(-7);
      const avgRecent = recentDays.reduce((sum, d) => sum + d.count, 0) / recentDays.length;
      insights.push(`Average ${avgRecent.toFixed(1)} deviations per day (last 7 days)`);
    }

    // Weekly pattern insight
    const maxDay = weeklyPattern.reduce((max, curr) => curr.count > max.count ? curr : max);
    insights.push(`Most deviations occur on ${maxDay.day} (${maxDay.count} total)`);

    return insights;
  }
}

module.exports = new StatisticalAnalysisService();
