import React, { useState } from 'react';
import { Upload, Play } from 'lucide-react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import FileUpload from '../components/common/FileUpload';
import { workflowAPI } from '../api/workflow.api';
import toast from 'react-hot-toast';

const WorkflowAnalysis = () => {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);

  const handleUpload = async () => {
    if (!uploadedFile) {
      toast.error('Please select a file');
      return;
    }

    try {
      const response = await workflowAPI.upload(uploadedFile);
      toast.success(`Uploaded ${response.data.total_logs} workflow logs`);
      setUploadedFile(null);
    } catch (error) {
      toast.error('Failed to upload workflow logs');
    }
  };

  const handleAnalyze = async () => {
    try {
      setAnalyzing(true);
      const response = await workflowAPI.analyze();
      setResult(response.data);
      toast.success(`Found ${response.data.total_deviations} deviations`);
    } catch (error) {
      toast.error(error.response?.data?.message || 'Failed to analyze workflow');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Workflow Analysis</h1>
        <p className="mt-1 text-gray-600">Upload workflow logs and detect deviations from SOP</p>
      </div>

      <Card title="Upload Workflow Logs">
        <FileUpload
          onFileSelect={setUploadedFile}
          accept=".csv,.json"
        />
        <Button onClick={handleUpload} className="mt-4" disabled={!uploadedFile}>
          <Upload className="h-4 w-4 mr-2" />
          Upload Logs
        </Button>
      </Card>

      <Card title="Analyze Workflow">
        <p className="text-gray-600 mb-4">
          Analyze uploaded workflow logs against SOP rules to detect deviations
        </p>
        <Button onClick={handleAnalyze} disabled={analyzing}>
          {analyzing ? (
            <>Processing...</>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" />
              Analyze Workflow
            </>
          )}
        </Button>
      </Card>

      {result && (
        <Card title="Analysis Results">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Total Deviations</p>
              <p className="text-2xl font-bold text-gray-900">{result.total_deviations}</p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Critical</p>
              <p className="text-2xl font-bold text-red-600">{result.summary?.critical || 0}</p>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">High</p>
              <p className="text-2xl font-bold text-orange-600">{result.summary?.high || 0}</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Medium</p>
              <p className="text-2xl font-bold text-yellow-600">{result.summary?.medium || 0}</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default WorkflowAnalysis;
