import pandas as pd
import os
import json
from datetime import datetime

def create_aggregation_module():
    """Create and configure the data aggregation module for combining form responses."""
    
    # Create a dictionary to store aggregation-related functions
    aggregation_module = {}
    
    def combine_responses(translated_responses):
        """Combine responses from multiple forms into a single dataset."""
        combined_df = pd.DataFrame()
        metadata = {
            'source_forms': [],
            'total_responses': 0,
            'responses_by_language': {},
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        for lang_code, response_data in translated_responses.items():
            if 'data' in response_data and isinstance(response_data['data'], pd.DataFrame) and not response_data['data'].empty:
                # Add to the combined DataFrame
                combined_df = pd.concat([combined_df, response_data['data']], ignore_index=True)
                
                # Update metadata
                metadata['source_forms'].append({
                    'form_id': response_data['metadata']['form_id'],
                    'form_title': response_data['metadata']['form_title'],
                    'language': response_data['metadata']['language'],
                    'response_count': response_data['metadata']['response_count']
                })
                
                metadata['responses_by_language'][lang_code] = response_data['metadata']['response_count']
                metadata['total_responses'] += response_data['metadata']['response_count']
        
        return {
            'data': combined_df,
            'metadata': metadata
        }
    
    def analyze_responses(combined_data):
        """Analyze the combined responses to extract insights."""
        if 'data' not in combined_data or combined_data['data'].empty:
            return {
                'error': 'No data available for analysis'
            }
            
        df = combined_data['data']
        metadata = combined_data['metadata']
        
        # Initialize analysis results
        analysis = {
            'summary': {
                'total_responses': metadata['total_responses'],
                'responses_by_language': metadata['responses_by_language']
            },
            'questions': [],
            'language_distribution': {},
            'timestamp_analysis': {}
        }
        
        # Language distribution
        if 'language' in df.columns:
            language_counts = df['language'].value_counts().to_dict()
            analysis['language_distribution'] = language_counts
        
        # Timestamp analysis if available
        if 'Timestamp' in df.columns:
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_any_dtype(df['Timestamp']):
                try:
                    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                except:
                    # If conversion fails, skip timestamp analysis
                    pass
            
            if pd.api.types.is_datetime64_any_dtype(df['Timestamp']):
                # Responses by day
                df['response_date'] = df['Timestamp'].dt.date
                responses_by_day = df['response_date'].value_counts().sort_index()
                
                analysis['timestamp_analysis'] = {
                    'first_response': df['Timestamp'].min().strftime('%Y-%m-%d'),
                    'last_response': df['Timestamp'].max().strftime('%Y-%m-%d'),
                    'responses_by_day': responses_by_day.to_dict()
                }
        
        # Analyze each question (column)
        exclude_columns = ['form_id', 'language', 'form_title', 'Timestamp', 'translated', 
                          'response_date', 'translated_original']
        
        for column in df.columns:
            if column in exclude_columns or column.endswith('_original'):
                continue
                
            # Basic column analysis
            question_analysis = {
                'question': column,
                'response_count': df[column].count(),
                'missing_count': df[column].isna().sum()
            }
            
            # For categorical/multiple choice questions
            if df[column].dtype == 'object':
                value_counts = df[column].value_counts().to_dict()
                question_analysis['value_counts'] = value_counts
                
                # Calculate percentages
                value_percentages = (df[column].value_counts(normalize=True) * 100).round(1).to_dict()
                question_analysis['value_percentages'] = value_percentages
            
            # For numeric questions
            elif pd.api.types.is_numeric_dtype(df[column]):
                question_analysis['mean'] = df[column].mean()
                question_analysis['median'] = df[column].median()
                question_analysis['min'] = df[column].min()
                question_analysis['max'] = df[column].max()
                question_analysis['std'] = df[column].std()
            
            analysis['questions'].append(question_analysis)
        
        return analysis
    
    def save_combined_data(combined_data, filename_base):
        """Save combined data and analysis to files."""
        # Create directory if it doesn't exist
        os.makedirs('static/data', exist_ok=True)
        
        result_files = {}
        
        # Save combined DataFrame
        if 'data' in combined_data and isinstance(combined_data['data'], pd.DataFrame):
            csv_path = f"static/data/{filename_base}_combined.csv"
            combined_data['data'].to_csv(csv_path, index=False)
            result_files['csv'] = csv_path
        
        # Save metadata and analysis as JSON
        if 'metadata' in combined_data:
            json_path = f"static/data/{filename_base}_metadata.json"
            with open(json_path, 'w') as f:
                json.dump(combined_data['metadata'], f, indent=2, default=str)
            result_files['metadata'] = json_path
        
        return result_files
    
    def save_analysis_results(analysis, filename_base):
        """Save analysis results to a JSON file."""
        # Create directory if it doesn't exist
        os.makedirs('static/data', exist_ok=True)
        
        json_path = f"static/data/{filename_base}_analysis.json"
        with open(json_path, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        return json_path
    
    # Add functions to the aggregation module
    aggregation_module['combine_responses'] = combine_responses
    aggregation_module['analyze_responses'] = analyze_responses
    aggregation_module['save_combined_data'] = save_combined_data
    aggregation_module['save_analysis_results'] = save_analysis_results
    
    return aggregation_module
