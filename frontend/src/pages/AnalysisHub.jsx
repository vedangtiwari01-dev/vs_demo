import { useRef, useContext } from 'react';
import { AnalysisContext } from '../context/AnalysisContext';
import SOPUploadWidget from '../components/analysis/SOPUploadWidget';
import WorkflowUploadWidget from '../components/analysis/WorkflowUploadWidget';
import AnalyzeButton from '../components/analysis/AnalyzeButton';
import ResultsViewer from '../components/analysis/ResultsViewer';

const AnalysisHub = () => {
  const { state, updateState } = useContext(AnalysisContext);
  const analyzeButtonRef = useRef(null);

  const handleReanalyze = () => {
    // Trigger analysis by calling the AnalyzeButton's method
    if (analyzeButtonRef.current) {
      analyzeButtonRef.current.triggerAnalysis();
    }
  };

  return (
    <div className="flex w-full h-screen bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50 relative overflow-hidden">
      {/* Left Sidebar - 25% - Pinned to absolute left */}
      <aside className="w-1/4 min-w-[25%] max-w-[25%] bg-gradient-to-b from-secondary-900 via-secondary-800 to-secondary-900 border-r border-primary-600/30 overflow-y-auto relative z-10 shadow-2xl">
        <div className="p-6">
          <div className="mb-8 relative">
            <div className="absolute -left-4 top-0 w-1 h-full bg-gradient-to-b from-primary-500 to-transparent"></div>
            <h1 className="text-3xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-blue-300">
              Compliance Analysis
            </h1>
            <p className="text-primary-200 text-sm mt-2">Advanced SOP Deviation Detection</p>
          </div>

          <SOPUploadWidget
            selectedSop={state.selectedSop}
            onSelectSop={(sop) => updateState({ selectedSop: sop })}
          />

          <WorkflowUploadWidget
            selectedWorkflow={state.selectedWorkflow}
            onSelectWorkflow={(workflow) => updateState({ selectedWorkflow: workflow })}
          />

          <AnalyzeButton
            ref={analyzeButtonRef}
            selectedSop={state.selectedSop}
            selectedWorkflow={state.selectedWorkflow}
            onAnalyze={(result) => updateState({ analysisResult: result })}
            isAnalyzing={state.isAnalyzing}
            setIsAnalyzing={(analyzing) => updateState({ isAnalyzing: analyzing })}
          />
        </div>
      </aside>

      {/* Right Panel - 75% */}
      <main className="flex-1 w-3/4 overflow-y-auto relative z-10">
        <ResultsViewer
          analysisResult={state.analysisResult}
          isAnalyzing={state.isAnalyzing}
          onReanalyze={handleReanalyze}
        />
      </main>
    </div>
  );
};

export default AnalysisHub;
