import React, { useState, useEffect } from 'react';
import { FileText, Upload, Trash2, RefreshCw } from 'lucide-react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Loading from '../components/common/Loading';
import FileUpload from '../components/common/FileUpload';
import { sopAPI } from '../api/sop.api';
import toast from 'react-hot-toast';

const SOPManagement = () => {
  const [sops, setSops] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadData, setUploadData] = useState({ file: null, title: '', version: '' });
  const [processing, setProcessing] = useState(null);

  useEffect(() => {
    loadSOPs();
  }, []);

  const loadSOPs = async () => {
    try {
      setLoading(true);
      const response = await sopAPI.list();
      setSops(response.data || []);
    } catch (error) {
      toast.error('Failed to load SOPs');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!uploadData.file) {
      toast.error('Please select a file');
      return;
    }

    try {
      console.log('[handleUpload] Starting upload...');
      const response = await sopAPI.upload(uploadData.file, uploadData.title, uploadData.version);
      console.log('[handleUpload] Upload response:', response);
      toast.success('SOP uploaded successfully');
      setShowUpload(false);
      setUploadData({ file: null, title: '', version: '' });
      loadSOPs();
    } catch (error) {
      console.error('[handleUpload] Upload error:', error);
      console.error('[handleUpload] Error response:', error.response);
      toast.error('Failed to upload SOP: ' + (error.response?.data?.message || error.message));
    }
  };

  const handleProcess = async (id) => {
    try {
      setProcessing(id);
      await sopAPI.process(id);
      toast.success('SOP processed successfully');
      loadSOPs();
    } catch (error) {
      toast.error('Failed to process SOP');
    } finally {
      setProcessing(null);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this SOP?')) return;

    try {
      await sopAPI.delete(id);
      toast.success('SOP deleted successfully');
      loadSOPs();
    } catch (error) {
      toast.error('Failed to delete SOP');
    }
  };

  if (loading) return <Loading message="Loading SOPs..." />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">SOP Management</h1>
          <p className="mt-1 text-gray-600">Upload and manage Standard Operating Procedures</p>
        </div>
        <Button onClick={() => setShowUpload(!showUpload)}>
          <Upload className="h-4 w-4 mr-2" />
          Upload SOP
        </Button>
      </div>

      {showUpload && (
        <Card>
          <h3 className="text-lg font-semibold mb-4">Upload New SOP</h3>
          <div className="space-y-4">
            <FileUpload
              onFileSelect={(file) => setUploadData({ ...uploadData, file })}
              accept=".pdf,.docx"
            />
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Title (optional)"
                className="input"
                value={uploadData.title}
                onChange={(e) => setUploadData({ ...uploadData, title: e.target.value })}
              />
              <input
                type="text"
                placeholder="Version (optional)"
                className="input"
                value={uploadData.version}
                onChange={(e) => setUploadData({ ...uploadData, version: e.target.value })}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleUpload}>Upload</Button>
              <Button variant="secondary" onClick={() => setShowUpload(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6">
        {sops.map((sop) => (
          <Card key={sop.id}>
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-4">
                <div className="bg-primary-100 p-3 rounded-lg">
                  <FileText className="h-6 w-6 text-primary-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{sop.title}</h3>
                  <p className="text-sm text-gray-600">Version: {sop.version || 'N/A'}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    Uploaded: {new Date(sop.uploaded_at).toLocaleDateString()}
                  </p>
                  <div className="mt-2">
                    <span
                      className={`badge ${
                        sop.processed ? 'badge-low' : 'badge-medium'
                      }`}
                    >
                      {sop.status}
                    </span>
                    {sop.rules && sop.rules.length > 0 && (
                      <span className="ml-2 text-sm text-gray-600">
                        {sop.rules.length} rules extracted
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                {!sop.processed && (
                  <Button
                    size="sm"
                    onClick={() => handleProcess(sop.id)}
                    disabled={processing === sop.id}
                  >
                    {processing === sop.id ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      'Process'
                    )}
                  </Button>
                )}
                <Button variant="danger" size="sm" onClick={() => handleDelete(sop.id)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </Card>
        ))}
        {sops.length === 0 && (
          <Card>
            <p className="text-center text-gray-500 py-8">
              No SOPs uploaded yet. Click "Upload SOP" to get started.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
};

export default SOPManagement;
