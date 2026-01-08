import { createContext, useState, useEffect } from 'react';

export const AnalysisContext = createContext();

export const AnalysisProvider = ({ children }) => {
  // Initialize state - try to restore from localStorage first
  const [state, setState] = useState(() => {
    try {
      const saved = localStorage.getItem('analysisState');
      if (saved) {
        const parsed = JSON.parse(saved);
        console.log('[AnalysisContext] Restored state from localStorage');
        return parsed;
      }
    } catch (error) {
      console.error('[AnalysisContext] Failed to restore state:', error);
    }

    // Default state if nothing saved or error occurred
    return {
      selectedSop: null,
      selectedWorkflow: null,
      analysisResult: null,
      patternAnalysis: null,
      isAnalyzing: false,
      uploadHistory: []
    };
  });

  // Persist state to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem('analysisState', JSON.stringify(state));
    } catch (error) {
      console.error('[AnalysisContext] Failed to save state:', error);
    }
  }, [state]);

  // Helper function to update specific parts of state
  const updateState = (updates) => {
    setState((prevState) => ({
      ...prevState,
      ...updates
    }));
  };

  // Clear state (useful for reset/logout)
  const clearState = () => {
    setState({
      selectedSop: null,
      selectedWorkflow: null,
      analysisResult: null,
      patternAnalysis: null,
      isAnalyzing: false,
      uploadHistory: []
    });
    localStorage.removeItem('analysisState');
  };

  const value = {
    state,
    setState,
    updateState,
    clearState
  };

  return (
    <AnalysisContext.Provider value={value}>
      {children}
    </AnalysisContext.Provider>
  );
};
