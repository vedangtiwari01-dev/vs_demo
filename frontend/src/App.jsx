import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import AnalysisHub from './pages/AnalysisHub';
import StressTesting from './pages/StressTesting';

// Old pages - archived (kept for reference)
// import Dashboard from './pages/Dashboard';
// import SOPManagement from './pages/SOPManagement';
// import WorkflowAnalysis from './pages/WorkflowAnalysis';
// import DeviationDetection from './pages/DeviationDetection';
// import BehavioralProfiling from './pages/BehavioralProfiling';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<AnalysisHub />} />
          <Route path="/stress-test" element={<StressTesting />} />

          {/* Old routes - removed to simplify UI */}
          {/* <Route path="/dashboard" element={<Dashboard />} /> */}
          {/* <Route path="/sop" element={<SOPManagement />} /> */}
          {/* <Route path="/workflow" element={<WorkflowAnalysis />} /> */}
          {/* <Route path="/deviations" element={<DeviationDetection />} /> */}
          {/* <Route path="/behavioral" element={<BehavioralProfiling />} /> */}
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
