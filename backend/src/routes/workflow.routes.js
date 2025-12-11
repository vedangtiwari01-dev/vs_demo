const express = require('express');
const router = express.Router();
const workflowController = require('../controllers/workflow.controller');
const { upload } = require('../services/file-upload.service');

router.post('/upload', upload.single('logs'), workflowController.uploadWorkflowLogs);
router.get('/', workflowController.listWorkflowLogs);
router.get('/:caseId', workflowController.getWorkflowByCase);
router.post('/analyze', workflowController.analyzeWorkflow);

module.exports = router;
