import { useState } from 'react';
import { ChevronDown, ChevronRight, Loader, Download, RefreshCw } from 'lucide-react';

const ResultsViewer = ({ analysisResult, isAnalyzing, onReanalyze }) => {
  const [expandedSections, setExpandedSections] = useState({
    overview: true,
    deviationsByType: true,
    deviationsTable: false,
    behavioral: false,
    hiddenRules: false,
    systemic: false,
    time: false,
    risk: false,
    recommendations: false
  });

  const [expandedOfficers, setExpandedOfficers] = useState({});

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

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const toggleOfficer = (officerId) => {
    setExpandedOfficers(prev => ({
      ...prev,
      [officerId]: !prev[officerId]
    }));
  };

  if (isAnalyzing) {
    return (
      <div className="flex items-center justify-center h-full bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50">
        <div className="text-center">
          <div className="relative">
            <div className="w-20 h-20 border-4 border-primary-200 rounded-full mx-auto mb-6"></div>
            <Loader className="w-12 h-12 text-primary-600 animate-spin mx-auto mb-4 absolute top-4 left-1/2 transform -translate-x-1/2" />
          </div>
          <p className="text-secondary-800 font-semibold text-lg">Analyzing compliance...</p>
          <p className="text-sm text-secondary-600 mt-2">This may take a few moments</p>
        </div>
      </div>
    );
  }

  if (!analysisResult) {
    return (
      <div className="flex items-center justify-center h-full p-8 bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-secondary-600 rounded-full mx-auto mb-6 flex items-center justify-center shadow-2xl">
            <div className="w-12 h-12 border-4 border-white rounded-lg rotate-45"></div>
          </div>
          <h2 className="text-2xl font-bold text-secondary-900 mb-2">No Analysis Run Yet</h2>
          <p className="text-secondary-700 mb-6">
            Select an SOP and Workflow Log, then click "Analyze Compliance" to begin
          </p>
          <div className="bg-white/70 backdrop-blur-sm border border-primary-300 rounded-xl p-6 text-left shadow-lg">
            <p className="text-sm font-semibold text-secondary-800 mb-3">Sample Report Preview:</p>
            <ul className="text-sm text-secondary-700 space-y-2">
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

  const { deviations, summary, patterns } = analysisResult;

  return (
    <div className="p-6 bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50 min-h-screen">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-2xl p-6 mb-6 border border-primary-200 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-primary-400/20 to-transparent rounded-full blur-3xl"></div>
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-secondary-600">
              Analysis Report
            </h1>
            <div className="flex space-x-2">
              <button
                onClick={handleDownload}
                className="px-4 py-2 text-sm bg-white border border-primary-300 rounded-lg hover:bg-primary-50 hover:border-primary-400 transition-all flex items-center space-x-2 shadow-sm"
              >
                <Download className="w-4 h-4 text-primary-600" />
                <span className="text-secondary-700 font-medium">Download</span>
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
          <p className="text-sm text-secondary-700 font-medium">
            {analysisResult.workflow.filename} vs {analysisResult.sop.title}
          </p>
          <p className="text-xs text-secondary-600 mt-1">
            Analyzed: {new Date(analysisResult.timestamp).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Overview Metrics */}
      <Section
        title="📈 OVERVIEW METRICS"
        isExpanded={expandedSections.overview}
        onToggle={() => toggleSection('overview')}
      >
        <div className="grid grid-cols-3 gap-4 mb-4">
          <MetricCard label="Total Cases" value={summary.total_cases || 0} />
          <MetricCard label="Total Logs" value={summary.total_logs || 0} />
          <MetricCard label="Officers" value={summary.total_officers || 0} />
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <h4 className="font-medium text-gray-800 mb-2">⚠️ Deviations Found: {summary.total_deviations || 0}</h4>
          <div className="space-y-1 ml-4">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center space-x-2">
                <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                <span>Critical</span>
              </span>
              <span className="font-medium">{summary.critical || 0} ({Math.round((summary.critical || 0) / (summary.total_deviations || 1) * 100)}%)</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center space-x-2">
                <span className="w-3 h-3 bg-orange-500 rounded-full"></span>
                <span>High</span>
              </span>
              <span className="font-medium">{summary.high || 0} ({Math.round((summary.high || 0) / (summary.total_deviations || 1) * 100)}%)</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center space-x-2">
                <span className="w-3 h-3 bg-yellow-500 rounded-full"></span>
                <span>Medium</span>
              </span>
              <span className="font-medium">{summary.medium || 0} ({Math.round((summary.medium || 0) / (summary.total_deviations || 1) * 100)}%)</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center space-x-2">
                <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                <span>Low</span>
              </span>
              <span className="font-medium">{summary.low || 0} ({Math.round((summary.low || 0) / (summary.total_deviations || 1) * 100)}%)</span>
            </div>
          </div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-800">✅ Compliance Rate:</span>
            <span className="text-2xl font-bold text-green-600">
              {((1 - (summary.total_deviations || 0) / Math.max(summary.total_logs || 1, 1)) * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </Section>

      {/* Deviations by Type */}
      <Section
        title="🔍 DEVIATIONS BY TYPE"
        isExpanded={expandedSections.deviationsByType}
        onToggle={() => toggleSection('deviationsByType')}
      >
        <div className="space-y-2">
          {Object.entries(
            deviations.reduce((acc, dev) => {
              acc[dev.deviation_type] = (acc[dev.deviation_type] || 0) + 1;
              return acc;
            }, {})
          ).map(([type, count]) => (
            <div key={type} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <span className="text-sm font-medium text-gray-700 capitalize">{type.replace(/_/g, ' ')}</span>
              <div className="flex items-center space-x-3">
                <span className="text-sm font-bold text-gray-800">{count} ({Math.round(count / deviations.length * 100)}%)</span>
              </div>
            </div>
          ))}
        </div>
        <button
          onClick={() => toggleSection('deviationsTable')}
          className="mt-4 w-full py-2 border border-gray-300 rounded hover:bg-gray-50 text-sm font-medium text-gray-700 transition-colors"
        >
          {expandedSections.deviationsTable ? '🔼 Hide' : '🔽 Show'} All Deviations Table
        </button>
      </Section>

      {/* All Deviations Table */}
      {expandedSections.deviationsTable && (
        <Section
          title="📋 ALL DEVIATIONS TABLE"
          isExpanded={true}
          onToggle={() => toggleSection('deviationsTable')}
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 border-b-2 border-gray-300">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold text-gray-700">Case ID</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-700">Officer</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-700">Type</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-700">Severity</th>
                  <th className="px-3 py-2 text-left font-semibold text-gray-700">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {deviations.map((dev, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-mono text-xs text-gray-600">{dev.case_id}</td>
                    <td className="px-3 py-2 text-gray-700">{dev.officer_id}</td>
                    <td className="px-3 py-2">
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                        {dev.deviation_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-1 text-xs rounded font-medium ${
                        dev.severity === 'critical' ? 'bg-red-100 text-red-700' :
                        dev.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                        dev.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {dev.severity.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-gray-600 max-w-md truncate" title={dev.description}>
                      {dev.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {/* Behavioral Patterns */}
      {patterns?.behavioral_patterns && patterns.behavioral_patterns.length > 0 && (
        <Section
          title="👤 BEHAVIORAL PATTERNS (AI-Powered)"
          isExpanded={expandedSections.behavioral}
          onToggle={() => toggleSection('behavioral')}
        >
          <div className="space-y-4">
            {patterns.behavioral_patterns.map((pattern, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-gray-800">Pattern {idx + 1}: {pattern.pattern}</h4>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    pattern.risk_level === 'high' ? 'bg-red-100 text-red-700' :
                    pattern.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    🔴 Risk: {pattern.risk_level?.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{pattern.supporting_evidence}</p>
                <div className="text-xs text-gray-500">
                  Frequency: {pattern.frequency}
                </div>
                {pattern.officers_involved && pattern.officers_involved.length > 0 && (
                  <div className="mt-2">
                    <button
                      onClick={() => toggleOfficer(`pattern-${idx}`)}
                      className="text-sm text-blue-600 hover:underline flex items-center space-x-1"
                    >
                      <span>📊 View Officer Details</span>
                      {expandedOfficers[`pattern-${idx}`] ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </button>
                    {expandedOfficers[`pattern-${idx}`] && (
                      <div className="mt-3 ml-8 p-4 bg-gray-50 border-l-4 border-blue-500">
                        <h5 className="font-medium text-gray-800 mb-2">Officer Details</h5>
                        <div className="space-y-2 text-sm">
                          {pattern.officers_involved.map((officer, oidx) => (
                            <div key={oidx} className="text-gray-700">
                              • Officer: {officer}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Hidden Rules */}
      {patterns?.hidden_rules && patterns.hidden_rules.length > 0 && (
        <Section
          title="🎯 HIDDEN RULES DISCOVERED"
          isExpanded={expandedSections.hiddenRules}
          onToggle={() => toggleSection('hiddenRules')}
        >
          <div className="space-y-3">
            {patterns.hidden_rules.map((rule, idx) => (
              <div key={idx} className="border-l-4 border-yellow-400 bg-yellow-50 p-4 rounded">
                <h4 className="font-medium text-gray-800 mb-1">Rule {idx + 1}: {rule.rule}</h4>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Confidence: <span className="font-medium">{rule.confidence}</span> ({rule.evidence})</div>
                  <div>Compliance Impact: <span className="font-medium text-red-600">{rule.compliance_impact}</span></div>
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Recommendations */}
      {patterns?.recommendations && patterns.recommendations.length > 0 && (
        <Section
          title="💡 RECOMMENDATIONS"
          isExpanded={expandedSections.recommendations}
          onToggle={() => toggleSection('recommendations')}
        >
          <div className="space-y-2">
            {patterns.recommendations.map((rec, idx) => (
              <div key={idx} className="flex items-start space-x-2 p-3 bg-blue-50 border border-blue-200 rounded">
                <span className="text-blue-600 font-bold">{idx + 1}.</span>
                <span className="text-sm text-gray-700">{rec}</span>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
};

// Helper Components
const Section = ({ title, isExpanded, onToggle, children }) => (
  <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg mb-4 border border-primary-200 overflow-hidden relative">
    <div className="absolute top-0 right-0 w-32 h-32 bg-primary-400/10 rounded-full blur-2xl"></div>
    <div
      className="p-4 cursor-pointer hover:bg-primary-50/50 flex items-center justify-between transition-all relative z-10"
      onClick={onToggle}
    >
      <h3 className="font-bold text-secondary-800">{title}</h3>
      {isExpanded ? <ChevronDown className="w-5 h-5 text-primary-600" /> : <ChevronRight className="w-5 h-5 text-primary-600" />}
    </div>
    {isExpanded && (
      <div className="px-4 pb-4 relative z-10">
        {children}
      </div>
    )}
  </div>
);

const MetricCard = ({ label, value }) => (
  <div className="bg-gradient-to-br from-white to-primary-50 border border-primary-200 rounded-xl p-4 shadow-md hover:shadow-lg transition-all">
    <div className="text-sm text-secondary-600 mb-1 font-medium">{label}</div>
    <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-secondary-600">{value}</div>
  </div>
);

export default ResultsViewer;
