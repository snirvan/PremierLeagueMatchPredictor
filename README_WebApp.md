# Premier League Predictor Web Application

A modern web application that displays AI-powered Premier League match predictions alongside actual results.

## Features

- **Season Tabs**: Browse through different Premier League seasons (2019-2024)
- **Match Predictions**: View AI predictions vs actual results for every match
- **Accuracy Statistics**: See overall and per-result-type accuracy metrics
- **Filtering**: Filter matches by correct/incorrect predictions
- **Confidence Scores**: View prediction confidence levels
- **Modern UI**: Clean, responsive design with Tailwind CSS

## Architecture

- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Backend**: Flask API with CORS support
- **ML Model**: Random Forest classifier with scikit-learn
- **Data**: Premier League match data with engineered features

## Setup Instructions

### Prerequisites

- Python 3.12+ with virtual environment
- Node.js 18+ and npm
- Trained ML model files (`rf_model.pkl` and `label_encoder.pkl`)

### Backend Setup

1. Ensure your Python virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```

2. Install Flask dependencies:
   ```bash
   pip install Flask Flask-CORS
   ```

3. Start the backend server:
   ```bash
   ./start_backend.sh
   ```
   
   Or manually:
   ```bash
   cd backend
   python app.py
   ```

   The API will be available at `http://localhost:5001`

### Frontend Setup

1. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   ./start_frontend.sh
   ```
   
   Or manually:
   ```bash
   cd frontend
   npm run dev
   ```

   The web app will be available at `http://localhost:3000`

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/seasons` - Get available seasons
- `GET /api/matches/<season>` - Get matches and predictions for a season
- `GET /api/accuracy/<season>` - Get accuracy statistics for a season

## Usage

1. Start both backend and frontend servers
2. Open `http://localhost:3000` in your browser
3. Select a season from the tabs
4. Browse through match predictions and results
5. Use filters to view correct/incorrect predictions
6. Check accuracy statistics and confidence scores

## File Structure

```
PremierLeaguePredictor/
├── backend/
│   ├── app.py              # Flask API server
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   └── page.tsx    # Main page component
│   │   ├── components/
│   │   │   ├── SeasonTabs.tsx   # Season selection tabs
│   │   │   └── MatchList.tsx    # Match results display
│   │   └── types/
│   │       └── index.ts    # TypeScript definitions
│   ├── package.json
│   └── ...Next.js config files
├── rf_model.pkl           # Trained Random Forest model
├── label_encoder.pkl      # Label encoder for predictions
├── matches_features_with_balance.csv  # Dataset
├── start_backend.sh       # Backend startup script
└── start_frontend.sh      # Frontend startup script
```

## Notes

- The model was trained on seasons 2019-2021, validated on 2022-2023, and tested on 2024
- Current accuracy on 2024 season: ~48% overall
- The web app displays predictions for all available seasons
- Make sure both servers are running for full functionality
