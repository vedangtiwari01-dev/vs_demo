import { useState } from 'react';
import { Download, RefreshCw } from 'lucide-react';
import ModernLoading from '../common/ModernLoading';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const ResultsViewer = ({ analysisResult, isAnalyzing, onReanalyze }) => {
  const [activeTab, setActiveTab] = useState('overview');

  const handleDownload = () => {
    const dataStr = JSON.stringify(analysisResult, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `compliance-analysis-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (isAnalyzing) {
    return (
      <div className="flex items-center justify-center h-full bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50">
        <ModernLoading
          message="Analyzing compliance..."
          subMessage="Running ML pipeline and pattern detection"
          size="lg"
        />
      </div>
    );
  }

  if (!analysisResult) {
    return (
      <div className="flex items-center justify-center h-full p-8 bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full mx-auto mb-6 flex items-center justify-center shadow-2xl">
            <div className="w-12 h-12 border-4 border-white rounded-lg rotate-45"></div>
          </div>
          <h2 className="text-2xl font-semibold text-gray-800 mb-2">No Analysis Run Yet</h2>
          <p className="text-gray-600 mb-6">
            Select an SOP and Workflow Log, then click "Analyze Compliance" to begin
          </p>
          <div className="bg-white border border-gray-200 rounded-xl p-6 text-left shadow-lg">
            <p className="text-sm font-medium text-gray-800 mb-3">Sample Report Preview:</p>
            <ul className="text-sm text-gray-600 space-y-2">
              <li className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-1.5"></div>
                <span>Overview metrics and compliance rate</span>
              </li>
              <li className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-1.5"></div>
                <span>Deviations by type and severity</span>
              </li>
              <li className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-1.5"></div>
                <span>Behavioral patterns (AI-powered)</span>
              </li>
              <li className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-1.5"></div>
                <span>Hidden rules discovered</span>
              </li>
              <li className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-1.5"></div>
                <span>Systemic issues and recommendations</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  // Extract data from analysisResult
  const data = analysisResult.data || analysisResult;
  const deviations = data.deviations || [];
  const summary = data.summary || {};
  const patterns = data.patterns || analysisResult.patterns || {};

  console.log('Combined analysis result:', analysisResult);
  console.log('Deviations:', deviations);
  console.log('Patterns:', patterns);

  // Tab definitions (3 tabs - merged ML and Statistics)
  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'aiinsights', label: 'AI Insights' },
    { id: 'mlstats', label: 'ML & Statistics' },
  ];

  return (
    <div className="circuit-bg circuit-nodes min-h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-2xl border-b border-gray-200 relative overflow-hidden">
        <div className="p-6 relative z-10">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-3xl font-semibold text-primary-600">
              Analysis Report
            </h1>
            <div className="flex space-x-2">
              <button
                onClick={handleDownload}
                className="px-4 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-all flex items-center space-x-2 shadow-sm"
              >
                <Download className="w-4 h-4 text-primary-600" />
                <span className="text-gray-800 font-medium">Download</span>
              </button>
              <button
                onClick={onReanalyze}
                disabled={isAnalyzing}
                className="px-4 py-2 text-sm bg-gradient-to-r from-primary-600 to-secondary-600 text-white rounded-lg hover:from-primary-500 hover:to-secondary-500 transition-all flex items-center space-x-2 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className={`w-4 h-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
                <span className="font-medium">{isAnalyzing ? 'Analyzing...' : 'Re-analyze'}</span>
              </button>
            </div>
          </div>
          <p className="text-sm text-gray-600 font-medium">
            {analysisResult.workflow?.filename || 'Workflow'} vs {analysisResult.sop?.title || 'SOP'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Analyzed: {new Date(analysisResult.timestamp || Date.now()).toLocaleString()}
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 pb-0 relative z-10">
          <div className="flex space-x-1 border-b border-gray-200">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 text-sm font-medium transition-all relative ${
                  activeTab === tab.id
                    ? 'text-primary-600 bg-gray-50'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                <span>{tab.label}</span>
                {activeTab === tab.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600"></div>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && <OverviewTab data={data} summary={summary} deviations={deviations} patterns={patterns} analysisResult={analysisResult} />}
        {activeTab === 'aiinsights' && <AIInsightsTab patterns={patterns} />}
        {activeTab === 'mlstats' && <MLStatisticsTab patterns={patterns} deviations={deviations} />}
      </div>
    </div>
  );
};

// ============================================================================
// TAB 1: OVERVIEW - BASIC INFORMATION ONLY (NO CHARTS)
// ============================================================================
const OverviewTab = ({ data, patterns, deviations, analysisResult }) => {
  // Count severity directly from deviations array
  const severityCounts = deviations.reduce((acc, dev) => {
    const severity = dev.severity || 'Unknown';
    acc[severity] = (acc[severity] || 0) + 1;
    return acc;
  }, {});

  const critical = severityCounts.Critical || severityCounts.critical || 0;
  const high = severityCounts.High || severityCounts.high || 0;
  const medium = severityCounts.Medium || severityCounts.medium || 0;
  const low = severityCounts.Low || severityCounts.low || 0;
  const totalDeviations = deviations.length;

  // Count unique officers
  const uniqueOfficers = [...new Set(deviations.map(d => d.officer_id).filter(Boolean))];
  const totalOfficers = uniqueOfficers.length;

  // Get unique case IDs
  const uniqueCases = [...new Set(deviations.map(d => d.case_id).filter(Boolean))];
  const totalCases = uniqueCases.length;

  // Get workflow fields from first deviation or workflow metadata
  const workflowFields = analysisResult.workflow?.fields ||
                        analysisResult.workflow?.columns ||
                        (deviations.length > 0 ? Object.keys(deviations[0]).filter(k => k !== 'id') : []);

  // Get total logs count
  const totalLogs = analysisResult.workflow?.total_logs ||
                    analysisResult.workflow?.log_count ||
                    'N/A';

  // Get SOP rules
  const sopRules = analysisResult.sop?.rules || [];

  return (
    <div className="space-y-6">
      {/* 1. Basic Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Cases"
          value={totalCases}
        />
        <MetricCard
          label="Total Logs"
          value={totalLogs}
        />
        <MetricCard
          label="Total Deviations"
          value={totalDeviations}
        />
        <MetricCard
          label="Total Officers"
          value={totalOfficers}
        />
      </div>

      {/* 2. Severity Breakdown - COMPACTED */}
      <div className="widget-transparent rounded-xl shadow-xl p-4 border border-primary-300">
        <h3 className="text-base font-semibold text-primary-600 mb-3">Deviations by Severity</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="bg-red-50/40 border-l-4 border-red-500 p-3 rounded">
            <div className="text-xs text-red-700 font-medium">Critical</div>
            <div className="text-lg font-medium text-red-600">{critical}</div>
            <div className="text-xs text-red-500">
              {totalDeviations > 0 ? Math.round((critical / totalDeviations) * 100) : 0}%
            </div>
          </div>
          <div className="bg-orange-50/40 border-l-4 border-orange-500 p-3 rounded">
            <div className="text-xs text-orange-700 font-medium">High</div>
            <div className="text-lg font-medium text-orange-600">{high}</div>
            <div className="text-xs text-orange-500">
              {totalDeviations > 0 ? Math.round((high / totalDeviations) * 100) : 0}%
            </div>
          </div>
          <div className="bg-yellow-50/40 border-l-4 border-yellow-500 p-3 rounded">
            <div className="text-xs text-yellow-700 font-medium">Medium</div>
            <div className="text-lg font-medium text-yellow-600">{medium}</div>
            <div className="text-xs text-yellow-500">
              {totalDeviations > 0 ? Math.round((medium / totalDeviations) * 100) : 0}%
            </div>
          </div>
          <div className="bg-blue-50/40 border-l-4 border-blue-500 p-3 rounded">
            <div className="text-xs text-blue-700 font-medium">Low</div>
            <div className="text-lg font-medium text-blue-600">{low}</div>
            <div className="text-xs text-blue-500">
              {totalDeviations > 0 ? Math.round((low / totalDeviations) * 100) : 0}%
            </div>
          </div>
        </div>
      </div>

      {/* 3. Data Cleaning Report */}
      {(patterns?.cleaning_report || patterns?.data_quality) && (
        <div className="widget-transparent rounded-xl shadow-xl p-4 border border-primary-300">
          <h3 className="text-base font-semibold text-primary-600 mb-3">Data Cleaning Report</h3>

          {patterns.cleaning_report && (
            <div className="mb-6">
              <h4 className="text-xs font-medium text-gray-700 mb-3 flex items-center">
                <svg className="w-4 h-4 mr-2 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                Preprocessing Steps
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries(patterns.cleaning_report).map(([step, value]) => (
                  <div key={step} className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-3 border border-gray-200 hover:shadow-md transition-shadow">
                    <p className="text-xs font-medium text-gray-500 uppercase mb-1">{step.replace(/_/g, ' ')}</p>
                    <p className="text-sm font-semibold text-primary-600">
                      {typeof value === 'object' ? JSON.stringify(value) : value}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {patterns.data_quality && (
            <div>
              <h4 className="text-xs font-medium text-gray-700 mb-3 flex items-center">
                <svg className="w-4 h-4 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Data Quality Metrics
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries(patterns.data_quality).map(([metric, value]) => (
                  <div key={metric} className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg p-3 border border-green-200 hover:shadow-md transition-shadow">
                    <p className="text-xs font-medium text-gray-600 uppercase mb-1">{metric.replace(/_/g, ' ')}</p>
                    <p className="text-lg font-semibold text-gray-800">
                      {typeof value === 'number' ? value.toFixed(2) : value}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 4. All Deviations List */}
      <details className="widget-transparent rounded-xl shadow-xl border border-primary-300">
        <summary className="px-6 py-4 cursor-pointer font-medium text-primary-600 hover:bg-primary-50/50 transition-colors">
          All Deviations ({totalDeviations} total)
        </summary>
        <div className="px-6 pb-4 max-h-96 overflow-y-auto">
          <div className="space-y-2">
            {deviations.map((dev, idx) => (
              <div key={idx} className={`p-3 rounded border-l-4 ${
                (dev.severity === 'Critical' || dev.severity === 'critical') ? 'bg-red-50 border-red-500' :
                (dev.severity === 'High' || dev.severity === 'high') ? 'bg-orange-50 border-orange-500' :
                (dev.severity === 'Medium' || dev.severity === 'medium') ? 'bg-yellow-50 border-yellow-500' :
                'bg-blue-50 border-blue-500'
              }`}>
                <div className="flex items-start justify-between mb-1">
                  <div className="font-medium text-gray-800 text-sm">
                    {dev.deviation_type || dev.type || 'Deviation'}
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    (dev.severity === 'Critical' || dev.severity === 'critical') ? 'bg-red-100 text-red-800' :
                    (dev.severity === 'High' || dev.severity === 'high') ? 'bg-orange-100 text-orange-800' :
                    (dev.severity === 'Medium' || dev.severity === 'medium') ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {dev.severity}
                  </span>
                </div>
                <div className="text-xs text-gray-600 space-y-1">
                  {dev.case_id && <div><span className="font-medium">Case:</span> {dev.case_id}</div>}
                  {dev.officer_id && <div><span className="font-medium">Officer:</span> {dev.officer_id}</div>}
                  {dev.description && <div className="mt-1">{dev.description}</div>}
                  {dev.justification && <div className="mt-1 italic">"{dev.justification}"</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </details>

      {/* 5. Workflow Log Fields (Collapsed) */}
      {workflowFields.length > 0 && (
        <details className="widget-transparent rounded-xl shadow-xl border border-primary-300">
          <summary className="px-6 py-4 cursor-pointer font-medium text-primary-600 hover:bg-primary-50/50 transition-colors">
            Workflow Log Fields ({workflowFields.length} fields)
          </summary>
          <div className="px-6 pb-4">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {workflowFields.map((field, idx) => (
                <div key={idx} className="bg-gray-50 px-3 py-2 rounded text-sm text-gray-600 border border-gray-200/50">
                  {field}
                </div>
              ))}
            </div>
          </div>
        </details>
      )}

      {/* 6. SOP Rules (Collapsed) */}
      {sopRules.length > 0 && (
        <details className="widget-transparent rounded-xl shadow-xl border border-primary-300">
          <summary className="px-6 py-4 cursor-pointer font-medium text-primary-600 hover:bg-primary-50/50 transition-colors">
            SOP Rules ({sopRules.length} rules)
          </summary>
          <div className="px-6 pb-4 space-y-3">
            {sopRules.map((rule, idx) => {
              // Handle different rule formats
              const ruleType = rule.rule_type || rule.type || 'Rule';
              const ruleName = rule.name || rule.rule_name || `Rule ${idx + 1}`;
              const ruleDescription = rule.description || rule.rule_description || rule.condition || '';
              const ruleSeverity = rule.severity || '';

              return (
                <div key={idx} className="bg-gray-50 p-4 rounded border-l-4 border-primary-500">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium text-gray-800">
                      {ruleName} {ruleType && `(${ruleType})`}
                    </div>
                    {ruleSeverity && (
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        ruleSeverity.toLowerCase() === 'critical' ? 'bg-red-100 text-red-800' :
                        ruleSeverity.toLowerCase() === 'high' ? 'bg-orange-100 text-orange-800' :
                        ruleSeverity.toLowerCase() === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {ruleSeverity}
                      </span>
                    )}
                  </div>
                  {ruleDescription && (
                    <div className="text-sm text-gray-600">{ruleDescription}</div>
                  )}
                </div>
              );
            })}
          </div>
        </details>
      )}

    </div>
  );
};

// ============================================================================
// TAB 2: AI INSIGHTS - ALL AI RESPONSES CONSOLIDATED (NO OVERALL SUMMARY)
// ============================================================================
const AIInsightsTab = ({ patterns }) => {
  return (
    <div className="space-y-4">
      {/* 1. Time Patterns & Trends */}
      {patterns.time_patterns && patterns.time_patterns.length > 0 && (
        <details open className="widget-transparent rounded-xl shadow-xl border border-primary-300">
          <summary className="px-6 py-4 cursor-pointer font-medium text-primary-600 hover:bg-primary-50/50 transition-colors">
            Time Patterns & Trends ({patterns.time_patterns.length})
          </summary>
          <div className="px-6 pb-4 space-y-3">
            {patterns.time_patterns.map((pattern, idx) => (
              <div key={idx} className="bg-gray-50 p-3 rounded-lg border-l-4 border-blue-500">
                <div className="text-sm font-medium text-gray-800 mb-2">{pattern.pattern || `Pattern ${idx + 1}`}</div>
                <div className="text-xs text-gray-600 mb-2">{pattern.description}</div>
                {pattern.evidence && (
                  <div className="text-xs text-gray-500 bg-white/50 p-2 rounded">
                    <strong>Evidence:</strong> {pattern.evidence}
                  </div>
                )}
              </div>
            ))}
          </div>
        </details>
      )}

      {/* 2. Behavioral Patterns */}
      {patterns.behavioral_patterns && patterns.behavioral_patterns.length > 0 && (
        <details className="widget-transparent rounded-xl shadow-xl border border-primary-300">
          <summary className="px-6 py-4 cursor-pointer font-medium text-primary-600 hover:bg-primary-50/50 transition-colors">
            Behavioral Patterns ({patterns.behavioral_patterns.length})
          </summary>
          <div className="px-6 pb-4 space-y-3">
            {patterns.behavioral_patterns.map((pattern, idx) => (
              <div key={idx} className="bg-gray-50 p-3 rounded-lg border-l-4 border-purple-500">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium text-gray-800">{pattern.pattern || `Pattern ${idx + 1}`}</div>
                  {pattern.risk_level && (
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      pattern.risk_level === 'High' ? 'bg-red-100 text-red-700' :
                      pattern.risk_level === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {pattern.risk_level} Risk
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-600 mb-2">{pattern.description}</div>
                {pattern.frequency && (
                  <div className="text-xs text-gray-500 mb-1">
                    <strong>Frequency:</strong> {pattern.frequency}
                  </div>
                )}
                {pattern.officers_involved && (
                  <div className="text-xs text-gray-500 bg-gray-100 p-2 rounded">
                    <strong>Officers:</strong> {pattern.officers_involved.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </details>
      )}

      {/* 3. Hidden Rules */}
      {patterns.hidden_rules && patterns.hidden_rules.length > 0 && (
        <details className="widget-transparent rounded-xl shadow-xl border border-primary-300">
          <summary className="px-6 py-4 cursor-pointer font-medium text-primary-600 hover:bg-primary-50/50 transition-colors">
            Hidden Rules ({patterns.hidden_rules.length})
          </summary>
          <div className="px-6 pb-4 space-y-3">
            {patterns.hidden_rules.map((rule, idx) => (
              <div key={idx} className="bg-gray-50 p-3 rounded-lg border-l-4 border-amber-500">
                <div className="text-sm font-medium text-gray-800 mb-2">{rule.rule || `Rule ${idx + 1}`}</div>
                <div className="text-xs text-gray-600 mb-2">{rule.description}</div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {rule.confidence && (
                    <div className="bg-gray-100 p-2 rounded">
                      <strong>Confidence:</strong> {rule.confidence}
                    </div>
                  )}
                  {rule.compliance_impact && (
                    <div className="bg-gray-100 p-2 rounded">
                      <strong>Impact:</strong> {rule.compliance_impact}
                    </div>
                  )}
                </div>
                {rule.evidence && (
                  <div className="text-xs text-gray-600 bg-gray-100 p-2 rounded mt-2">
                    <strong>Evidence:</strong> {rule.evidence}
                  </div>
                )}
              </div>
            ))}
          </div>
        </details>
      )}

      {/* 4. Systemic Issues */}
      {patterns.systemic_issues && patterns.systemic_issues.length > 0 && (
        <details className="widget-transparent rounded-xl shadow-xl border border-primary-300">
          <summary className="px-6 py-4 cursor-pointer font-medium text-primary-600 hover:bg-primary-50/50 transition-colors">
            Systemic Issues ({patterns.systemic_issues.length})
          </summary>
          <div className="px-6 pb-4 space-y-3">
            {patterns.systemic_issues.map((issue, idx) => (
              <div key={idx} className="bg-gray-50 p-3 rounded-lg border-l-4 border-red-500">
                <div className="text-sm font-medium text-gray-800 mb-2">{issue.issue || `Issue ${idx + 1}`}</div>
                <div className="text-xs text-gray-600 mb-2">{issue.description}</div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {issue.frequency && (
                    <div className="bg-gray-100 p-2 rounded">
                      <strong>Frequency:</strong> {issue.frequency}
                    </div>
                  )}
                  {issue.impact && (
                    <div className="bg-gray-100 p-2 rounded">
                      <strong>Impact:</strong> {issue.impact}
                    </div>
                  )}
                </div>
                {issue.recommended_fix && (
                  <div className="text-xs text-green-800 bg-gray-100 p-2 rounded mt-2">
                    <span className="font-medium">Fix:</span> {issue.recommended_fix}
                  </div>
                )}
              </div>
            ))}
          </div>
        </details>
      )}

      {/* 5. Risk Insights */}
      {patterns.risk_insights && patterns.risk_insights.length > 0 && (
        <details className="widget-transparent rounded-xl shadow-xl border border-primary-300">
          <summary className="px-6 py-4 cursor-pointer font-medium text-primary-600 hover:bg-primary-50/50 transition-colors">
            Risk Insights ({patterns.risk_insights.length})
          </summary>
          <div className="px-6 pb-4 space-y-2">
            {patterns.risk_insights.map((insight, idx) => (
              <div key={idx} className="bg-gray-50 p-3 rounded-lg border-l-4 border-orange-500">
                <div className="text-xs text-gray-600">{insight.description || insight}</div>
              </div>
            ))}
          </div>
        </details>
      )}

      {/* 6. Recommendations - FIXED FORMATTING */}
      {patterns.recommendations && patterns.recommendations.length > 0 && (
        <details className="widget-transparent rounded-xl shadow-xl border border-primary-300">
          <summary className="px-6 py-4 cursor-pointer font-medium text-primary-600 hover:bg-primary-50/50 transition-colors">
            Recommendations ({patterns.recommendations.length})
          </summary>
          <div className="px-6 pb-4 space-y-2">
            {patterns.recommendations.map((rec, idx) => {
              // Handle different recommendation formats and clean text
              let text = '';
              if (typeof rec === 'string') {
                text = rec;
              } else if (rec.recommendation) {
                text = rec.recommendation;
              } else if (rec.text) {
                text = rec.text;
              }

              // Clean up recommendation text:
              // 1. Remove leading commas
              // 2. Remove brackets from severity tags but keep the tag itself
              //    [CRITICAL - 1 WEEK] → CRITICAL - 1 WEEK
              text = text
                .replace(/^[,\s]+/, '') // Remove leading commas and spaces
                .replace(/^\[([A-Z0-9\s\-]+)\]\s*/, '$1 ') // Remove brackets, keep tag content
                .trim();

              return (
                <div key={idx} className="flex items-start space-x-3 bg-white/50 p-3 rounded-lg border-l-4 border-green-500">
                  <div className="flex-shrink-0 w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                    {idx + 1}
                  </div>
                  <div className="text-xs text-gray-800 flex-1">{text}</div>
                </div>
              );
            })}
          </div>
        </details>
      )}
    </div>
  );
};

// ============================================================================
// TAB 3: ML & STATISTICS - MERGED TAB
// ============================================================================
const MLStatisticsTab = ({ patterns, deviations }) => {
  const officerStats = patterns.statistical_summary?.officer_statistics || {};
  const mlSummary = patterns.ml_summary || {};
  const statSummary = patterns.statistical_summary || {};
  const timeSeries = statSummary.time_series || {};
  const temporal = statSummary.temporal_patterns || {};
  const advancedCorr = statSummary.advanced_correlations || {};
  const controlCharts = statSummary.control_charts || {};

  // Compute officer stats from deviations if not available
  let topOfficers = officerStats.top_officers || [];
  if (topOfficers.length === 0 && deviations.length > 0) {
    const officerMap = deviations.reduce((acc, dev) => {
      const officer = dev.officer_id;
      if (!officer) return acc;
      if (!acc[officer]) {
        acc[officer] = { officer_id: officer, total_deviations: 0, Critical: 0, High: 0, Medium: 0, Low: 0 };
      }
      acc[officer].total_deviations++;
      // Handle case-insensitive severity
      const severity = dev.severity || 'Unknown';
      const severityCapitalized = severity.charAt(0).toUpperCase() + severity.slice(1).toLowerCase();
      if (acc[officer][severityCapitalized] !== undefined) {
        acc[officer][severityCapitalized]++;
      }
      return acc;
    }, {});
    topOfficers = Object.values(officerMap).sort((a, b) => b.total_deviations - a.total_deviations);
  }

  // Get all available statistics
  const allStats = statSummary || {};

  // Get ML metadata for more detailed info
  const mlMetadata = patterns.ml_metadata || {};
  const temporalPatterns = statSummary.temporal_patterns || {};

  // Debug logging for temporal patterns
  console.log('[MLStatisticsTab] temporal_patterns:', temporalPatterns);
  console.log('[MLStatisticsTab] has hour_distribution:', !!temporalPatterns?.hour_distribution);
  console.log('[MLStatisticsTab] has day_distribution:', !!temporalPatterns?.day_distribution);
  if (temporalPatterns?.hour_distribution) {
    console.log('[MLStatisticsTab] hour_distribution keys:', Object.keys(temporalPatterns.hour_distribution));
  }
  if (temporalPatterns?.day_distribution) {
    console.log('[MLStatisticsTab] day_distribution keys:', Object.keys(temporalPatterns.day_distribution));
  }

  return (
    <div className="space-y-6">
      {/* Simplified ML Summary - 3 Sentences */}
      <div className="widget-transparent rounded-xl shadow-xl p-4 border border-primary-300">
        <h3 className="text-lg font-semibold text-primary-600 mb-3">Machine Learning Analysis</h3>
        {mlSummary.ml_applied ? (
          <div className="space-y-2 text-xs text-gray-800">
            <p>
              <span className="font-medium">Feature Engineering:</span> Created{' '}
              {(() => {
                // Try multiple sources for feature count
                const featureCount =
                  mlMetadata.feature_engineering?.n_features ||
                  mlMetadata.feature_engineering?.features_created ||
                  mlSummary.features_created ||
                  mlSummary.n_features ||
                  (mlSummary.feature_engineering ?
                    (mlSummary.feature_engineering.n_features || mlSummary.feature_engineering.features_created) :
                    null);

                return featureCount || 'several';
              })()}{' '}
              features using{' '}
              {mlMetadata.feature_engineering?.methods?.join(', ') ||
               mlSummary.feature_methods ||
               'standard methods'}.
            </p>
            <p>
              <span className="font-medium">Clustering:</span> Identified {mlMetadata.clustering?.n_clusters || mlSummary.clusters_found || 0} clusters
              using {mlMetadata.clustering?.method || mlSummary.clustering_method || 'DBSCAN'}
              {mlMetadata.clustering?.parameters?.eps ? ` with eps=${mlMetadata.clustering.parameters.eps}` : ''}.
            </p>
            <p>
              <span className="font-medium">Anomaly Detection:</span> Detected {mlMetadata.anomaly_detection?.n_anomalies || mlSummary.anomalies_detected || 0} anomalies
              using {mlMetadata.anomaly_detection?.method || mlSummary.anomaly_method || 'Isolation Forest'}.
            </p>
          </div>
        ) : (
          <p className="text-xs text-gray-600">ML analysis not applied - dataset too small or ML unavailable.</p>
        )}
      </div>

      {/* VISUALIZATION SECTION - 4 CHARTS */}
      <div className="space-y-6">
        <h2 className="text-xl font-semibold text-primary-600 mb-4">
          Deviation Analytics
        </h2>

        {/* Row 1: Line Charts - Temporal Trends */}
        <div className="grid grid-cols-2 gap-4">
          {/* Chart 1: Hourly Deviation Trend */}
          {temporalPatterns?.hour_distribution && Object.keys(temporalPatterns.hour_distribution).length > 0 ? (
            <div className="widget-transparent rounded-lg shadow-xl p-3 border border-primary-300">
              <h4 className="text-sm font-semibold text-primary-600 mb-2">Hourly Deviation Trend</h4>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={
                  Object.entries(temporalPatterns.hour_distribution)
                    .map(([hour, count]) => ({ hour: `${hour}:00`, count }))
                    .sort((a, b) => parseInt(a.hour) - parseInt(b.hour))
                }>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(6, 182, 212, 0.2)" />
                  <XAxis
                    dataKey="hour"
                    tick={{ fontSize: 10, fill: '#1f2937' }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis tick={{ fontSize: 10, fill: '#1f2937' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.9)',
                      border: '1px solid rgba(6, 182, 212, 0.3)',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#0891b2"
                    strokeWidth={2}
                    dot={{ fill: '#0891b2', r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="widget-transparent rounded-lg shadow-xl p-3 border border-primary-300">
              <h4 className="text-sm font-semibold text-primary-600 mb-2">Hourly Deviation Trend</h4>
              <div className="flex items-center justify-center h-[200px] text-xs text-gray-500">
                No hourly temporal data available
              </div>
            </div>
          )}

          {/* Chart 2: Daily Deviation Trend */}
          {temporalPatterns?.day_distribution && Object.keys(temporalPatterns.day_distribution).length > 0 ? (
            <div className="widget-transparent rounded-lg shadow-xl p-3 border border-primary-300">
              <h4 className="text-sm font-semibold text-primary-600 mb-2">Daily Deviation Trend</h4>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={
                  ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    .map(day => ({ day, count: temporalPatterns.day_distribution[day] || 0 }))
                }>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(6, 182, 212, 0.2)" />
                  <XAxis
                    dataKey="day"
                    tick={{ fontSize: 10, fill: '#1f2937' }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis tick={{ fontSize: 10, fill: '#1f2937' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.9)',
                      border: '1px solid rgba(6, 182, 212, 0.3)',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#0891b2"
                    strokeWidth={2}
                    dot={{ fill: '#0891b2', r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="widget-transparent rounded-lg shadow-xl p-3 border border-primary-300">
              <h4 className="text-sm font-semibold text-primary-600 mb-2">Daily Deviation Trend</h4>
              <div className="flex items-center justify-center h-[200px] text-xs text-gray-500">
                No daily temporal data available
              </div>
            </div>
          )}
        </div>

        {/* Row 2: Officer Analysis - Stacked Bar + Pie Chart */}
        <div className="grid grid-cols-2 gap-4">
          {/* Chart 3: Stacked Bar - Officer Deviations by Severity */}
          {topOfficers.length > 0 && (
            <div className="widget-transparent rounded-lg shadow-xl p-3 border border-primary-300">
              <h4 className="text-sm font-semibold text-primary-600 mb-2">Officer Deviations by Severity</h4>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={
                  topOfficers.slice(0, 10).map(officer => ({
                    officer: officer.officer_id,
                    Critical: officer.Critical || 0,
                    High: officer.High || 0,
                    Medium: officer.Medium || 0,
                    Low: officer.Low || 0
                  }))
                }>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(6, 182, 212, 0.2)" />
                  <XAxis
                    dataKey="officer"
                    tick={{ fontSize: 9, fill: '#1f2937' }}
                    angle={-45}
                    textAnchor="end"
                    height={70}
                  />
                  <YAxis tick={{ fontSize: 10, fill: '#1f2937' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.9)',
                      border: '1px solid rgba(6, 182, 212, 0.3)',
                      borderRadius: '8px',
                      fontSize: '11px'
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar dataKey="Critical" stackId="a" fill="#dc2626" />
                  <Bar dataKey="High" stackId="a" fill="#ea580c" />
                  <Bar dataKey="Medium" stackId="a" fill="#ca8a04" />
                  <Bar dataKey="Low" stackId="a" fill="#2563eb" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Chart 4: Pie Chart - Officer Deviation Percentage */}
          {topOfficers.length > 0 && (() => {
            const totalDevs = topOfficers.reduce((sum, o) => sum + o.total_deviations, 0);
            const pieData = topOfficers.slice(0, 8).map(officer => ({
              name: officer.officer_id,
              value: officer.total_deviations,
              percentage: ((officer.total_deviations / totalDevs) * 100).toFixed(1)
            }));
            const COLORS = ['#0891b2', '#2563eb', '#7c3aed', '#db2777', '#dc2626', '#ea580c', '#ca8a04', '#059669'];

            return (
              <div className="widget-transparent rounded-lg shadow-xl p-3 border border-primary-300">
                <h4 className="text-sm font-semibold text-primary-600 mb-2">Officer Deviation Distribution</h4>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name}: ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        border: '1px solid rgba(6, 182, 212, 0.3)',
                        borderRadius: '8px',
                        fontSize: '11px'
                      }}
                      formatter={(value, name, props) => [`${value} (${props.payload.percentage}%)`, name]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            );
          })()}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// HELPER COMPONENTS
// ============================================================================
const MetricCard = ({ label, value }) => (
  <div className="widget-transparent border-primary-300 rounded-xl p-3 shadow-lg hover:shadow-xl transition-all">
    <div className="text-sm text-gray-600 font-medium mb-2">{label}</div>
    <div className="text-2xl font-medium text-primary-600">
      {value}
    </div>
  </div>
);

const StatCard = ({ label, value }) => (
  <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-md">
    <div className="text-xs text-gray-600 mb-1 font-medium">{label}</div>
    <div className="text-xl font-medium text-gray-800">{value || 'N/A'}</div>
  </div>
);

export default ResultsViewer;
