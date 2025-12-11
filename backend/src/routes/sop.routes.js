const express = require('express');
const router = express.Router();
const sopController = require('../controllers/sop.controller');
const { upload } = require('../services/file-upload.service');

router.post('/upload', upload.single('sop'), sopController.uploadSOP);
router.get('/', sopController.listSOPs);
router.get('/:id', sopController.getSOPById);
router.post('/:id/process', sopController.processSOP);
router.get('/:id/rules', sopController.getSOPRules);
router.delete('/:id', sopController.deleteSOP);

module.exports = router;
