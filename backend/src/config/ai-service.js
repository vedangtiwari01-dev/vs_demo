module.exports = {
  aiServiceUrl: process.env.AI_SERVICE_URL || 'http://localhost:8000',
  timeout: 300000, // 5 minutes for ML processing
  retryAttempts: 3,
  retryDelay: 1000,
};
