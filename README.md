# Google Forms Multi-Language Tool

This web application allows you to:

1. Authenticate with Google to access Google Forms and Sheets
2. Retrieve responses from three identical Google Forms in different languages (English, Spanish, and Polish)
3. Translate non-English responses into English
4. Combine all responses into a single dataset
5. Generate comprehensive reports with visualizations
6. Output reports as downloadable PDFs and shareable web links

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- Google Cloud Platform account with OAuth 2.0 credentials
- Google Translate API key (optional, can use library without API key)

### Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   CLIENT_SECRET_FILE=client_secret.json
   REDIRECT_URI=http://localhost:5000/oauth2callback
   SECRET_KEY=your_secret_key
   TRANSLATE_API_KEY=your_google_translate_api_key
   ```
4. Place your Google OAuth client secret JSON file in the root directory

### Running the Application

```
python app.py
```

The application will be available at http://localhost:5000

## Features

- OAuth 2.0 authentication with Google
- Multi-language form response retrieval
- Automatic translation of non-English responses
- Data aggregation and analysis
- Visualization generation
- PDF report creation
- Web-based sharing

## Weekly Updates

The tool is designed to be rerun weekly to incorporate new responses.
