from flask import Flask, redirect, request, url_for, session, render_template, flash, send_file, jsonify, abort
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
import os
import json
from datetime import datetime
import uuid

# Import modules
from config import SECRET_KEY, SUPPORTED_LANGUAGES
from auth import create_auth_module
from forms import create_forms_module
from translation import create_translation_module
from aggregation import create_aggregation_module
from visualization import create_visualization_module
from report import create_report_module
from sharing import create_sharing_module

# Initialize Flask application
app = Flask(__name__)
app.secret_key = SECRET_KEY
bootstrap = Bootstrap(app)

# Create modules
auth_module = create_auth_module()
forms_module = create_forms_module(auth_module)
translation_module = create_translation_module()
aggregation_module = create_aggregation_module()
visualization_module = create_visualization_module()
report_module = create_report_module(visualization_module)
sharing_module = create_sharing_module()

# Forms for user input
class FormSelectionForm(FlaskForm):
    english_form_id = StringField('English Form ID', validators=[DataRequired()])
    spanish_form_id = StringField('Spanish Form ID', validators=[DataRequired()])
    polish_form_id = StringField('Polish Form ID', validators=[DataRequired()])
    report_title = StringField('Report Title', default='Multi-Language Form Response Analysis')
    submit = SubmitField('Retrieve and Process Responses')

# Routes
@app.route('/')
def index():
    """Home page route."""
    if not auth_module['is_authenticated']():
        return render_template('index.html', authenticated=False)
    return render_template('index.html', authenticated=True)

@app.route('/login')
def login():
    """Initiate the OAuth 2.0 authorization flow."""
    flow = auth_module['create_oauth_flow']()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    """Handle the OAuth 2.0 callback."""
    state = session.get('state', None)
    if state is None:
        return redirect(url_for('index'))
    
    flow = auth_module['create_oauth_flow']()
    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Dashboard page after successful authentication."""
    if not auth_module['is_authenticated']():
        return redirect(url_for('login'))
    
    form = FormSelectionForm()
    return render_template('dashboard.html', form=form)

@app.route('/process', methods=['POST'])
def process_forms():
    """Process the selected forms."""
    if not auth_module['is_authenticated']():
        return redirect(url_for('login'))
    
    form = FormSelectionForm()
    if form.validate_on_submit():
        # Get form IDs
        english_form_id = form.english_form_id.data
        spanish_form_id = form.spanish_form_id.data
        polish_form_id = form.polish_form_id.data
        report_title = form.report_title.data
        
        # Create a unique job ID
        job_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Step 1: Retrieve form responses
        responses = {}
        responses['en'] = forms_module['get_form_responses'](english_form_id, 'en')
        responses['es'] = forms_module['get_form_responses'](spanish_form_id, 'es')
        responses['pl'] = forms_module['get_form_responses'](polish_form_id, 'pl')
        
        # Save raw responses
        for lang, response in responses.items():
            if 'data' in response and not response['data'].empty:
                forms_module['save_responses_to_file'](response, f"{timestamp}_{job_id}_{lang}_raw.csv")
        
        # Step 2: Translate non-English responses
        translated_responses = translation_module['batch_translate_responses'](responses)
        
        # Save translated responses
        translation_module['save_translated_responses'](translated_responses, f"{timestamp}_{job_id}")
        
        # Step 3: Combine responses
        combined_data = aggregation_module['combine_responses'](translated_responses)
        
        # Save combined data
        aggregation_module['save_combined_data'](combined_data, f"{timestamp}_{job_id}")
        
        # Step 4: Analyze responses
        analysis = aggregation_module['analyze_responses'](combined_data)
        
        # Save analysis
        analysis_path = aggregation_module['save_analysis_results'](analysis, f"{timestamp}_{job_id}")
        
        # Step 5: Generate report
        report_info = report_module['generate_complete_report'](analysis, combined_data, report_title)
        
        # Step 6: Create download package
        package_info = sharing_module['create_download_package'](report_info, combined_data['data'])
        
        # Step 7: Create shareable link
        share_url = sharing_module['create_shareable_link'](report_info)
        
        # Store results in session for the results page
        session['last_report'] = {
            'job_id': job_id,
            'timestamp': timestamp,
            'report_info': report_info,
            'package_info': package_info,
            'share_url': share_url,
            'html_url': sharing_module['get_report_url'](report_info['report_filename'], 'html'),
            'pdf_url': sharing_module['get_report_url'](report_info['report_filename'], 'pdf'),
            'download_url': sharing_module['get_download_url'](package_info),
            'total_responses': combined_data['metadata']['total_responses'],
            'responses_by_language': combined_data['metadata']['responses_by_language']
        }
        
        return redirect(url_for('results'))
    
    return render_template('dashboard.html', form=form)

@app.route('/results')
def results():
    """Show results after processing."""
    if not auth_module['is_authenticated']():
        return redirect(url_for('login'))
    
    if 'last_report' not in session:
        flash('No report has been generated yet.', 'warning')
        return redirect(url_for('dashboard'))
    
    return render_template('results.html', report=session['last_report'])

@app.route('/download/<package_name>')
def download_package(package_name):
    """Download a report package."""
    if not auth_module['is_authenticated']():
        return redirect(url_for('login'))
    
    package_path = f"static/packages/{package_name}.zip"
    if os.path.exists(package_path):
        return send_file(package_path, as_attachment=True)
    else:
        abort(404)

@app.route('/shared/<share_id>')
def shared_report(share_id):
    """View a shared report."""
    # In a real implementation, this would check a database
    # For this demo, we'll check the JSON file
    share_path = f"static/shares/{share_id}.json"
    if not os.path.exists(share_path):
        abort(404)
    
    with open(share_path, 'r') as f:
        sharing_info = json.load(f)
    
    # Check if expired
    if 'expires_at' in sharing_info:
        expires_at = datetime.strptime(sharing_info['expires_at'], '%Y-%m-%d %H:%M:%S')
        if expires_at < datetime.now():
            return render_template('shared_expired.html')
    
    # Get the HTML report path
    html_path = sharing_info.get('html_path')
    if not html_path or not os.path.exists(html_path):
        abort(404)
    
    # Serve the HTML file directly
    return send_file(html_path)

@app.route('/logout')
def logout():
    """Log out the user by clearing credentials."""
    auth_module['clear_credentials']()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/about')
def about():
    """About page with information about the application."""
    return render_template('about.html')

if __name__ == '__main__':
    # Create necessary directories if they don't exist
    os.makedirs('static/img', exist_ok=True)
    os.makedirs('static/reports', exist_ok=True)
    os.makedirs('static/data', exist_ok=True)
    os.makedirs('static/packages', exist_ok=True)
    os.makedirs('static/shares', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Run the Flask application
    app.run(host='0.0.0.0', port=5000, debug=True)
