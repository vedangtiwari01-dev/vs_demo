import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, FileText, Users, CheckCircle } from 'lucide-react';
import Card from '../components/common/Card';
import Loading from '../components/common/Loading';
import { analyticsAPI } from '../api/deviation.api';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await analyticsAPI.getDashboard();
      setData(response.data);
    } catch (error) {
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading message="Loading dashboard..." />;
  if (!data) return <div>No data available</div>;

  const stats = [
    {
      label: 'Total Cases',
      value: data.summary?.total_cases || 0,
      icon: FileText,
      color: 'bg-blue-100 text-blue-600',
    },
    {
      label: 'Total Deviations',
      value: data.summary?.total_deviations || 0,
      icon: AlertTriangle,
      color: 'bg-red-100 text-red-600',
    },
    {
      label: 'Total Officers',
      value: data.summary?.total_officers || 0,
      icon: Users,
      color: 'bg-green-100 text-green-600',
    },
    {
      label: 'Compliance Rate',
      value: `${(100 - (data.summary?.deviation_rate || 0)).toFixed(1)}%`,
      icon: CheckCircle,
      color: 'bg-purple-100 text-purple-600',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-gray-600">Overview of loan processing compliance metrics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index}>
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <Icon className="h-6 w-6" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                  <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Recent Deviations">
          <div className="space-y-3">
            {data.recent_deviations?.slice(0, 5).map((deviation) => (
              <div key={deviation.id} className="border-l-4 border-red-500 pl-4 py-2">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">{deviation.description}</p>
                    <p className="text-sm text-gray-600">
                      Officer: {deviation.Officer?.name || deviation.officer_id}
                    </p>
                  </div>
                  <span className={`badge badge-${deviation.severity}`}>
                    {deviation.severity}
                  </span>
                </div>
              </div>
            ))}
            {(!data.recent_deviations || data.recent_deviations.length === 0) && (
              <p className="text-gray-500 text-center py-4">No deviations found</p>
            )}
          </div>
          <Link
            to="/deviations"
            className="mt-4 text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            View all deviations →
          </Link>
        </Card>

        <Card title="High-Risk Officers">
          <div className="space-y-3">
            {data.high_risk_officers?.slice(0, 5).map((officer, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{officer.Officer?.name || officer.officer_id}</p>
                  <p className="text-sm text-gray-600">{officer.Officer?.role}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-semibold text-red-600">{officer.deviation_count}</p>
                  <p className="text-xs text-gray-500">deviations</p>
                </div>
              </div>
            ))}
            {(!data.high_risk_officers || data.high_risk_officers.length === 0) && (
              <p className="text-gray-500 text-center py-4">No data available</p>
            )}
          </div>
          <Link
            to="/behavioral"
            className="mt-4 text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            View behavioral profiles →
          </Link>
        </Card>
      </div>

      <Card title="Quick Actions">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/sop"
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors text-center"
          >
            <FileText className="mx-auto h-8 w-8 text-gray-400" />
            <p className="mt-2 font-medium text-gray-900">Upload SOP</p>
          </Link>
          <Link
            to="/workflow"
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors text-center"
          >
            <AlertTriangle className="mx-auto h-8 w-8 text-gray-400" />
            <p className="mt-2 font-medium text-gray-900">Upload Logs</p>
          </Link>
          <Link
            to="/stress-test"
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-colors text-center"
          >
            <Users className="mx-auto h-8 w-8 text-gray-400" />
            <p className="mt-2 font-medium text-gray-900">Run Stress Test</p>
          </Link>
        </div>
      </Card>
    </div>
  );
};

export default Dashboard;
