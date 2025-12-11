const axios = require('axios');
const config = require('../config/ai-service');

class AIIntegrationService {
  constructor() {
    this.client = axios.create({
      baseURL: config.aiServiceUrl,
      timeout: config.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async parseSOP(filePath, fileType) {
    try {
      const response = await this.client.post('/ai/sop/parse', {
        file_path: filePath,
        file_type: fileType,
      });
      return response.data;
    } catch (error) {
      console.error('Error parsing SOP:', error.message);
      throw new Error('Failed to parse SOP document');
    }
  }

  async extractRules(sopText) {
    try {
      const response = await this.client.post('/ai/sop/extract-rules', {
        text: sopText,
      });
      return response.data;
    } catch (error) {
      console.error('Error extracting rules:', error.message);
      throw new Error('Failed to extract rules from SOP');
    }
  }

  async detectDeviations(logs, rules) {
    try {
      const response = await this.client.post('/ai/deviation/detect', {
        logs,
        rules,
      });
      return response.data;
    } catch (error) {
      console.error('Error detecting deviations:', error.message);
      throw new Error('Failed to detect deviations');
    }
  }

  async validateSequence(logs, expectedSequence) {
    try {
      const response = await this.client.post('/ai/deviation/validate-sequence', {
        logs,
        expected_sequence: expectedSequence,
      });
      return response.data;
    } catch (error) {
      console.error('Error validating sequence:', error.message);
      throw new Error('Failed to validate sequence');
    }
  }

  async buildBehavioralProfile(officerId, logs, deviations) {
    try {
      const response = await this.client.post('/ai/behavioral/profile', {
        officer_id: officerId,
        logs,
        deviations,
      });
      return response.data;
    } catch (error) {
      console.error('Error building behavioral profile:', error.message);
      throw new Error('Failed to build behavioral profile');
    }
  }

  async detectPatterns(officerId, logs, deviations) {
    try {
      const response = await this.client.post('/ai/behavioral/patterns', {
        officer_id: officerId,
        logs,
        deviations,
      });
      return response.data;
    } catch (error) {
      console.error('Error detecting patterns:', error.message);
      throw new Error('Failed to detect behavioral patterns');
    }
  }

  async calculateRiskScore(officerId, deviations) {
    try {
      const response = await this.client.post('/ai/behavioral/risk-score', {
        officer_id: officerId,
        deviations,
      });
      return response.data;
    } catch (error) {
      console.error('Error calculating risk score:', error.message);
      throw new Error('Failed to calculate risk score');
    }
  }

  async generateSyntheticLogs(scenarioType, parameters) {
    try {
      const response = await this.client.post('/ai/synthetic/generate', {
        scenario_type: scenarioType,
        parameters,
      });
      return response.data;
    } catch (error) {
      console.error('Error generating synthetic logs:', error.message);
      throw new Error('Failed to generate synthetic logs');
    }
  }

  async healthCheck() {
    try {
      const response = await this.client.get('/ai/health');
      return response.data;
    } catch (error) {
      console.error('AI service health check failed:', error.message);
      return { status: 'unhealthy', error: error.message };
    }
  }
}

module.exports = new AIIntegrationService();
