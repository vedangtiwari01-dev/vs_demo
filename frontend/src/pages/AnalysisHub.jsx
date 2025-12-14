import { useState } from 'react';
import SOPUploadWidget from '../components/analysis/SOPUploadWidget';
import WorkflowUploadWidget from '../components/analysis/WorkflowUploadWidget';
import AnalyzeButton from '../components/analysis/AnalyzeButton';
import ResultsViewer from '../components/analysis/ResultsViewer';

const AnalysisHub = () => {
  const [selectedSop, setSelectedSop] = useState(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  return (
    <div className="flex w-full h-screen bg-gradient-to-br from-slate-50 via-cyan-50 to-blue-50 relative overflow-hidden">
      {/* Geometric Background Designs */}
      <div className="absolute inset-0 pointer-events-none opacity-30">
        <div className="absolute top-10 right-20 w-64 h-64 bg-gradient-to-br from-primary-400 to-transparent rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 left-10 w-96 h-96 bg-gradient-to-tr from-secondary-400 to-transparent rounded-full blur-3xl"></div>
        <div className="absolute top-1/3 right-1/3 w-32 h-32 border-4 border-primary-300 rotate-45 opacity-20"></div>
        <div className="absolute bottom-1/4 right-1/4 w-24 h-24 border-4 border-secondary-300 rounded-full opacity-20"></div>
      </div>

      {/* Left Sidebar - 25% - Pinned to absolute left */}
      <aside className="w-1/4 min-w-[25%] max-w-[25%] bg-gradient-to-b from-secondary-900 via-secondary-800 to-secondary-900 border-r border-primary-600/30 overflow-y-auto relative z-10 shadow-2xl">
        {/* Geometric Accent */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-primary-500/20 to-transparent"></div>
        <div className="absolute bottom-20 left-0 w-24 h-24 bg-gradient-to-tr from-primary-500/20 to-transparent rounded-full"></div>

        <div className="p-6">
          <div className="mb-8 relative">
            <div className="absolute -left-4 top-0 w-1 h-full bg-gradient-to-b from-primary-500 to-transparent"></div>
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-blue-300">
              Compliance Analysis
            </h1>
            <p className="text-primary-200 text-sm mt-2">Advanced SOP Deviation Detection</p>
          </div>

          <SOPUploadWidget
            selectedSop={selectedSop}
            onSelectSop={setSelectedSop}
          />

          <WorkflowUploadWidget
            selectedWorkflow={selectedWorkflow}
            onSelectWorkflow={setSelectedWorkflow}
          />

          <AnalyzeButton
            selectedSop={selectedSop}
            selectedWorkflow={selectedWorkflow}
            onAnalyze={setAnalysisResult}
            isAnalyzing={isAnalyzing}
            setIsAnalyzing={setIsAnalyzing}
          />
        </div>
      </aside>

      {/* Right Panel - 75% */}
      <main className="flex-1 w-3/4 overflow-y-auto relative z-10">
        <ResultsViewer
          analysisResult={analysisResult}
          isAnalyzing={isAnalyzing}
        />
      </main>
    </div>
  );
};

export default AnalysisHub;
