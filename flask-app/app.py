import os
import atexit
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from dotenv import load_dotenv
from src.database import db
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
            static_folder='src/frontend/static',
            template_folder='src/frontend/templates')

# Configure app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
# Ensure instance folder exists for SQLite and other runtime files
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'dream11_prediction.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f"sqlite:///{db_path}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(app.instance_path, 'flask_session')
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Create session directory if it doesn't exist
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Enable CORS
CORS(app)

# Initialize database with app
db.init_app(app)
migrate = Migrate(app, db)

# Initialize Flask-Session
from flask_session import Session
Session(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'frontend.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Set up user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from src.models.user import User
    return User.query.get(int(user_id))

# Import and register blueprints
from src.api.routes import api_bp
from src.frontend.routes import frontend_bp

app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(frontend_bp)

# Exempt API routes from CSRF protection for JSON-based endpoints
csrf.exempt(api_bp)

# Database tables are managed via Alembic migrations. Do not call db.create_all() at runtime.

# Initialize the background scheduler for auto-updating cricket data
scheduler = BackgroundScheduler()

# Import the cricket data update function
def init_scheduler():
    """Initialize the scheduler to auto-update cricket match data"""
    try:
        # Import here to avoid circular imports
        from scripts.update_cricket_data import update_cricket_data
        
        # Schedule all cricket matches update job to run every 4 hours
        scheduler.add_job(
            lambda: update_cricket_data(match_type='all'), 
            'interval', 
            hours=4, 
            id='update_all_matches'
        )
        
        # Also run immediately on startup to ensure fresh data
        scheduler.add_job(
            lambda: update_cricket_data(match_type='all'),
            id='startup_update'
        )
        
        # Start the scheduler
        scheduler.start()
        
        # Register the shutdown hook to close scheduler when app stops
        atexit.register(lambda: scheduler.shutdown())
        
        logging.info("Cricket match data auto-update scheduler initialized")
    except Exception as e:
        logging.error(f"Failed to initialize scheduler: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

# Temporarily disabled automatic API scheduler to reduce API calls
# with app.app_context():
#     init_scheduler()
logging.info("Auto-update scheduler temporarily disabled to reduce API calls")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'True') == 'True')
