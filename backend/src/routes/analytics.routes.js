const express = require('express');
const router = express.Router();
const analyticsController = require('../controllers/analytics.controller');

router.get('/dashboard', analyticsController.getDashboard);
router.get('/compliance-rate', analyticsController.getComplianceRate);
router.get('/trends', analyticsController.getTrends);
router.get('/process-flow', analyticsController.getProcessFlow);

module.exports = router;
