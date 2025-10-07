"""
Authentication Middleware for AI Crypto Trading Bot
PIN-based authentication with session management
Version: 1.0
"""

import os
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)

# Secret key for JWT tokens (should be loaded from environment)
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-secret-key-change-in-production')
SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))


class AuthenticationManager:
    """Manages authentication for the trading bot system"""

    def __init__(self, pin: Optional[str] = None):
        """
        Initialize authentication manager

        Args:
            pin: 6-digit PIN for authentication (loaded from env if not provided)
        """
        self.pin = pin or os.getenv('BOT_CONTROL_PIN', '123456')

        # Validate PIN format
        if not self.pin or len(self.pin) != 6 or not self.pin.isdigit():
            logger.error("Invalid PIN configuration. PIN must be 6 digits.")
            raise ValueError("BOT_CONTROL_PIN must be exactly 6 digits")

        # Hash the PIN for secure storage
        self.pin_hash = bcrypt.hashpw(self.pin.encode('utf-8'), bcrypt.gensalt())

        logger.info("Authentication manager initialized")

    def verify_pin(self, pin: str) -> bool:
        """
        Verify if provided PIN matches

        Args:
            pin: PIN to verify

        Returns:
            True if PIN matches, False otherwise
        """
        try:
            return bcrypt.checkpw(pin.encode('utf-8'), self.pin_hash)
        except Exception as e:
            logger.error(f"Error verifying PIN: {e}")
            return False

    def generate_token(self, user_id: str = 'admin') -> str:
        """
        Generate JWT token for authenticated user

        Args:
            user_id: User identifier

        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(minutes=SESSION_TIMEOUT_MINUTES),
            'iat': datetime.utcnow()
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return payload

        Args:
            token: JWT token string

        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None


# Global authentication manager instance
auth_manager = AuthenticationManager()


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for Flask routes

    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            return 'Protected content'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for Authorization header
        auth_header = request.headers.get('Authorization', '')

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = auth_manager.verify_token(token)

            if payload:
                # Token is valid, proceed with request
                request.user_id = payload.get('user_id')
                return f(*args, **kwargs)

        # Check for session-based auth
        if session.get('authenticated'):
            session_exp = session.get('expires_at')
            if session_exp and datetime.fromisoformat(session_exp) > datetime.utcnow():
                return f(*args, **kwargs)

        # Authentication failed
        return jsonify({
            'success': False,
            'error': 'Authentication required',
            'message': 'Please provide valid authentication credentials'
        }), 401

    return decorated_function


def optional_auth(f: Callable) -> Callable:
    """
    Decorator for routes that have optional authentication
    Sets request.authenticated to True/False
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request.authenticated = False
        request.user_id = None

        # Check for Authorization header
        auth_header = request.headers.get('Authorization', '')

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = auth_manager.verify_token(token)

            if payload:
                request.authenticated = True
                request.user_id = payload.get('user_id')

        # Check for session-based auth
        elif session.get('authenticated'):
            session_exp = session.get('expires_at')
            if session_exp and datetime.fromisoformat(session_exp) > datetime.utcnow():
                request.authenticated = True
                request.user_id = 'admin'

        return f(*args, **kwargs)

    return decorated_function


def login_endpoint():
    """
    Flask endpoint for PIN-based login

    Expected JSON body:
    {
        "pin": "123456"
    }

    Returns JWT token on success
    """
    try:
        data = request.get_json()

        if not data or 'pin' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing PIN',
                'message': 'PIN is required for authentication'
            }), 400

        pin = data['pin']

        # Verify PIN
        if auth_manager.verify_pin(pin):
            # Generate JWT token
            token = auth_manager.generate_token()

            # Set session
            session['authenticated'] = True
            session['expires_at'] = (datetime.utcnow() + timedelta(minutes=SESSION_TIMEOUT_MINUTES)).isoformat()

            logger.info("User authenticated successfully")

            return jsonify({
                'success': True,
                'message': 'Authentication successful',
                'token': token,
                'expires_in': SESSION_TIMEOUT_MINUTES * 60  # in seconds
            }), 200
        else:
            logger.warning("Failed authentication attempt")

            return jsonify({
                'success': False,
                'error': 'Invalid PIN',
                'message': 'The provided PIN is incorrect'
            }), 401

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': 'An error occurred during authentication'
        }), 500


def logout_endpoint():
    """
    Flask endpoint for logout
    Clears session data
    """
    session.clear()

    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


def check_auth_endpoint():
    """
    Flask endpoint to check authentication status
    """
    authenticated = False
    expires_in = 0

    # Check session
    if session.get('authenticated'):
        session_exp = session.get('expires_at')
        if session_exp:
            exp_time = datetime.fromisoformat(session_exp)
            if exp_time > datetime.utcnow():
                authenticated = True
                expires_in = int((exp_time - datetime.utcnow()).total_seconds())

    return jsonify({
        'authenticated': authenticated,
        'expires_in': expires_in
    }), 200
