# Loan Processing SOP Compliance & Deviation Detection System

An AI-powered full-stack web application that extracts rules from Standard Operating Procedures (SOPs), analyzes workflow logs, detects compliance deviations, profiles officer behavior, and simulates stress-test scenarios.

## Overview

In real loan processing operations, officers and analysts often deviate from SOPs due to time pressure, informal practices, system issues, or workload. These deviations create regulatory and financial risks. This system helps identify, analyze, and understand these deviations to improve compliance and operational efficiency.

## Key Features

### Core Compliance Features
- **SOP Document Upload & Parsing**: Upload SOP documents (PDF/DOCX) and automatically extract compliance rules using NLP
- **Workflow Log Analysis**: Upload workflow logs (CSV/JSON) and analyze actual processing steps
- **Deviation Detection**: Automatically detect:
  - Missing steps
  - Wrong sequence
  - Improper approvals
  - Timing violations
  - Control breaches
- **Graphical Visualization**: Visual representation of process flows, deviations, and compliance metrics

### Advanced Features
- **Behavioral Pattern Profiling**: Detect individual and team-level behavioral patterns
  - "Officer X repeatedly skips income verification when workload > 20 cases/day"
  - "Analyst Y overrides collateral valuation when senior authority is unavailable"
  - "Team A has 70% higher deviation rate than Team B"
- **Stress Testing**: Generate synthetic workflow logs under extreme scenarios:
  - Officer shortage (reduced staff, increased workload)
  - Peak load (compressed timelines, high volume)
  - System downtime (gaps in processing, batched operations)
  - Regulatory changes (new required steps, adaptation period)

## Tech Stack

- **Backend**: Node.js + Express (RESTful API, file handling, business logic)
- **Frontend**: React + Vite + Tailwind CSS (modern, responsive UI)
- **AI Service**: Python + FastAPI (NLP, deviation detection, behavioral profiling)
- **Database**: SQLite (zero-config, file-based)
- **ML/NLP**: Rule-based logic with pattern matching (easily extensible to ML models)

## Architecture

```
┌─────────────────────────────────────────────┐
│         Frontend (React + Vite)             │
│      http://localhost:5174                  │
└──────────────┬──────────────────────────────┘
               │ REST API
               │
┌──────────────┴──────────────────────────────┐
│       Backend (Node.js + Express)           │
│         http://localhost:3000               │
│    ├── File Upload & Management             │
│    ├── Business Logic                       │
│    └── SQLite Database                      │
└──────────────┬──────────────────────────────┘
               │ HTTP/JSON
               │
┌──────────────┴──────────────────────────────┐
│      AI Service (Python + FastAPI)          │
│         http://localhost:8000               │
│    ├── NLP (SOP Parsing)                    │
│    ├── Deviation Detection                  │
│    ├── Behavioral Profiling                 │
│    └── Synthetic Log Generation             │
└─────────────────────────────────────────────┘
```

## Prerequisites

- **Node.js**: 18.x or higher
- **Python**: 3.9 or higher
- **npm** or **yarn**
- **pip** (Python package manager)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd vs_demo
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Start the backend server
npm run dev
```

The backend will run at `http://localhost:3000`

### 3. AI Service Setup

```bash
cd ai-service

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the AI service
python main.py
```

The AI service will run at `http://localhost:8000`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Start the development server
npm run dev
```

The frontend will run at `http://localhost:5174`

## Usage Guide

### Quick Start with Sample Data

1. **Start all three services** (Backend, AI Service, Frontend)

2. **Upload Sample SOP**:
   - Navigate to **SOP Management** page
   - Click "Upload SOP"
   - Upload the sample SOP from `backend/sample-data/sample-sop-text.txt` (or convert to PDF)
   - Click "Process" to extract rules

3. **Upload Sample Workflow Logs**:
   - Navigate to **Workflow Analysis** page
   - Upload `backend/sample-data/sample-workflow-logs.csv`
   - Click "Analyze Workflow" to detect deviations

4. **View Results**:
   - **Dashboard**: Overview of compliance metrics
   - **Deviations**: Detailed list of detected violations
   - **Behavioral Profiling**: Officer risk matrix and behavioral patterns

5. **Run Stress Test**:
   - Navigate to **Stress Testing** page
   - Select a scenario type (e.g., "Officer Shortage")
   - Configure parameters
   - Click "Generate Synthetic Logs"
   - Analyze the generated logs to see deviation patterns under stress

## API Documentation

### Backend API Endpoints

**Base URL**: `http://localhost:3000/api`

#### SOP Management
- `POST /sops/upload` - Upload SOP document
- `GET /sops` - List all SOPs
- `GET /sops/:id` - Get SOP details
- `POST /sops/:id/process` - Process SOP and extract rules
- `GET /sops/:id/rules` - Get extracted rules
- `DELETE /sops/:id` - Delete SOP

#### Workflow Logs
- `POST /workflows/upload` - Upload workflow logs
- `GET /workflows` - List workflow logs
- `GET /workflows/:caseId` - Get logs for specific case
- `POST /workflows/analyze` - Analyze logs and detect deviations

#### Deviations
- `GET /deviations` - List deviations (supports filters)
- `GET /deviations/:id` - Get deviation details
- `GET /deviations/summary` - Get deviation summary statistics
- `GET /deviations/by-officer` - Group deviations by officer
- `GET /deviations/by-type` - Group deviations by type

