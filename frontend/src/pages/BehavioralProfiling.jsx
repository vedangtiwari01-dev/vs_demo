import React, { useState, useEffect } from 'react';
import { Users, TrendingUp } from 'lucide-react';
import Card from '../components/common/Card';
import Loading from '../components/common/Loading';
import { behavioralAPI } from '../api/deviation.api';
import toast from 'react-hot-toast';

const BehavioralProfiling = () => {
  const [riskMatrix, setRiskMatrix] = useState([]);
  const [patterns, setPatterns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [riskResponse, patternsResponse] = await Promise.all([
        behavioralAPI.getRiskMatrix(),
        behavioralAPI.getPatterns(),
      ]);
      setRiskMatrix(riskResponse.data || []);
      setPatterns(patternsResponse.data || []);
    } catch (error) {
      toast.error('Failed to load behavioral data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading message="Loading behavioral profiles..." />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Behavioral Profiling</h1>
        <p className="mt-1 text-gray-600">Analyze officer behavior patterns and risk indicators</p>
      </div>

      <Card title="Officer Risk Matrix">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Officer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Role
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Total Deviations
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Critical
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  High
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Risk Score
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {riskMatrix.map((officer, index) => (
                <tr key={index} className={officer.risk_score > 50 ? 'bg-red-50' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{officer.officer_name}</div>
                    <div className="text-sm text-gray-500">{officer.officer_id}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {officer.role}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                    {officer.total_deviations}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className="badge badge-critical">{officer.critical}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className="badge badge-high">{officer.high}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <div
                      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        officer.risk_score > 50
                          ? 'bg-red-100 text-red-800'
                          : officer.risk_score > 25
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}
                    >
                      {officer.risk_score}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {riskMatrix.length === 0 && (
            <p className="text-center text-gray-500 py-8">No risk data available</p>
          )}
        </div>
      </Card>

      <Card title="Detected Behavioral Patterns">
        <div className="space-y-4">
          {patterns.map((pattern, index) => (
            <div key={index} className="border-l-4 border-primary-500 pl-4 py-3">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-semibold text-gray-900">{pattern.description}</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Type: {pattern.pattern_type.replace('_', ' ')}
                  </p>
                  {pattern.Officer && (
                    <p className="text-sm text-gray-600">
                      Officer: {pattern.Officer.name}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">
                    Confidence: {(pattern.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
          {patterns.length === 0 && (
            <p className="text-center text-gray-500 py-8">
              No behavioral patterns detected yet
            </p>
          )}
        </div>
      </Card>
    </div>
  );
};

export default BehavioralProfiling;
