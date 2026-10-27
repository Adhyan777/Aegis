# Aegis — Fraud Detection & Transaction Intelligence

Aegis is a full-stack financial transaction monitoring dashboard that combines transaction analytics, rule-based fraud detection, and statistical anomaly analysis to help identify suspicious activity and explain risk signals.

## Overview

Aegis brings transaction data, analytics, and fraud investigation into one interface. It is built to demonstrate full-stack engineering, API integration, database design, and explainable risk scoring.

## Features

- **Transaction monitoring:** Browse and inspect transaction records.
- **Analytics dashboard:** View transaction metrics, charts, and breakdowns.
- **Rule-based fraud detection:** Evaluate transactions against configurable risk indicators.
- **Statistical anomaly detection:** Identify unusual spending patterns, large amounts, repeated transactions, and declined payments.
- **Fraud intelligence:** Combine risk signals and explanatory reasons.
- **Investigation interface:** Review suspicious transactions in the dashboard.
- **REST API:** Serve transaction, analytics, and fraud-intelligence data.
- **Automated tests:** Verify core anomaly-detection behavior.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| Code quality | ESLint |
| Testing | Python `unittest` |

## Architecture

```text
React + TypeScript Dashboard
             |
          REST API
             |
          FastAPI
             |
       +-----+------+
       |            |
  PostgreSQL   Fraud Analysis
                    |
             +------+------+
             |             |
        Rule-Based     Statistical
         Scoring       Heuristic
             |             |
             +------+------+
                    |
             Risk Explanations
```

## Getting Started

### Prerequisites

- Python
- Node.js and npm
- PostgreSQL

### 1. Configure the backend

From the project root, activate the existing virtual environment and start FastAPI:

```powershell
cd backend
..\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Configure your local database connection and required environment variables in `backend/.env` according to the backend configuration. Ensure PostgreSQL is running before starting the application.

Backend URL: `http://127.0.0.1:8000`

Interactive API documentation: `http://127.0.0.1:8000/docs`

### 2. Start the frontend

Open a second terminal:

```powershell
cd "D:\Projects(Adhyan)\Aegis\frontend"
npm install
npm run dev
```

Open the local URL printed by Vite, typically `http://localhost:5173`.

### 3. Run the frontend checks

From the frontend directory:

```powershell
npm run lint
npm run build
```

### 4. Run the anomaly-detection tests

From the backend directory:

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Backend health check |
| GET | `/api/transactions` | Retrieve transactions |
| POST | `/api/transactions` | Create a transaction |
| DELETE | `/api/transactions/{transaction_id}` | Delete a transaction |
| GET | `/api/fraud/summary` | Fraud summary |
| GET | `/api/fraud/analyze/{transaction_id}` | Rule-based transaction analysis |
| GET | `/api/fraud/analyze-all` | Analyze transactions using fraud rules |
| GET | `/api/fraud/ml/analyze/{transaction_id}` | Statistical anomaly analysis |
| GET | `/api/fraud/intelligence/{transaction_id}` | Combined fraud intelligence |
| GET | `/api/fraud/intelligence-all` | Fraud intelligence across transactions |

For additional analytics endpoints and request schemas, see the interactive API documentation at `/docs`.

## Fraud Detection Approach

Aegis combines rule-based scoring with a pure-Python statistical anomaly heuristic. The system evaluates signals such as unusually large transactions, customer spending spikes, repeated activity, and failed or declined payments.

**Important:** The current anomaly detector is not a trained machine-learning model. Its score is a heuristic risk score, not a calibrated probability of fraud.

## Testing and Evaluation

The project includes unit tests and synthetic stress-test scenarios to check expected detector behavior.

Synthetic tests are useful for validating implementation and detecting regressions, but they do not establish real-world fraud-detection accuracy. Production-quality evaluation would require representative labeled data, a held-out test set, and appropriate precision, recall, F1-score, and false-positive analysis.

## Future Improvements

- Train and evaluate a genuine machine-learning model on suitable labeled data.
- Add API integration tests and continuous integration.
- Improve risk-threshold configuration and analyst feedback workflows.
- Add authentication, authorization, and audit logging.
- Deploy the application securely.
- Add dashboard screenshots and a live demonstration.

## Project Purpose

Aegis demonstrates full-stack application development, REST API design, relational database integration, transaction analytics, and explainable fraud-risk analysis in a financial monitoring use case.
