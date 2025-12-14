import { forwardRef, useImperativeHandle } from 'react';
import { Loader, Play } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { workflowAPI } from '../../api/workflow.api';

const AnalyzeButton = forwardRef(({ selectedSop, selectedWorkflow, onAnalyze, isAnalyzing, setIsAnalyzing }, ref) => {
  const isEnabled = selectedSop && selectedWorkflow && !isAnalyzing;

  const handleAnalyze = async () => {
    if (!selectedSop || !selectedWorkflow || isAnalyzing) return;

    setIsAnalyzing(true);
    try {
      // Step 1: Run deviation detection
      toast.loading('Detecting deviations...', { id: 'analysis' });
      const deviationResponse = await workflowAPI.analyze();

      console.log('Deviation response:', deviationResponse);

      // Step 2: Run pattern analysis
      toast.loading('Analyzing patterns with AI...', { id: 'analysis' });
      const patternResponse = await workflowAPI.analyzePatterns();

      console.log('Pattern response:', patternResponse);

      // Extract data from nested response structure
      // Backend wraps response in { success, message, data: {...} }
      const deviationData = deviationResponse.data.data || deviationResponse.data;
      const patternData = patternResponse.data.data || patternResponse.data;

      // Combine results
      const analysisResult = {
        deviations: deviationData.deviations || [],
        summary: deviationData.summary || {},
        patterns: patternData.patterns || patternData,
        sop: selectedSop,
        workflow: selectedWorkflow,
        timestamp: new Date().toISOString()
      };

      console.log('Combined analysis result:', analysisResult);

      onAnalyze(analysisResult);
      toast.success('✓ Analysis complete!', { id: 'analysis' });
    } catch (error) {
      console.error('Analysis failed:', error);
      toast.error(`Analysis failed: ${error.response?.data?.message || error.message}`, { id: 'analysis' });
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Expose triggerAnalysis method to parent via ref
  useImperativeHandle(ref, () => ({
    triggerAnalysis: handleAnalyze
  }));

  if (!selectedSop || !selectedWorkflow) {
    return (
      <div className="bg-gradient-to-br from-secondary-800 to-secondary-700 border border-orange-500/30 rounded-lg p-4 shadow-lg relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-24 bg-orange-500/10 rounded-full blur-2xl"></div>
        <div className="relative z-10">
          <h3 className="font-semibold text-orange-300 mb-3">Analysis Requirements</h3>
          <p className="text-sm text-primary-200 mb-3">Please select:</p>
          <ul className="text-sm text-primary-200 space-y-2 ml-2">
            <li className="flex items-center space-x-2">
              {selectedSop ? (
                <div className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center">
                  <span className="text-white text-xs">✓</span>
                </div>
              ) : (
                <div className="w-4 h-4 border-2 border-primary-400 rounded" />
              )}
              <span>1 SOP document</span>
            </li>
            <li className="flex items-center space-x-2">
              {selectedWorkflow ? (
                <div className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center">
                  <span className="text-white text-xs">✓</span>
                </div>
              ) : (
                <div className="w-4 h-4 border-2 border-primary-400 rounded" />
              )}
              <span>1 Workflow log file</span>
            </li>
          </ul>
          <button
            disabled
            className="mt-4 w-full py-3 px-4 bg-secondary-700/50 text-primary-400 rounded-lg cursor-not-allowed border border-secondary-600"
          >
            Analyze (Disabled)
          </button>
          <p className="mt-2 text-xs text-primary-300 text-center">Select files above</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-secondary-800 to-secondary-700 border border-primary-500/30 rounded-lg p-4 shadow-lg relative overflow-hidden">
      <div className="absolute bottom-0 right-0 w-32 h-32 bg-primary-500/10 rounded-full blur-2xl"></div>
      <div className="relative z-10">
        <h3 className="font-semibold text-cyan-300 mb-3">Ready to Analyze</h3>
        <div className="space-y-2 mb-4">
          <div className="text-sm text-primary-200">
            <span className="font-medium">Selected:</span>
          </div>
          <div className="text-sm pl-2 space-y-1">
            <div className="flex items-center space-x-2">
              <div className="w-1.5 h-1.5 rounded-full bg-primary-400"></div>
              <span className="text-cyan-100">SOP: {selectedSop.title}</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-1.5 h-1.5 rounded-full bg-primary-400"></div>
              <span className="text-cyan-100">Logs: {selectedWorkflow.filename}</span>
            </div>
          </div>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={isAnalyzing}
          className={`w-full py-3 px-4 rounded-lg font-semibold flex items-center justify-center space-x-2 transition-all ${
            isAnalyzing
              ? 'bg-primary-600/50 cursor-not-allowed'
              : 'bg-gradient-to-r from-primary-600 to-secondary-600 hover:from-primary-500 hover:to-secondary-500 shadow-lg hover:shadow-primary-500/50'
          } text-white`}
        >
          {isAnalyzing ? (
            <>
              <Loader className="w-5 h-5 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              <span>Analyze Compliance</span>
            </>
          )}
        </button>

        {!isAnalyzing && (
          <div className="mt-3 pt-3 border-t border-primary-500/20 text-xs text-primary-300 space-y-1">
            <div>⏱️ ~5 seconds</div>
            <div>💰 ~$0.11</div>
          </div>
        )}
      </div>
    </div>
  );
});

AnalyzeButton.displayName = 'AnalyzeButton';

export default AnalyzeButton;