#### Behavioral Profiling
- `GET /behavioral/officers` - List officers with profiles
- `GET /behavioral/officers/:id` - Get officer profile details
- `POST /behavioral/officers/profile` - Build officer profile
- `GET /behavioral/patterns` - Get detected behavioral patterns
- `POST /behavioral/patterns/analyze` - Analyze patterns for officer
- `GET /behavioral/risk-matrix` - Get team risk matrix

#### Stress Testing
- `POST /stress-test/scenarios` - Create stress test scenario
- `GET /stress-test/scenarios` - List scenarios
- `POST /stress-test/generate` - Generate synthetic logs

#### Analytics
- `GET /analytics/dashboard` - Get dashboard summary
- `GET /analytics/compliance-rate` - Calculate compliance rate
- `GET /analytics/trends` - Get deviation trends over time
- `GET /analytics/process-flow` - Get process flow visualization data

### AI Service Endpoints

**Base URL**: `http://localhost:8000`

- `POST /ai/sop/parse` - Parse SOP document
- `POST /ai/sop/extract-rules` - Extract rules from text
- `POST /ai/deviation/detect` - Detect all deviations
- `POST /ai/behavioral/profile` - Build behavioral profile
- `POST /ai/behavioral/patterns` - Detect behavioral patterns
- `POST /ai/synthetic/generate` - Generate synthetic logs

## Database Schema

The system uses SQLite with the following core tables:

- **sops**: Uploaded SOP documents
- **sop_rules**: Extracted rules from SOPs
- **workflow_logs**: All workflow event logs
- **officers**: Officer information
- **deviations**: Detected compliance violations
- **behavioral_profiles**: Officer behavior metrics
- **behavioral_patterns**: Specific behavior patterns
- **stress_test_scenarios**: Stress test configurations

## Project Structure

```
loan-sop-compliance-system/
├── backend/                 # Node.js Express Backend
│   ├── src/
│   │   ├── config/         # Database and AI service config
│   │   ├── models/         # Sequelize models (8 tables)
│   │   ├── routes/         # API routes
│   │   ├── controllers/    # Business logic
│   │   ├── services/       # AI integration, file upload
│   │   ├── middleware/     # Error handling, validation
│   │   └── utils/          # Helper functions
│   ├── uploads/            # Uploaded files
│   ├── sample-data/        # Sample SOP and logs
│   ├── package.json
│   └── server.js
│
├── frontend/                # React + Vite Frontend
│   ├── src/
│   │   ├── api/            # API client and endpoints
│   │   ├── components/     # Reusable components
│   │   │   ├── common/     # Button, Card, FileUpload, Loading
│   │   │   └── layout/     # Navbar, Layout
│   │   ├── pages/          # Main application pages
│   │   │   ├── Dashboard.jsx
│   │   │   ├── SOPManagement.jsx
│   │   │   ├── WorkflowAnalysis.jsx
│   │   │   ├── DeviationDetection.jsx
│   │   │   ├── BehavioralProfiling.jsx
│   │   │   └── StressTesting.jsx
│   │   ├── utils/          # Constants, helpers
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── index.html
│
└── ai-service/              # Python FastAPI AI Microservice
    ├── app/
    │   ├── models/         # Pydantic schemas
    │   ├── routers/        # API endpoints
    │   ├── services/       # Core AI logic
    │   │   ├── nlp/        # SOP parsing, rule extraction
    │   │   ├── deviation/  # Deviation detection logic
    │   │   ├── behavioral/ # Behavioral profiling
    │   │   └── synthetic/  # Synthetic log generation
    │   └── utils/
    ├── requirements.txt
    └── main.py
```

## Development

### Adding New Rules

Edit `ai-service/app/services/nlp/rule_parser.py` to add new pattern matching rules for SOP parsing.

### Extending ML Capabilities

The current implementation uses rule-based logic. To add machine learning:

1. Install additional dependencies (scikit-learn, spaCy models)
2. Train models on historical data
3. Replace rule-based logic in deviation detection services
4. Update Pydantic schemas for ML model outputs

### Database Migrations

SQLite schema is auto-synced via Sequelize. For PostgreSQL in production:

```bash
# Update connection string in backend/src/config/database.js
# Run migrations
npm run migrate
```

## Troubleshooting

### Backend won't start
- Check if port 3000 is available
- Ensure all npm dependencies are installed
- Verify .env file exists

### AI Service won't start
- Check if port 8000 is available
- Ensure Python virtual environment is activated
- Verify all pip packages are installed
- Check Python version (3.9+)

### Frontend won't connect to backend
- Verify backend is running on port 3000
- Check VITE_API_URL in frontend/.env
- Clear browser cache and restart dev server

### File upload fails
- Check backend/uploads directory exists and has write permissions
- Verify file size is under 50MB
- Check file type matches allowed extensions

## Production Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Stop services
docker-compose down
```

### Manual Deployment

1. **Backend**: Use PM2 for process management
2. **Frontend**: Build with `npm run build` and serve with nginx
3. **AI Service**: Use uvicorn with --workers flag
4. **Database**: Migrate to PostgreSQL for production

## Performance Considerations

- **Database**: SQLite is suitable for < 100K records. Use PostgreSQL for larger datasets
- **File Storage**: Consider moving to S3/cloud storage for production
- **Caching**: Implement Redis for frequently accessed data
- **Scaling**: Backend and AI service can be horizontally scaled

## Security Notes

- No authentication implemented (add JWT or OAuth for production)
- File uploads should be scanned for malware
- Implement rate limiting for API endpoints
- Use HTTPS in production
- Sanitize all user inputs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: This README

## Acknowledgments

Built as a demonstration of AI-powered compliance monitoring for loan processing operations.

---

**Version**: 1.0.0
**Last Updated**: December 2025
