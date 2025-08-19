# FinSim Web Application

A modern web application for personal injury settlement analysis, built with React and Flask, using the PolicyEngine design system.

## Overview

FinSim Web helps users analyze retirement options for personal injury settlements by comparing different investment scenarios including annuities and stock portfolios. The application uses Monte Carlo simulations to provide confidence-based spending recommendations.

## Features

- **Multiple Scenario Comparison**: Compare 100% stocks vs various annuity options
- **Monte Carlo Simulation**: 2,000 simulations per scenario for robust analysis
- **Confidence-Based Analysis**: See sustainable spending at different confidence levels (90%, 75%, 50%, 25%)
- **Interactive Charts**: Visualize success rates across different spending levels
- **Export Functionality**: Download results as CSV for further analysis
- **PolicyEngine Tax Integration**: Accurate federal and state tax calculations

## Architecture

The application consists of:
- **Frontend**: React with TypeScript, Vite, and Recharts for visualization
- **Backend**: Flask API with Python simulation engine
- **Styling**: PolicyEngine design system with Roboto font and teal/blue color palette

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 22+
- npm

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Run tests (TDD approach)
python -m pytest tests/ -v

# Start the Flask server
python app.py
```

The backend will run on http://localhost:5000

### Frontend Setup

```bash
cd frontend
npm install

# Run tests
npm test

# Start the development server
npm run dev
```

The frontend will run on http://localhost:3000

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/scenarios` - Get available scenarios
- `POST /api/simulate` - Run single simulation
- `POST /api/simulate/batch` - Run batch simulations
- `POST /api/analyze/confidence` - Analyze confidence thresholds
- `POST /api/export` - Export results as CSV or JSON

## Testing

The project follows Test-Driven Development (TDD):

### Backend Tests
```bash
cd backend
python -m pytest tests/test_api.py -v --cov=.
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

## Deployment

### Production Build

Frontend:
```bash
cd frontend
npm run build
```

Backend:
```bash
cd backend
gunicorn app:app --bind 0.0.0.0:5000
```

### Docker Support

Build and run with Docker:
```bash
docker-compose up --build
```

## Configuration

### Environment Variables

Backend (.env):
```
FLASK_ENV=production
FLASK_DEBUG=0
API_KEY=your-api-key
```

Frontend (.env):
```
VITE_API_URL=https://api.yourdomain.com
```

## PolicyEngine Integration

The application uses PolicyEngine for accurate tax calculations:
- Federal and state income tax
- Capital gains tax
- Social Security taxation
- State-specific tax rules

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests first (TDD)
4. Implement features
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - See LICENSE file for details