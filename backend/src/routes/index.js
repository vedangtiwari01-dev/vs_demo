const express = require('express');
const router = express.Router();

const sopRoutes = require('./sop.routes');
const workflowRoutes = require('./workflow.routes');
const deviationRoutes = require('./deviation.routes');
const stressTestRoutes = require('./stress-test.routes');
const behavioralRoutes = require('./behavioral.routes');
const analyticsRoutes = require('./analytics.routes');

// Health check
router.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Backend API is running' });
});

// Mount routes
router.use('/sops', sopRoutes);
router.use('/workflows', workflowRoutes);
router.use('/deviations', deviationRoutes);
router.use('/stress-test', stressTestRoutes);
router.use('/behavioral', behavioralRoutes);
router.use('/analytics', analyticsRoutes);

module.exports = router;
