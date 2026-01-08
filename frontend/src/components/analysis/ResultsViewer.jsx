import { useState } from 'react';
import { Loader, Download, RefreshCw } from 'lucide-react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, RadialBarChart, RadialBar,
  LineChart, Line, Area, AreaChart, ScatterChart, Scatter, ZAxis
} from 'recharts';

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

  // Extract data from analysisResult
  const data = analysisResult.data || analysisResult;
  const deviations = data.deviations || [];
  const summary = data.summary || {};
  const patterns = data || {};

  // Tab definitions
  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'trends', label: 'Trends', icon: '📈' },
    { id: 'officers', label: 'Officers', icon: '👥' },
    { id: 'deepdive', label: 'Deep Dive', icon: '🔍' },
    { id: 'statistics', label: 'Statistics', icon: '📉' },
  ];

  return (
    <div className="bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50 min-h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm shadow-2xl border-b border-primary-200 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-primary-400/20 to-transparent rounded-full blur-3xl"></div>
        <div className="p-6 relative z-10">
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
            {analysisResult.workflow?.filename || 'Workflow'} vs {analysisResult.sop?.title || 'SOP'}
          </p>
          <p className="text-xs text-secondary-600 mt-1">
            Analyzed: {new Date(analysisResult.timestamp || Date.now()).toLocaleString()}
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 pb-0 relative z-10">
          <div className="flex space-x-1 border-b border-primary-200">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 text-sm font-semibold transition-all relative ${
                  activeTab === tab.id
                    ? 'text-primary-600 bg-gradient-to-t from-primary-50 to-white'
                    : 'text-secondary-600 hover:text-secondary-800 hover:bg-white/50'
                }`}
              >
                <span className="flex items-center space-x-2">
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </span>
                {activeTab === tab.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-600 to-secondary-600"></div>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && <OverviewTab data={data} summary={summary} deviations={deviations} patterns={patterns} />}
        {activeTab === 'trends' && <TrendsTab data={data} patterns={patterns} />}
        {activeTab === 'officers' && <OfficersTab data={data} patterns={patterns} />}
        {activeTab === 'deepdive' && <DeepDiveTab data={data} deviations={deviations} patterns={patterns} />}
        {activeTab === 'statistics' && <StatisticsTab data={data} patterns={patterns} />}
      </div>
    </div>
  );
};

// ============================================================================
// TAB 1: OVERVIEW DASHBOARD
// ============================================================================
const OverviewTab = ({ data, summary, deviations, patterns }) => {
  const totalDeviations = data.total_deviations || summary.total_deviations || 0;
  const severityDist = summary.severity_distribution || {};
  const critical = severityDist.critical || 0;
  const high = severityDist.high || 0;
  const medium = severityDist.medium || 0;
  const low = severityDist.low || 0;

  return (
    <div className="space-y-6">
      {/* Row 1: Key Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          label="Total Deviations"
          value={totalDeviations}
          gradient="from-red-500 to-orange-500"
        />
        <MetricCard
          label="Critical"
          value={`${critical} (${totalDeviations > 0 ? Math.round((critical / totalDeviations) * 100) : 0}%)`}
          gradient="from-red-600 to-red-700"
        />
        <MetricCard
          label="High Severity"
          value={`${high} (${totalDeviations > 0 ? Math.round((high / totalDeviations) * 100) : 0}%)`}
          gradient="from-orange-500 to-orange-600"
        />
        <MetricCard
          label="Officers"
          value={summary.total_officers || data.statistical_summary?.officer_statistics?.total_officers || 0}
          gradient="from-blue-500 to-cyan-500"
        />
      </div>

      {/* Row 2: Charts - Severity Breakdown and Top Types */}
      <div className="grid grid-cols-2 gap-4">
        {/* Severity Pie Chart */}
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">Severity Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Critical', value: critical, color: '#ef4444' },
                  { name: 'High', value: high, color: '#f97316' },
                  { name: 'Medium', value: medium, color: '#fbbf24' },
                  { name: 'Low', value: low, color: '#10b981' }
                ].filter(item => item.value > 0)}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {[
                  { name: 'Critical', value: critical, color: '#ef4444' },
                  { name: 'High', value: high, color: '#f97316' },
                  { name: 'Medium', value: medium, color: '#fbbf24' },
                  { name: 'Low', value: low, color: '#10b981' }
                ].filter(item => item.value > 0).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Deviation Types Bar Chart */}
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">Top 10 Deviation Types</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={(data.statistical_summary?.top_deviation_types || []).slice(0, 10).map(item => ({
                name: (item.type || '').replace(/_/g, ' '),
                count: item.count || 0,
                percentage: item.percentage || 0
              }))}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="name" width={90} style={{ fontSize: '11px' }} />
              <Tooltip />
              <Bar dataKey="count" fill="#0891b2" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 3: Severity Gauge */}
      {data.statistical_summary?.severity_score !== undefined && (
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">Severity Score Gauge</h3>
          <ResponsiveContainer width="100%" height={250}>
            <RadialBarChart
              cx="50%"
              cy="50%"
              innerRadius="60%"
              outerRadius="90%"
              barSize={20}
              data={[{
                name: 'Severity',
                value: data.statistical_summary.severity_score,
                fill: data.statistical_summary.severity_score > 75 ? '#ef4444' :
                      data.statistical_summary.severity_score > 50 ? '#f97316' :
                      data.statistical_summary.severity_score > 25 ? '#fbbf24' : '#10b981'
              }]}
              startAngle={180}
              endAngle={0}
            >
              <RadialBar
                minAngle={15}
                label={{ position: 'insideStart', fill: '#fff', fontSize: 20 }}
                background
                clockWise
                dataKey="value"
              />
              <Legend iconSize={10} layout="vertical" verticalAlign="bottom" />
              <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="text-3xl font-bold" fill="#1f2937">
                {data.statistical_summary.severity_score}/100
              </text>
            </RadialBarChart>
          </ResponsiveContainer>
          {data.statistical_summary.severity_assessment && (
            <p className="text-center text-sm text-gray-600 mt-2">{data.statistical_summary.severity_assessment}</p>
          )}
        </div>
      )}

      {/* Row 4: Risk Summary */}
      {patterns.overall_summary && (
        <div className="bg-gradient-to-br from-red-50 to-orange-50 border-2 border-red-200 rounded-xl shadow-lg p-6">
          <h3 className="font-bold text-red-800 mb-2 flex items-center space-x-2">
            <span>🔴</span>
            <span>Risk Assessment</span>
          </h3>
          <p className="text-sm text-gray-700 mb-4">{patterns.overall_summary}</p>
          {data.statistical_summary?.severity_assessment && (
            <div className="mt-3 p-3 bg-white/60 rounded border border-red-200">
              <p className="text-sm font-semibold text-red-900">
                Severity Score: {data.statistical_summary.severity_score}/100
              </p>
              <p className="text-xs text-gray-600 mt-1">{data.statistical_summary.severity_assessment}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// TAB 2: TRENDS & PATTERNS
// ============================================================================
const TrendsTab = ({ data, patterns }) => {
  const timeSeries = data.statistical_summary?.time_series;
  const temporal = data.statistical_summary?.temporal_patterns;
  const timePatterns = patterns.time_patterns || [];

  return (
    <div className="space-y-6">
      {/* Time Series Data */}
      {timeSeries?.available && timeSeries.daily_counts?.dates && (
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">📈 Time Series Analysis</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart
              data={timeSeries.daily_counts.dates.map((date, idx) => ({
                date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                count: timeSeries.daily_counts.counts[idx],
                ma7: timeSeries.moving_averages?.['7_day']?.[idx]
              }))}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0891b2" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#0891b2" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" style={{ fontSize: '11px' }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="count" stroke="#0891b2" fillOpacity={1} fill="url(#colorCount)" name="Daily Count" />
              {timeSeries.moving_averages?.['7_day'] && (
                <Line type="monotone" dataKey="ma7" stroke="#f97316" strokeWidth={2} dot={false} name="7-Day MA" />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Temporal Patterns */}
      {temporal?.has_temporal_data && (
        <div className="grid grid-cols-2 gap-4">
          {/* Hour Distribution Bar Chart */}
          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
            <h3 className="font-bold text-secondary-800 mb-4">Hour Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={Object.entries(temporal.hour_distribution || {})
                  .sort(([a], [b]) => parseInt(a) - parseInt(b))
                  .map(([hour, count]) => ({
                    hour: `${hour}:00`,
                    count
                  }))}
                margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" style={{ fontSize: '10px' }} angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#0891b2" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Day Distribution Bar Chart */}
          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
            <h3 className="font-bold text-secondary-800 mb-4">Day Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={Object.entries(temporal.day_distribution || {}).map(([day, count]) => ({
                  day,
                  count
                }))}
                margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" style={{ fontSize: '11px' }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#f97316" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* AI Time Patterns */}
      {timePatterns.length > 0 && (
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">🕐 AI-Detected Time Patterns</h3>
          <div className="space-y-3">
            {timePatterns.map((pattern, idx) => (
              <div key={idx} className="p-4 bg-blue-50 border border-blue-200 rounded">
                <p className="text-sm font-medium text-gray-800">{pattern.pattern || pattern}</p>
                {pattern.supporting_evidence && (
                  <p className="text-xs text-gray-600 mt-2">{pattern.supporting_evidence}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// TAB 3: OFFICERS ANALYSIS
// ============================================================================
const OfficersTab = ({ data, patterns }) => {
  const officerStats = data.statistical_summary?.officer_statistics;
  const topOfficers = officerStats?.top_officers || officerStats?.top_20_officers || [];

  return (
    <div className="space-y-6">
      {/* Top Officers Charts */}
      <div className="grid grid-cols-2 gap-4">
        {/* Stacked Bar Chart - Officer Rankings */}
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">👥 Top 15 Officers (by Severity)</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={topOfficers.slice(0, 15).map(officer => ({
                id: officer.officer_id,
                critical: officer.severity_breakdown?.critical || 0,
                high: officer.severity_breakdown?.high || 0,
                medium: officer.severity_breakdown?.medium || 0,
                low: officer.severity_breakdown?.low || 0
              }))}
              layout="horizontal"
              margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="category" dataKey="id" style={{ fontSize: '10px' }} angle={-45} textAnchor="end" height={100} />
              <YAxis type="number" />
              <Tooltip />
              <Legend />
              <Bar dataKey="critical" stackId="a" fill="#ef4444" name="Critical" />
              <Bar dataKey="high" stackId="a" fill="#f97316" name="High" />
              <Bar dataKey="medium" stackId="a" fill="#fbbf24" name="Medium" />
              <Bar dataKey="low" stackId="a" fill="#10b981" name="Low" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Scatter Plot - Officer Risk Profile */}
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">Officer Risk Scatter Plot</h3>
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid />
              <XAxis type="number" dataKey="total" name="Total Deviations" label={{ value: 'Total Deviations', position: 'insideBottom', offset: -10 }} />
              <YAxis type="number" dataKey="critical" name="Critical Count" label={{ value: 'Critical Count', angle: -90, position: 'insideLeft' }} />
              <ZAxis type="number" range={[100, 400]} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} content={({ payload }) => {
                if (payload && payload.length > 0) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-3 border border-gray-300 rounded shadow-lg text-xs">
                      <p className="font-bold">{data.id}</p>
                      <p>Total: {data.total}</p>
                      <p>Critical: {data.critical}</p>
                    </div>
                  );
                }
                return null;
              }} />
              <Legend />
              <Scatter
                name="Officers"
                data={topOfficers.slice(0, 20).map(officer => ({
                  id: officer.officer_id,
                  total: officer.total_deviations,
                  critical: officer.severity_breakdown?.critical || 0
                }))}
                fill="#ef4444"
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Officer Details Table */}
      <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
        <h3 className="font-bold text-secondary-800 mb-4">Officer Details Table</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-100 border-b-2 border-gray-300">
              <tr>
                <th className="px-3 py-2 text-left font-semibold text-gray-700">Officer ID</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Total</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Critical</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">High</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Medium</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">Low</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {topOfficers.slice(0, 15).map((officer, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-3 py-2 font-medium text-gray-800">{officer.officer_id}</td>
                  <td className="px-3 py-2 text-center font-bold">{officer.total_deviations}</td>
                  <td className="px-3 py-2 text-center text-red-700">{officer.severity_breakdown?.critical || 0}</td>
                  <td className="px-3 py-2 text-center text-orange-700">{officer.severity_breakdown?.high || 0}</td>
                  <td className="px-3 py-2 text-center text-yellow-700">{officer.severity_breakdown?.medium || 0}</td>
                  <td className="px-3 py-2 text-center text-green-700">{officer.severity_breakdown?.low || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Behavioral Patterns for Officers */}
      {patterns.behavioral_patterns && patterns.behavioral_patterns.length > 0 && (
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">👤 Behavioral Patterns</h3>
          <div className="space-y-4">
            {patterns.behavioral_patterns.map((pattern, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-gray-800">{pattern.pattern}</h4>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    pattern.risk_level === 'critical' ? 'bg-red-100 text-red-700' :
                    pattern.risk_level === 'high' ? 'bg-orange-100 text-orange-700' :
                    pattern.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    Risk: {pattern.risk_level?.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{pattern.supporting_evidence}</p>
                <div className="text-xs text-gray-500">Frequency: {pattern.frequency}</div>
                {pattern.officers_involved && pattern.officers_involved.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {pattern.officers_involved.map((officer, oidx) => (
                      <span key={oidx} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                        {officer}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// TAB 4: DEEP DIVE
// ============================================================================
const DeepDiveTab = ({ data, deviations, patterns }) => {
  const [showAllDeviations, setShowAllDeviations] = useState(false);

  return (
    <div className="space-y-6">
      {/* AI Insights */}
      {patterns.hidden_rules && patterns.hidden_rules.length > 0 && (
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">🎯 Hidden Rules Discovered</h3>
          <div className="space-y-3">
            {patterns.hidden_rules.map((rule, idx) => (
              <div key={idx} className="border-l-4 border-yellow-400 bg-yellow-50 p-4 rounded">
                <h4 className="font-medium text-gray-800 mb-1">{rule.rule}</h4>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Confidence: <span className="font-medium">{rule.confidence}</span></div>
                  <div className="text-xs">{rule.evidence}</div>
                  <div className="text-xs text-red-600 mt-2">
                    <strong>Impact:</strong> {rule.compliance_impact}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {patterns.systemic_issues && patterns.systemic_issues.length > 0 && (
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">⚙️ Systemic Issues</h3>
          <div className="space-y-3">
            {patterns.systemic_issues.map((issue, idx) => (
              <div key={idx} className="border-l-4 border-red-400 bg-red-50 p-4 rounded">
                <h4 className="font-medium text-gray-800 mb-1">{issue.issue}</h4>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Frequency: <span className="font-medium">{issue.frequency}</span></div>
                  <div>Impact: <span className="text-red-700">{issue.impact}</span></div>
                  {issue.recommended_fix && (
                    <div className="mt-2 p-2 bg-white rounded text-xs">
                      <strong>Recommended Fix:</strong> {issue.recommended_fix}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {patterns.recommendations && patterns.recommendations.length > 0 && (
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">💡 Recommendations</h3>
          <div className="space-y-2">
            {patterns.recommendations.map((rec, idx) => (
              <div key={idx} className="flex items-start space-x-2 p-3 bg-blue-50 border border-blue-200 rounded">
                <span className="text-blue-600 font-bold">{idx + 1}.</span>
                <span className="text-sm text-gray-700">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Deviations Table */}
      <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-secondary-800">📋 All Deviations</h3>
          <button
            onClick={() => setShowAllDeviations(!showAllDeviations)}
            className="px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors"
          >
            {showAllDeviations ? 'Hide Table' : 'Show Table'}
          </button>
        </div>

        {showAllDeviations && (
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
                        {dev.deviation_type?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-1 text-xs rounded font-medium ${
                        dev.severity === 'critical' ? 'bg-red-100 text-red-700' :
                        dev.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                        dev.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {dev.severity?.toUpperCase()}
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
        )}
      </div>
    </div>
  );
};

// ============================================================================
// TAB 5: STATISTICS
// ============================================================================
const StatisticsTab = ({ data, patterns }) => {
  const stats = data.statistical_summary || {};
  const mlSummary = data.ml_summary;
  const advancedCorr = stats.advanced_correlations;
  const controlCharts = stats.control_charts;

  return (
    <div className="space-y-6">
      {/* ML Summary */}
      {mlSummary?.ml_applied && (
        <div className="grid grid-cols-4 gap-4">
          <StatCard label="Clustering Method" value={mlSummary.clustering_method} />
          <StatCard label="Clusters Found" value={mlSummary.clusters_found} />
          <StatCard label="Anomalies Detected" value={mlSummary.anomalies_detected} />
          <StatCard label="Compression Ratio" value={`${mlSummary.compression_ratio?.toFixed(2)}x`} />
        </div>
      )}

      {/* Advanced Correlations */}
      {advancedCorr?.available && (
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">📊 Statistical Correlations</h3>

          {advancedCorr.cramers_v && (
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Cramér's V Association Heatmap</h4>
              <div className="grid grid-cols-1 gap-2">
                {Object.entries(advancedCorr.cramers_v).map(([key, val]) => {
                  const value = val.value || 0;
                  const colorIntensity = Math.min(value * 100, 100);
                  const bgColor = value > 0.7 ? '#ef4444' : // Strong - Red
                                  value > 0.4 ? '#f97316' : // Moderate - Orange
                                  value > 0.2 ? '#fbbf24' : // Weak - Yellow
                                  '#10b981'; // Very weak - Green

                  return (
                    <div key={key} className="flex items-center rounded overflow-hidden border border-gray-200">
                      <div className="flex-1 p-3 bg-gray-50">
                        <span className="text-sm text-gray-700 capitalize font-medium">{key.replace(/_/g, ' ')}</span>
                      </div>
                      <div
                        className="w-32 p-3 text-center transition-all"
                        style={{ backgroundColor: bgColor, opacity: 0.3 + (colorIntensity / 100) * 0.7 }}
                      >
                        <div className="text-sm font-bold text-gray-900">{value.toFixed(3)}</div>
                      </div>
                      <div className="w-40 p-3 bg-white">
                        <div className="text-xs text-gray-600">{val.interpretation}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 flex items-center justify-center space-x-4 text-xs text-gray-600">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10b981', opacity: 0.6 }}></div>
                  <span>Weak (&lt;0.2)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#fbbf24', opacity: 0.7 }}></div>
                  <span>Moderate (0.2-0.4)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f97316', opacity: 0.8 }}></div>
                  <span>Strong (0.4-0.7)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded" style={{ backgroundColor: '#ef4444', opacity: 0.9 }}></div>
                  <span>Very Strong (&gt;0.7)</span>
                </div>
              </div>
            </div>
          )}

          {advancedCorr.chi_square_tests && (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Chi-Square Tests</h4>
              <div className="text-sm text-gray-600 p-3 bg-blue-50 rounded">
                Chi-square test results available for correlation analysis
              </div>
            </div>
          )}
        </div>
      )}

      {/* Control Charts with Visualization */}
      {controlCharts?.available && controlCharts.shewhart && (
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">📉 Control Charts (SPC)</h3>

          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="p-4 bg-gray-50 rounded text-center">
              <div className="text-xs text-gray-600 mb-1">Mean (μ)</div>
              <div className="text-2xl font-bold text-gray-800">{controlCharts.shewhart.mean?.toFixed(2)}</div>
            </div>
            <div className="p-4 bg-gray-50 rounded text-center">
              <div className="text-xs text-gray-600 mb-1">Std Dev (σ)</div>
              <div className="text-2xl font-bold text-gray-800">{controlCharts.shewhart.std?.toFixed(2)}</div>
            </div>
            <div className="p-4 bg-blue-50 rounded text-center">
              <div className="text-xs text-gray-600 mb-1">UCL (μ + 3σ)</div>
              <div className="text-2xl font-bold text-blue-700">{controlCharts.shewhart.ucl?.toFixed(2)}</div>
            </div>
            <div className="p-4 bg-blue-50 rounded text-center">
              <div className="text-xs text-gray-600 mb-1">LCL (μ - 3σ)</div>
              <div className="text-2xl font-bold text-blue-700">{controlCharts.shewhart.lcl?.toFixed(2)}</div>
            </div>
          </div>

          {controlCharts.shewhart.out_of_control_points > 0 && (
            <div className="p-4 bg-red-50 border-2 border-red-200 rounded mb-4">
              <div className="text-sm font-semibold text-red-800">
                ⚠️ {controlCharts.shewhart.out_of_control_points} Out-of-Control Points Detected
              </div>
              <p className="text-xs text-gray-600 mt-1">
                Points outside control limits indicate process instability requiring investigation.
              </p>
            </div>
          )}

          {/* Visual representation */}
          <div className="bg-gray-50 p-4 rounded">
            <div className="h-48 relative">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={Array.from({ length: 10 }, (_, i) => ({
                    x: i + 1,
                    value: controlCharts.shewhart.mean,
                    ucl: controlCharts.shewhart.ucl,
                    lcl: controlCharts.shewhart.lcl
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="x" label={{ value: 'Sample', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Value', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="ucl" stroke="#3b82f6" strokeDasharray="5 5" name="UCL" dot={false} />
                  <Line type="monotone" dataKey="value" stroke="#10b981" strokeWidth={2} name="Mean" dot={false} />
                  <Line type="monotone" dataKey="lcl" stroke="#3b82f6" strokeDasharray="5 5" name="LCL" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Data Quality */}
      {data.data_quality && (
        <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-primary-200">
          <h3 className="font-bold text-secondary-800 mb-4">🔍 Data Quality Report</h3>
          <div className="text-sm text-gray-700 space-y-2">
            <pre className="bg-gray-50 p-4 rounded overflow-x-auto text-xs">
              {JSON.stringify(data.data_quality, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// HELPER COMPONENTS
// ============================================================================
const MetricCard = ({ label, value, gradient }) => (
  <div className="bg-white/80 backdrop-blur-sm border border-primary-200 rounded-xl p-4 shadow-md hover:shadow-lg transition-all">
    <div className="text-sm text-secondary-600 mb-1 font-medium">{label}</div>
    <div className={`text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r ${gradient || 'from-primary-600 to-secondary-600'}`}>
      {value}
    </div>
  </div>
);

const StatCard = ({ label, value }) => (
  <div className="bg-white/80 backdrop-blur-sm border border-primary-200 rounded-xl p-4 shadow-md">
    <div className="text-xs text-secondary-600 mb-1 font-medium">{label}</div>
    <div className="text-xl font-bold text-secondary-800">{value || 'N/A'}</div>
  </div>
);

const SeverityBar = ({ label, count, total, color }) => {
  const percentage = total > 0 ? (count / total) * 100 : 0;

  return (
    <div>
      <div className="flex items-center justify-between text-sm mb-1">
        <span className="font-medium text-gray-700">{label}</span>
        <span className="text-gray-600">{count} ({percentage.toFixed(1)}%)</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`${color} h-2 rounded-full transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};

export default ResultsViewer;
