import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import SOPManagement from './pages/SOPManagement';
import WorkflowAnalysis from './pages/WorkflowAnalysis';
import DeviationDetection from './pages/DeviationDetection';
import BehavioralProfiling from './pages/BehavioralProfiling';
import StressTesting from './pages/StressTesting';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/sop" element={<SOPManagement />} />
          <Route path="/workflow" element={<WorkflowAnalysis />} />
          <Route path="/deviations" element={<DeviationDetection />} />
          <Route path="/behavioral" element={<BehavioralProfiling />} />
          <Route path="/stress-test" element={<StressTesting />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
