const express = require('express');
const router = express.Router();
const deviationController = require('../controllers/deviation.controller');

router.get('/', deviationController.listDeviations);
router.get('/summary', deviationController.getDeviationSummary);
router.get('/by-officer', deviationController.getDeviationsByOfficer);
router.get('/by-type', deviationController.getDeviationsByType);
router.get('/:id', deviationController.getDeviationById);

module.exports = router;
