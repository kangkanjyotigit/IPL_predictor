# Dream11 Prediction App

A data-driven fantasy sports prediction application that provides advanced analytics and strategic insights for Dream11 contests.

## Features

### Core Analytics
- Comprehensive player analysis (form, stats, head-to-head records, venue performance)
- Pitch and weather condition analysis with impact predictions
- Real-time match updates (toss, playing XIs, last-minute changes)
- Machine learning prediction algorithms for player performance

### Strategic Tools
- Captain and vice-captain recommendation engine
- Budget optimization (100-credit limit)
- Differential player suggestions (low-ownership, high-potential)
- Multiple team generation with risk profiles (safe, balanced, aggressive)

### User Experience
- Intuitive interface with drag-and-drop team builder
- Performance tracking for prediction accuracy
- Educational content on fantasy strategy
- Community features for sharing insights
- Contest recommendations by skill level

## Technical Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: SQLite (development), PostgreSQL (production)
- **ML/Data Science**: Pandas, NumPy, Scikit-learn, TensorFlow
- **APIs**: Cricket data APIs (Cricsheet, Cricbuzz, ESPNCricinfo)

## Frontend Templates

The application includes the following templates:

### Authentication
- `login.html` - User login page
- `register.html` - New user registration page

### Core Pages
- `index.html` - Homepage/landing page
- `dashboard.html` - User dashboard showing performance and teams

### Match Related
- `matches.html` - List of all matches (live, upcoming, completed)
- `match_detail.html` - Detailed view of a specific match
- `team_builder.html` - Interface for creating Dream11 teams
- `team_detail.html` - View details of a created team

### Player Related
- `players.html` - List of all players with filtering options
- `player_detail.html` - Detailed player statistics and predictions

### Venue Related
- `venues.html` - List of all cricket venues
- `venue_detail.html` - Detailed venue statistics and history

### Analysis and Strategy
- `analytics.html` - Performance analytics and insights
- `strategy.html` - Strategy guides and tips for Dream11
- `profile.html` - User profile management

## Installation

1. Clone the repository
```
git clone https://github.com/yourusername/dream11-prediction.git
cd dream11-prediction
```

2. Create a virtual environment
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Set up environment variables
```
cp .env.example .env
# Edit .env with your API keys
```

5. Initialize the database
```
flask db init
flask db migrate
flask db upgrade
```

6. Run the application
```
flask run
```

## Ethical Considerations

- Transparent methodology for all predictions
- Responsible gaming prompts and spending limits
- Clear disclaimer that predictions are advisory only
- Strong privacy controls for user data

## License

MIT

## Disclaimer

This application is for educational and informational purposes only. Predictions are based on statistical models and historical data, and are not guarantees of future performance. Please use responsibly and gamble within your means.
