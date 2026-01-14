module.exports = {
  aiServiceUrl: process.env.AI_SERVICE_URL || 'http://localhost:8000',
  timeout: 1200000, // 20 minutes for ML processing (needed for large SOPs with chunked extraction)
  retryAttempts: 3,
  retryDelay: 1000,
};
