# Stock Monitor System

A real-time stock monitoring system that tracks stock prices, calculates RSI indicators, and sends notifications (Email/Telegram) based on user-defined strategies.

## Features

- **Real-time Monitoring**: Fetches stock data every 60 seconds (configurable).
- **Technical Indicators**: Calculates RSI (Relative Strength Index) automatically.
- **Custom Strategies**: Set custom RSI thresholds (Low/High) for each stock.
- **Notifications**: Supports Email and Telegram alerts.
- **Web Interface**: Vue 3 + Element Plus frontend for easy management.

## Project Structure

- `backend/`: Python FastAPI application
  - `app/services/`: Core business logic (Market Data, Indicators, Signals)
  - `app/api/`: REST API endpoints
  - `app/core/`: Configuration, Database, Scheduler
- `frontend/`: Vue 3 application
  - `src/views/`: UI Pages (Stock List, Settings)

## Prerequisites

- Python 3.8+
- Node.js 16+
- Redis (for alarm queue)

## Getting Started

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
# Activate (Windows)
.venv\Scripts\activate
# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Redis (Ensure Redis is running locally on port 6379)
# If you don't have Redis, you can use Docker:
# docker run -d -p 6379:6379 redis

# Run the server
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Usage

1. Open `http://localhost:5173` in your browser.
2. Add a stock code (e.g., `600519` for Moutai).
3. Configure your RSI thresholds in the "Strategy" settings.
4. Set up your notification preferences in "Notification Settings".
5. The system will automatically scan and alert you when conditions are met.

## Configuration

Backend configuration is managed via `backend/app/core/config.py` or environment variables.
Create a `.env` file in `backend/` to override defaults:

```env
DATABASE_URL=sqlite:///./sql_app.db
REDIS_HOST=localhost
SMTP_HOST=smtp.example.com
SMTP_USER=user@example.com
SMTP_PASSWORD=secret
TELEGRAM_BOT_TOKEN=your_bot_token
```
