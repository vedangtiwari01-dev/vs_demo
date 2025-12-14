import React, { useState } from 'react';
import { Zap, Play, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import { stressTestAPI } from '../api/deviation.api';
import { SCENARIO_TYPES } from '../utils/constants';
import toast from 'react-hot-toast';

const StressTesting = () => {
  const navigate = useNavigate();
  const [scenario, setScenario] = useState({
    scenario_type: 'officer_shortage',
    parameters: {
      normal_officers: 10,
      reduced_officers: 6,
      total_cases: 100,
      days: 30,
    },
  });
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState(null);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      const response = await stressTestAPI.generateLogs(scenario);
      setResult(response.data);
      toast.success(`✓ Generated ${response.data.total_logs} synthetic logs and added to analysis queue!`);
    } catch (error) {
      toast.error('Failed to generate synthetic logs');
    } finally {
      setGenerating(false);
    }
  };

  const handleGoToAnalysis = () => {
    navigate('/');
    toast.success('Navigate to Analysis Hub to select and analyze the generated logs');
  };

  const updateParameter = (key, value) => {
    setScenario({
      ...scenario,
      parameters: { ...scenario.parameters, [key]: parseInt(value) || 0 },
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Stress Testing</h1>
        <p className="mt-1 text-gray-600">Generate synthetic workflow logs under extreme scenarios</p>
      </div>

      <Card title="Configure Stress Test Scenario">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Scenario Type
            </label>
            <select
              className="input"
              value={scenario.scenario_type}
              onChange={(e) =>
                setScenario({ ...scenario, scenario_type: e.target.value })
              }
            >
              {Object.entries(SCENARIO_TYPES).map(([key, value]) => (
                <option key={key} value={key}>
                  {value}
                </option>
              ))}
            </select>
          </div>

          {scenario.scenario_type === 'officer_shortage' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Normal Officers
                  </label>
                  <input
                    type="number"
                    className="input"
                    value={scenario.parameters.normal_officers}
                    onChange={(e) => updateParameter('normal_officers', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reduced Officers
                  </label>
                  <input
                    type="number"
                    className="input"
                    value={scenario.parameters.reduced_officers}
                    onChange={(e) => updateParameter('reduced_officers', e.target.value)}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Total Cases
                  </label>
                  <input
                    type="number"
                    className="input"
                    value={scenario.parameters.total_cases}
                    onChange={(e) => updateParameter('total_cases', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Days
                  </label>
                  <input
                    type="number"
                    className="input"
                    value={scenario.parameters.days}
                    onChange={(e) => updateParameter('days', e.target.value)}
                  />
                </div>
              </div>
            </>
          )}

          <Button onClick={handleGenerate} disabled={generating}>
            {generating ? (
              <>Generating...</>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Generate Synthetic Logs
              </>
            )}
          </Button>
        </div>
      </Card>

      {result && (
        <Card title="✅ Stress Test Results">
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Total Logs Generated</p>
              <p className="text-2xl font-bold text-gray-900">{result.total_logs}</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Unique Cases</p>
              <p className="text-2xl font-bold text-blue-600">{result.unique_cases}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Unique Officers</p>
              <p className="text-2xl font-bold text-green-600">{result.unique_officers}</p>
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
            <div className="flex items-start space-x-2">
              <div className="flex-shrink-0 mt-0.5">
                <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-green-800 mb-1">Logs Added to Analysis Queue!</h4>
                <p className="text-sm text-green-700">
                  Synthetic logs have been generated and added to your workflow queue. You can now select them in the Analysis Hub to run compliance analysis.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <Button onClick={handleGoToAnalysis} className="flex items-center space-x-2">
              <ArrowRight className="h-4 w-4" />
              <span>Go to Analysis Hub</span>
            </Button>
            <Button onClick={handleGenerate} disabled={generating} variant="secondary">
              {generating ? 'Generating...' : 'Generate More Logs'}
            </Button>
          </div>

          <p className="mt-4 text-xs text-gray-500">
            💡 Tip: Generated logs will appear with a "Generated" badge in the workflow list
          </p>
        </Card>
      )}
    </div>
  );
};

export default StressTesting;
