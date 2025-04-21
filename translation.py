from googletrans import Translator
import pandas as pd
import os
import json
from time import sleep

def create_translation_module():
    """Create and configure the translation module for translating form responses."""
    
    # Create a dictionary to store translation-related functions
    translation_module = {}
    
    def translate_text(text, source_lang, target_lang='en'):
        """Translate text from source language to target language."""
        if not text or text.strip() == '':
            return text
        
        if source_lang == target_lang:
            return text
            
        try:
            translator = Translator()
            result = translator.translate(text, src=source_lang, dest=target_lang)
            
            # Add a small delay to avoid rate limiting
            sleep(0.2)
            
            return result.text
        except Exception as e:
            print(f"Translation error: {e}")
            # Return original text if translation fails
            return text
    
    def translate_dataframe(df, source_lang, target_lang='en', text_columns=None):
        """Translate text columns in a DataFrame."""
        if source_lang == target_lang:
            # No translation needed
            df['translated'] = False
            return df
            
        # Create a copy to avoid modifying the original
        translated_df = df.copy()
        translated_df['translated'] = True
        
        # If no specific columns are provided, try to identify text columns
        if not text_columns:
            # Exclude metadata columns and timestamp columns
            exclude_columns = ['form_id', 'language', 'form_title', 'Timestamp', 'translated']
            text_columns = [col for col in df.columns if col not in exclude_columns]
        
        # Translate each text column
        for column in text_columns:
            if column in translated_df.columns:
                translated_df[f'{column}_original'] = translated_df[column]
                translated_df[column] = translated_df[column].apply(
                    lambda x: translate_text(x, source_lang, target_lang) if pd.notna(x) else x
                )
        
        return translated_df
    
    def batch_translate_responses(responses_dict, target_lang='en'):
        """Translate responses from multiple forms in different languages."""
        translated_responses = {}
        
        for lang_code, response_data in responses_dict.items():
            if 'data' in response_data and isinstance(response_data['data'], pd.DataFrame):
                # Skip translation for already target language
                if lang_code == target_lang:
                    response_data['data']['translated'] = False
                    translated_responses[lang_code] = response_data
                else:
                    # Translate the DataFrame
                    translated_df = translate_dataframe(
                        response_data['data'], 
                        source_lang=lang_code, 
                        target_lang=target_lang
                    )
                    
                    # Update the response data with translated DataFrame
                    response_data['data'] = translated_df
                    response_data['metadata']['translated'] = True
                    translated_responses[lang_code] = response_data
        
        return translated_responses
    
    def save_translated_responses(translated_responses, base_filename):
        """Save translated responses to CSV files."""
        result_files = {}
        
        # Create directory if it doesn't exist
        os.makedirs('static/data', exist_ok=True)
        
        for lang_code, response_data in translated_responses.items():
            if 'data' in response_data and isinstance(response_data['data'], pd.DataFrame):
                # Generate filename
                filename = f"{base_filename}_{lang_code}_translated.csv"
                file_path = f"static/data/{filename}"
                
                # Save to CSV
                response_data['data'].to_csv(file_path, index=False)
                result_files[lang_code] = file_path
        
        return result_files
    
    # Add functions to the translation module
    translation_module['translate_text'] = translate_text
    translation_module['translate_dataframe'] = translate_dataframe
    translation_module['batch_translate_responses'] = batch_translate_responses
    translation_module['save_translated_responses'] = save_translated_responses
    
    return translation_module
