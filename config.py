import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env
load_dotenv(BASE_DIR / '.env')


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'finwise-ai-insecure-dev-key-change-in-production')
    
    # Database configuration with PostgreSQL compatibility fix
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Default SQLite database in instance/ directory
        instance_dir = BASE_DIR / 'instance'
        instance_dir.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{instance_dir / 'finwise.db'}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security and Session Cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() in ('true', '1', 't')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Gemini AI Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash').strip()
    
    # Financial Settings
    DEFAULT_CURRENCY_SYMBOL = os.environ.get('CURRENCY_SYMBOL', '₹')
    DEFAULT_CURRENCY_CODE = os.environ.get('CURRENCY_CODE', 'INR')
    
    # Items per page for pagination
    ITEMS_PER_PAGE = 15


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key-do-not-use-in-prod'
    GEMINI_API_KEY = ''  # Forces fallback advisor for offline automated tests


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
