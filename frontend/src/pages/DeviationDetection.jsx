import React, { useState, useEffect } from 'react';
import { Search, Filter } from 'lucide-react';
import Card from '../components/common/Card';
import Loading from '../components/common/Loading';
import { deviationAPI } from '../api/deviation.api';
import { DEVIATION_TYPES } from '../utils/constants';
import toast from 'react-hot-toast';

const DeviationDetection = () => {
  const [deviations, setDeviations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    severity: '',
    deviation_type: '',
  });

  useEffect(() => {
    loadDeviations();
  }, [filters]);

  const loadDeviations = async () => {
    try {
      setLoading(true);
      const response = await deviationAPI.list(filters);
      setDeviations(response.data.deviations || []);
    } catch (error) {
      toast.error('Failed to load deviations');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Deviation Detection</h1>
        <p className="mt-1 text-gray-600">View and analyze detected compliance deviations</p>
      </div>

      <Card>
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
            <select
              className="input"
              value={filters.severity}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select
              className="input"
              value={filters.deviation_type}
              onChange={(e) => setFilters({ ...filters, deviation_type: e.target.value })}
            >
              <option value="">All Types</option>
              {Object.entries(DEVIATION_TYPES).map(([key, value]) => (
                <option key={key} value={key}>
                  {value}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {loading ? (
        <Loading message="Loading deviations..." />
      ) : (
        <div className="space-y-4">
          {deviations.map((deviation) => (
            <Card key={deviation.id}>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`badge badge-${deviation.severity}`}>
                      {deviation.severity}
                    </span>
                    <span className="text-sm text-gray-600">
                      {DEVIATION_TYPES[deviation.deviation_type] || deviation.deviation_type}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">{deviation.description}</h3>
                  <p className="text-sm text-gray-600 mt-2">
                    <span className="font-medium">Case:</span> {deviation.case_id}
                    <span className="mx-2">|</span>
                    <span className="font-medium">Officer:</span>{' '}
                    {deviation.Officer?.name || deviation.officer_id}
                  </p>
                  {deviation.expected_behavior && (
                    <div className="mt-3 p-3 bg-gray-50 rounded">
                      <p className="text-sm">
                        <span className="font-medium">Expected:</span> {deviation.expected_behavior}
                      </p>
                      <p className="text-sm mt-1">
                        <span className="font-medium">Actual:</span> {deviation.actual_behavior}
                      </p>
                    </div>
                  )}
                </div>
                <div className="text-sm text-gray-500">
                  {new Date(deviation.detected_at).toLocaleDateString()}
                </div>
              </div>
            </Card>
          ))}
          {deviations.length === 0 && (
            <Card>
              <p className="text-center text-gray-500 py-8">
                No deviations found. Upload workflow logs and run analysis to detect deviations.
              </p>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default DeviationDetection;
