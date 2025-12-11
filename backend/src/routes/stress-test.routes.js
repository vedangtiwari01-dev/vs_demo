const express = require('express');
const router = express.Router();
const stressTestController = require('../controllers/stress-test.controller');

router.post('/scenarios', stressTestController.createScenario);
router.get('/scenarios', stressTestController.listScenarios);
router.get('/scenarios/:id', stressTestController.getScenarioById);
router.post('/generate', stressTestController.generateSyntheticLogs);
router.delete('/scenarios/:id', stressTestController.deleteScenario);

module.exports = router;
