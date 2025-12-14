import { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Trash2, Loader } from 'lucide-react';
import { toast } from 'react-hot-toast';
import FileUpload from '../common/FileUpload';
import { workflowAPI } from '../../api/workflow.api';
import axios from 'axios';
import { API_BASE_URL } from '../../utils/constants';

const WorkflowUploadWidget = ({ selectedWorkflow, onSelectWorkflow }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [workflowList, setWorkflowList] = useState([]);
  const [uploadProgress, setUploadProgress] = useState('');

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      // Get list of uploaded workflow files with metadata
      const response = await axios.get(`${API_BASE_URL}/workflows/list-files`);
      console.log('Workflows response:', response.data);

      // Backend wraps response in { success, message, data: { files: [...] } }
      const files = response.data.data?.files || response.data.files || [];
      console.log('Workflows loaded:', files);
      setWorkflowList(files);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    }
  };

  const handleFileSelect = async (file) => {
    setIsUploading(true);
    setUploadProgress('Analyzing CSV headers...');

    try {
      // Step 1: Analyze headers to get AI-generated column mappings
      const analyzeFormData = new FormData();
      analyzeFormData.append('logs', file);

      const analyzeResponse = await axios.post(`${API_BASE_URL}/workflows/analyze-headers`, analyzeFormData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      console.log('Analyze response:', analyzeResponse.data);

      // Extract mapping_suggestions from the response
      // Backend wraps response in { success, data, message }
      const responseData = analyzeResponse.data.data || analyzeResponse.data;
      const mappingSuggestions = responseData.mapping_suggestions;

      if (!mappingSuggestions) {
        throw new Error('No column mappings received from server');
      }

      console.log('Mapping suggestions:', mappingSuggestions);

      // Step 2: Upload file with the generated mappings
      setUploadProgress('Uploading workflow logs...');

      const uploadFormData = new FormData();
      uploadFormData.append('logs', file);
      uploadFormData.append('mapping', JSON.stringify(mappingSuggestions));

      const uploadResponse = await axios.post(`${API_BASE_URL}/workflows/upload-with-mapping`, uploadFormData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      console.log('Upload response:', uploadResponse.data);

      toast.success(`✓ ${file.name} uploaded and processed successfully!`);
      setIsCollapsed(true); // Auto-collapse after success
      setUploadProgress('');

      // Reload workflow list
      await loadWorkflows();
    } catch (error) {
      console.error('Workflow upload error:', error);
      console.error('Error details:', error.response?.data);
      const errorMsg = error.response?.data?.message || error.message;
      toast.error(`Failed to upload workflow: ${errorMsg}`);
      setUploadProgress('');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (workflowId, e) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this workflow log?')) {
      try {
        await axios.delete(`${API_BASE_URL}/workflows/${workflowId}`);
        await loadWorkflows();
        if (selectedWorkflow?.id === workflowId) {
          onSelectWorkflow(null);
        }
        toast.success('Workflow deleted successfully');
      } catch (error) {
        toast.error('Failed to delete workflow');
      }
    }
  };

  const handleSelectWorkflow = (workflow) => {
    onSelectWorkflow(workflow);
  };

  if (isCollapsed && selectedWorkflow) {
    return (
      <div className="mb-4 bg-gradient-to-br from-secondary-800 to-secondary-700 border border-primary-500/30 rounded-lg shadow-lg backdrop-blur-sm relative overflow-hidden">
        <div className="absolute top-0 left-0 w-24 h-24 bg-primary-500/10 rounded-full blur-2xl"></div>
        <div
          className="p-4 cursor-pointer hover:bg-secondary-700/50 transition-all relative z-10"
          onClick={() => setIsCollapsed(false)}
        >
          <div className="flex items-center justify-between">
            <span className="font-semibold text-cyan-300">Workflow Logs</span>
            <ChevronDown className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="mt-2 text-sm text-primary-200">
            ✓ {selectedWorkflow.filename}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4 bg-gradient-to-br from-secondary-800 to-secondary-700 border border-primary-500/30 rounded-lg shadow-lg backdrop-blur-sm relative overflow-hidden">
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-primary-500/10 rounded-full blur-2xl"></div>
      <div
        className="p-4 cursor-pointer hover:bg-secondary-700/50 flex items-center justify-between transition-all relative z-10"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <span className="font-semibold text-cyan-300">Workflow Logs</span>
        <ChevronUp className="w-5 h-5 text-cyan-400" />
      </div>

      <div className="px-4 pb-4 relative z-10">
        {/* Upload Area */}
        <FileUpload
          onFileSelect={handleFileSelect}
          accept=".csv,text/csv,application/csv"
          disabled={isUploading}
        />

        {/* Upload Progress */}
        {isUploading && (
          <div className="mt-3 p-3 bg-primary-900/40 border border-primary-400/50 rounded-lg backdrop-blur-sm">
            <div className="flex items-center space-x-2">
              <Loader className="w-4 h-4 text-primary-300 animate-spin" />
              <span className="text-sm text-primary-200">{uploadProgress}</span>
            </div>
          </div>
        )}

        {/* Workflow List */}
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-cyan-300 mb-3">Uploaded Logs</h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {workflowList.length === 0 ? (
              <p className="text-sm text-primary-300 italic">No workflow logs uploaded yet</p>
            ) : (
              workflowList.map((workflow) => (
                <div
                  key={workflow.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-all ${
                    selectedWorkflow?.id === workflow.id
                      ? 'border-primary-400 bg-gradient-to-r from-primary-900/60 to-secondary-800/60 shadow-lg'
                      : 'border-secondary-600 hover:border-primary-500/50 bg-secondary-800/40 hover:bg-secondary-700/60'
                  }`}
                  onClick={() => handleSelectWorkflow(workflow)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          checked={selectedWorkflow?.id === workflow.id}
                          onChange={() => handleSelectWorkflow(workflow)}
                          className="mt-0.5 accent-primary-500"
                        />
                        <span className="text-sm font-medium text-cyan-100">
                          {workflow.filename}
                        </span>
                        {workflow.is_generated && (
                          <span className="px-2 py-0.5 text-xs bg-purple-500/30 text-purple-200 rounded border border-purple-400/30">
                            Generated
                          </span>
                        )}
                      </div>
                      <div className="mt-1 ml-6 text-xs text-primary-300">
                        {new Date(workflow.uploaded_at).toLocaleDateString()}
                      </div>
                      <div className="mt-1 ml-6 text-xs text-primary-400">
                        {workflow.total_logs || 0} logs · {workflow.unique_cases || 0} cases
                      </div>
                    </div>
                    <button
                      onClick={(e) => handleDelete(workflow.id, e)}
                      className="p-1.5 hover:bg-red-500/20 rounded transition-colors"
                    >
                      <Trash2 className="w-4 h-4 text-red-400 hover:text-red-300" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowUploadWidget;
