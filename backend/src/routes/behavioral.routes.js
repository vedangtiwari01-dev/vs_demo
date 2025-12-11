const express = require('express');
const router = express.Router();
const behavioralController = require('../controllers/behavioral.controller');

router.get('/officers', behavioralController.listOfficers);
router.get('/officers/:id', behavioralController.getOfficerProfile);
router.post('/officers/profile', behavioralController.buildOfficerProfile);
router.get('/patterns', behavioralController.detectPatterns);
router.post('/patterns/analyze', behavioralController.analyzePatterns);
router.get('/risk-matrix', behavioralController.getRiskMatrix);

module.exports = router;
