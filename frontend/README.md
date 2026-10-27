# Aegis — Fraud Detection Dashboard

Aegis is a full-stack financial transaction monitoring and fraud intelligence application. Its React dashboard connects to a FastAPI backend and PostgreSQL database to display transaction analytics, suspicious activity, risk indicators, and fraud investigation details.

## Features

- Transaction monitoring and search
- Dashboard metrics and analytics charts
- Fraud intelligence and risk summaries
- Anomaly detection insights and risk explanations
- Transaction detail views
- Fraud investigation queue
- REST API integration with the Aegis backend

## Tech Stack

- **React** — UI components
- **TypeScript** — type-safe application code
- **Vite** — development server and production bundler
- **ESLint** — code quality checks
- **FastAPI** — backend API
- **PostgreSQL** — transaction database

## Getting Started

### Prerequisites

- Node.js and npm
- The Aegis backend configured and running
- PostgreSQL running with the backend database configured

### Install dependencies

From the frontend directory:

```bash
npm install
```

### Start the development server

```bash
npm run dev
```

Open the local URL displayed in the terminal, typically `http://localhost:5173`.

### Run the production build

```bash
npm run build
```

### Run lint checks

```bash
npm run lint
```

## Backend Connection

The frontend communicates with the Aegis FastAPI backend, normally available at:

`http://127.0.0.1:8000`

Start the backend separately and ensure PostgreSQL is running. If dashboard data fails to load, verify the backend health endpoint and check the browser console for API or CORS errors.

## Fraud Detection Note

Aegis currently combines rule-based fraud scoring with a pure-Python statistical anomaly heuristic. The anomaly score is a heuristic risk score, not a probability of fraud, and the current detector is not a trained machine-learning model.

## Development

The application uses Vite's hot-module replacement for fast development. TypeScript and ESLint help maintain code quality as the project evolves.

For complete backend setup, API endpoints, architecture, and evaluation details, see the root project README.

