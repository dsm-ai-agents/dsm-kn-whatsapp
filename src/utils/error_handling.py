class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv

from functools import wraps
from flask import jsonify
import logging

logger = logging.getLogger(__name__)

def handle_api_error(f):
    """
    Decorator to handle API errors and return proper JSON responses.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            logger.error(f"API Error in {f.__name__}: {e.message}")
            return jsonify({
                'status': 'error',
                'message': e.message
            }), e.status_code
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), 500
    return decorated_function 