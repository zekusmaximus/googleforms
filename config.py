import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OAuth 2.0 Configuration
CLIENT_SECRET_FILE = os.getenv('CLIENT_SECRET_FILE', 'client_secret.json')
SCOPES = [
    'https://www.googleapis.com/auth/forms.body.readonly',
    'https://www.googleapis.com/auth/forms.responses.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]
API_SERVICE_NAME = 'forms'
API_VERSION = 'v1'
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/oauth2callback')

# Application Configuration
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

# Google Translate API Configuration
TRANSLATE_API_KEY = os.getenv('TRANSLATE_API_KEY', '')

# Languages supported by the application
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'pl': 'Polish'
}

# Report Configuration
REPORT_TITLE = os.getenv('REPORT_TITLE', 'Multi-Language Form Response Analysis')
COMPANY_NAME = os.getenv('COMPANY_NAME', 'Your Company')
REPORT_LOGO = os.getenv('REPORT_LOGO', 'static/img/logo.png')
