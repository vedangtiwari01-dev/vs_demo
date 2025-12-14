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

  async extractRules(sopText, useLLM = true) {
    try {
      // use_llm should be a query parameter, not in the body
      const response = await this.client.post(
        `/ai/sop/extract-rules?use_llm=${useLLM}`,
        {
          text: sopText,
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error extracting rules:', error.message);
      console.error('Error details:', error.response?.data || error);
      throw new Error('Failed to extract rules from SOP');
    }
  }

  async analyzeColumnMapping(headers, sampleRows = []) {
    try {
      const response = await this.client.post('/ai/mapping/analyze-headers', {
        headers,
        sample_rows: sampleRows,
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing column mapping:', error.message);
      throw new Error('Failed to analyze column headers');
    }
  }

  async analyzeDeviationPatterns(deviationsWithNotes) {
    try {
      console.log(`[AI Service] Analyzing ${deviationsWithNotes.length} deviations for patterns...`);

      // Use extended timeout for pattern analysis (10 minutes)
      const response = await this.client.post(
        '/ai/deviation/analyze-patterns',
        { deviations: deviationsWithNotes },
        { timeout: 600000 } // 10 minutes
      );

      console.log('[AI Service] Pattern analysis complete');
      return response.data;
    } catch (error) {
      if (error.code === 'ECONNABORTED') {
        console.error('Error analyzing deviation patterns: Request timed out after 10 minutes');
        throw new Error('Pattern analysis timed out - try analyzing fewer deviations');
      }
      console.error('Error analyzing deviation patterns:', error.message);
      throw new Error('Failed to analyze deviation patterns');
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
