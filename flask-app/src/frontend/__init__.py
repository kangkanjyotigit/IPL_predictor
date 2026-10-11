"""Frontend package"""

from flask import Blueprint

# Create Blueprint with proper configuration
frontend_bp = Blueprint('frontend', __name__, 
                      template_folder='templates',
                      static_folder='static')

# Import routes at the end to avoid circular imports
from . import routes
