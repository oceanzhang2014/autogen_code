"""
Authentication utilities for the AutoGen Multi-Agent System.
"""
from functools import wraps
from flask import session, request, redirect, url_for, jsonify
import hashlib


# 硬编码的用户凭据（生产环境中应使用数据库和加密）
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("qw123456".encode()).hexdigest()


def hash_password(password: str) -> str:
    """
    Hash a password using SHA256.
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_credentials(username: str, password: str) -> bool:
    """
    Verify user credentials.
    
    Args:
        username (str): Username to verify
        password (str): Password to verify
        
    Returns:
        bool: True if credentials are valid
    """
    return (username == ADMIN_USERNAME and 
            hash_password(password) == ADMIN_PASSWORD_HASH)


def is_authenticated() -> bool:
    """
    Check if current session is authenticated.
    
    Returns:
        bool: True if user is logged in
    """
    return session.get('authenticated', False)


def login_required(f):
    """
    Decorator to require authentication for routes.
    
    Args:
        f: Function to wrap
        
    Returns:
        Wrapped function that checks authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            # For API requests, return JSON error
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            # For web requests, redirect to login
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def logout_user():
    """
    Log out the current user by clearing session.
    """
    session.pop('authenticated', None)
    session.pop('username', None)


def login_user(username: str):
    """
    Log in a user by setting session variables.
    
    Args:
        username (str): Username to log in
    """
    session['authenticated'] = True
    session['username'] = username