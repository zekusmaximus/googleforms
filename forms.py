import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import os
from datetime import datetime

def create_forms_module(auth_module):
    """Create and configure the forms module for retrieving Google Form responses."""
    
    # Create a dictionary to store forms-related functions
    forms_module = {}
    
    def get_form_metadata(form_id):
        """Retrieve metadata about a Google Form."""
        credentials = auth_module['get_credentials']()
        if not credentials:
            return None
        
        try:
            # Build the Forms API service
            forms_service = auth_module['build_service'](credentials, 'forms', 'v1')
            
            # Get form metadata
            form = forms_service.forms().get(formId=form_id).execute()
            return form
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    
    def get_form_responses(form_id, language_code='en'):
        """Retrieve responses from a Google Form.
        
        Since the Forms API doesn't directly provide responses, we need to use the Sheets API
        to access the linked response spreadsheet.
        """
        credentials = auth_module['get_credentials']()
        if not credentials:
            return None
        
        try:
            # Build the Forms API service to get form metadata
            forms_service = auth_module['build_service'](credentials, 'forms', 'v1')
            
            # Get form metadata to find the response destination
            form = forms_service.forms().get(formId=form_id).execute()
            
            # Check if the form has a response destination
            if 'responseDestination' not in form:
                return {'error': 'This form does not have a response destination set.'}
            
            # Get the linked spreadsheet ID
            if 'spreadsheet' in form['responseDestination']:
                spreadsheet_id = form['responseDestination']['spreadsheet']['spreadsheetId']
            else:
                return {'error': 'This form does not save responses to a spreadsheet.'}
            
            # Build the Sheets API service
            sheets_service = auth_module['build_service'](credentials, 'sheets', 'v4')
            
            # Get spreadsheet metadata to find the sheet with responses
            spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            
            # Get the first sheet (usually contains responses)
            sheet_id = spreadsheet['sheets'][0]['properties']['sheetId']
            sheet_title = spreadsheet['sheets'][0]['properties']['title']
            
            # Get the response data
            response_range = f"'{sheet_title}'!A:Z"  # Get all columns
            response_data = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=response_range
            ).execute()
            
            # Convert to DataFrame
            if 'values' in response_data:
                headers = response_data['values'][0]
                data = response_data['values'][1:] if len(response_data['values']) > 1 else []
                
                # Handle case where some rows might have fewer columns than headers
                normalized_data = []
                for row in data:
                    if len(row) < len(headers):
                        row.extend([''] * (len(headers) - len(row)))
                    normalized_data.append(row)
                
                df = pd.DataFrame(normalized_data, columns=headers)
                
                # Add metadata
                df['form_id'] = form_id
                df['language'] = language_code
                df['form_title'] = form.get('info', {}).get('title', 'Unknown Form')
                
                return {
                    'success': True,
                    'data': df,
                    'metadata': {
                        'form_id': form_id,
                        'form_title': form.get('info', {}).get('title', 'Unknown Form'),
                        'language': language_code,
                        'response_count': len(df)
                    }
                }
            else:
                return {
                    'success': True,
                    'data': pd.DataFrame(),
                    'metadata': {
                        'form_id': form_id,
                        'form_title': form.get('info', {}).get('title', 'Unknown Form'),
                        'language': language_code,
                        'response_count': 0
                    }
                }
                
        except HttpError as error:
            print(f"An error occurred: {error}")
            return {'error': str(error)}
    
    def get_form_questions(form_id):
        """Retrieve questions from a Google Form."""
        credentials = auth_module['get_credentials']()
        if not credentials:
            return None
        
        try:
            # Build the Forms API service
            forms_service = auth_module['build_service'](credentials, 'forms', 'v1')
            
            # Get form metadata
            form = forms_service.forms().get(formId=form_id).execute()
            
            # Extract questions
            questions = []
            if 'items' in form:
                for item in form['items']:
                    if 'questionItem' in item:
                        question = {
                            'id': item['itemId'],
                            'title': item['title'],
                            'type': item['questionItem']['question']['questionType']
                        }
                        
                        # Get options for multiple choice questions
                        if 'choiceQuestion' in item['questionItem']['question']:
                            options = []
                            for option in item['questionItem']['question']['choiceQuestion']['options']:
                                options.append(option.get('value', ''))
                            question['options'] = options
                        
                        questions.append(question)
            
            return questions
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    
    def save_responses_to_file(responses, filename):
        """Save form responses to a CSV file."""
        if 'data' in responses and isinstance(responses['data'], pd.DataFrame):
            # Create directory if it doesn't exist
            os.makedirs('static/data', exist_ok=True)
            
            # Save to CSV
            file_path = f"static/data/{filename}"
            responses['data'].to_csv(file_path, index=False)
            return file_path
        return None
    
    # Add functions to the forms module
    forms_module['get_form_metadata'] = get_form_metadata
    forms_module['get_form_responses'] = get_form_responses
    forms_module['get_form_questions'] = get_form_questions
    forms_module['save_responses_to_file'] = save_responses_to_file
    
    return forms_module
