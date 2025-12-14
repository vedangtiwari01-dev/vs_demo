const express = require('express');
const router = express.Router();
const workflowController = require('../controllers/workflow.controller');
const { upload } = require('../services/file-upload.service');

// Intelligent column mapping flow
router.post('/analyze-headers', upload.single('logs'), workflowController.analyzeHeaders);
router.post('/upload-with-mapping', upload.single('logs'), workflowController.uploadWithMapping);

// Original upload (kept for backward compatibility)
router.post('/upload', upload.single('logs'), workflowController.uploadWorkflowLogs);

// File management endpoints
router.get('/list-files', workflowController.listWorkflowFiles);

// Query endpoints
router.get('/', workflowController.listWorkflowLogs);
router.get('/:caseId', workflowController.getWorkflowByCase);

// Delete endpoint (must be before /:caseId to avoid conflict)
router.delete('/:id', workflowController.deleteWorkflowFile);

// Analysis endpoints
router.post('/analyze', workflowController.analyzeWorkflow);
router.post('/analyze-patterns', workflowController.analyzePatterns);

module.exports = router;
