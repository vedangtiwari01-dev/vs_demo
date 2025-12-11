import React, { useState } from 'react';
import { Zap, Play } from 'lucide-react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import { stressTestAPI } from '../api/deviation.api';
import { SCENARIO_TYPES } from '../utils/constants';
import toast from 'react-hot-toast';

const StressTesting = () => {
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
      toast.success(`Generated ${response.data.total_logs} synthetic logs`);
    } catch (error) {
      toast.error('Failed to generate synthetic logs');
    } finally {
      setGenerating(false);
    }
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
        <Card title="Stress Test Results">
          <div className="grid grid-cols-3 gap-4">
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
          <p className="mt-4 text-sm text-gray-600">
            Synthetic logs have been generated and saved to the database. Run workflow analysis to
            detect deviations in the generated logs.
          </p>
        </Card>
      )}
    </div>
  );
};

export default StressTesting;
