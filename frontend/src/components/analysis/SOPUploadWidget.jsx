import { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Trash2, Loader } from 'lucide-react';
import { toast } from 'react-hot-toast';
import FileUpload from '../common/FileUpload';
import { sopAPI } from '../../api/sop.api';

const SOPUploadWidget = ({ selectedSop, onSelectSop }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [sopList, setSopList] = useState([]);
  const [uploadProgress, setUploadProgress] = useState('');

  useEffect(() => {
    loadSOPs();
  }, []);

  const loadSOPs = async () => {
    try {
      const response = await sopAPI.list();
      // Backend returns data directly as the array, not wrapped in 'sops'
      const sopsArray = Array.isArray(response.data) ? response.data : (response.data.sops || []);
      setSopList(sopsArray);
    } catch (error) {
      console.error('Failed to load SOPs:', error);
    }
  };

  const handleFileSelect = async (file) => {
    setIsUploading(true);
    setUploadProgress('Uploading...');

    try {
      // Step 1: Upload
      const title = file.name.replace(/\.[^/.]+$/, '');
      const uploadResponse = await sopAPI.upload(file, title, '1.0');
      const sopId = uploadResponse.data.id;  // Fixed: data is the SOP object directly

      // Step 2: Auto-process (parse + extract rules)
      setUploadProgress('Parsing document...');
      await sopAPI.process(sopId);

      setUploadProgress('Extracting rules...');
      // Rules are extracted during process, just fetch the updated SOP
      await loadSOPs();

      toast.success(`✓ ${file.name} processed successfully!`);
      setIsCollapsed(true); // Auto-collapse after success
      setUploadProgress('');
    } catch (error) {
      console.error('SOP upload error:', error);
      toast.error(`Failed to process SOP: ${error.response?.data?.message || error.message}`);
      setUploadProgress('');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (sopId, e) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this SOP?')) {
      try {
        await sopAPI.delete(sopId);
        await loadSOPs();
        if (selectedSop?.id === sopId) {
          onSelectSop(null);
        }
        toast.success('SOP deleted successfully');
      } catch (error) {
        toast.error('Failed to delete SOP');
      }
    }
  };

  const handleSelectSop = (sop) => {
    onSelectSop(sop);
  };

  if (isCollapsed && selectedSop) {
    return (
      <div className="mb-4 bg-gradient-to-br from-secondary-800 to-secondary-700 border border-primary-500/30 rounded-lg shadow-lg backdrop-blur-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-20 h-20 bg-primary-500/10 rounded-full blur-2xl"></div>
        <div
          className="p-4 cursor-pointer hover:bg-secondary-700/50 transition-all relative z-10"
          onClick={() => setIsCollapsed(false)}
        >
          <div className="flex items-center justify-between">
            <span className="font-semibold text-cyan-300">SOP Documents</span>
            <ChevronDown className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="mt-2 text-sm text-primary-200">
            ✓ {selectedSop.title}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4 bg-gradient-to-br from-secondary-800 to-secondary-700 border border-primary-500/30 rounded-lg shadow-lg backdrop-blur-sm relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-primary-500/10 rounded-full blur-2xl"></div>
      <div
        className="p-4 cursor-pointer hover:bg-secondary-700/50 flex items-center justify-between transition-all relative z-10"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <span className="font-semibold text-cyan-300">SOP Documents</span>
        <ChevronUp className="w-5 h-5 text-cyan-400" />
      </div>

      <div className="px-4 pb-4 relative z-10">
        {/* Upload Area */}
        <FileUpload
          onFileSelect={handleFileSelect}
          accept=".pdf,.docx,.txt"
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

        {/* SOP List */}
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-cyan-300 mb-3">Uploaded SOPs</h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {sopList.length === 0 ? (
              <p className="text-sm text-primary-300 italic">No SOPs uploaded yet</p>
            ) : (
              sopList.map((sop) => (
                <div
                  key={sop.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-all ${
                    selectedSop?.id === sop.id
                      ? 'border-primary-400 bg-gradient-to-r from-primary-900/60 to-secondary-800/60 shadow-lg'
                      : 'border-secondary-600 hover:border-primary-500/50 bg-secondary-800/40 hover:bg-secondary-700/60'
                  }`}
                  onClick={() => handleSelectSop(sop)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          checked={selectedSop?.id === sop.id}
                          onChange={() => handleSelectSop(sop)}
                          className="mt-0.5 accent-primary-500"
                        />
                        <span className="text-sm font-medium text-cyan-100">
                          {sop.title}
                        </span>
                      </div>
                      <div className="mt-1 ml-6 text-xs text-primary-300">
                        {new Date(sop.uploaded_at).toLocaleDateString()}
                      </div>
                      {sop.rules && sop.rules.length > 0 && (
                        <div className="mt-1 ml-6 text-xs text-primary-400">
                          ✓ {sop.rules.length} rules
                        </div>
                      )}
                    </div>
                    <button
                      onClick={(e) => handleDelete(sop.id, e)}
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

export default SOPUploadWidget;
