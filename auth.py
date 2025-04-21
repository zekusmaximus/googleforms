import os
import json
import pickle
from flask import Flask, redirect, request, url_for, session, render_template, flash, send_file
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from config import CLIENT_SECRET_FILE, SCOPES, REDIRECT_URI, SECRET_KEY

def create_auth_module():
    """Create and configure the authentication module."""
    
    # Create a dictionary to store authentication-related functions
    auth_module = {}
    
    def get_credentials():
        """Get valid user credentials from storage or initiate OAuth2 flow."""
        if 'credentials' in session:
            credentials = Credentials(**session['credentials'])
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            return credentials
        return None
    
    def create_oauth_flow():
        """Create an OAuth 2.0 flow instance to manage the OAuth 2.0 Authorization Grant Flow."""
        if os.path.exists(CLIENT_SECRET_FILE):
            return Flow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
        else:
            # For development/testing without actual client_secret file
            # This would be replaced with proper error handling in production
            client_config = {
                "web": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                    "project_id": "form-translator-tool",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                    "redirect_uris": [REDIRECT_URI]
                }
            }
            return Flow.from_client_config(client_config, SCOPES, redirect_uri=REDIRECT_URI)
    
    def build_service(credentials, api_service, api_version):
        """Build a service object for interacting with the specified Google API."""
        return build(api_service, api_version, credentials=credentials)
    
    def is_authenticated():
        """Check if the user is authenticated."""
        return 'credentials' in session
    
    def clear_credentials():
        """Clear the stored credentials."""
        if 'credentials' in session:
            del session['credentials']
    
    # Add functions to the auth module
    auth_module['get_credentials'] = get_credentials
    auth_module['create_oauth_flow'] = create_oauth_flow
    auth_module['build_service'] = build_service
    auth_module['is_authenticated'] = is_authenticated
    auth_module['clear_credentials'] = clear_credentials
    
    return auth_module
