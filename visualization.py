import os
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
from io import BytesIO
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
import pdfkit
from jinja2 import Environment, FileSystemLoader

def create_visualization_module():
    """Create and configure the visualization module for generating charts and graphs."""
    
    # Create a dictionary to store visualization-related functions
    visualization_module = {}
    
    def generate_language_distribution_chart(analysis_data, save_dir='static/img'):
        """Generate a pie chart showing the distribution of responses by language."""
        if 'language_distribution' not in analysis_data or not analysis_data['language_distribution']:
            return None
            
        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Get language distribution data
        languages = analysis_data['language_distribution'].keys()
        counts = analysis_data['language_distribution'].values()
        
        # Create pie chart
        plt.pie(counts, labels=languages, autopct='%1.1f%%', startangle=90, 
                colors=sns.color_palette('pastel'))
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.title('Response Distribution by Language', fontsize=16)
        
        # Save the chart
        filename = f"{save_dir}/language_distribution.png"
        plt.savefig(filename, bbox_inches='tight', dpi=300)
        plt.close()
        
        return filename
    
    def generate_responses_over_time_chart(analysis_data, save_dir='static/img'):
        """Generate a line chart showing responses over time."""
        if ('timestamp_analysis' not in analysis_data or 
            'responses_by_day' not in analysis_data['timestamp_analysis'] or 
            not analysis_data['timestamp_analysis']['responses_by_day']):
            return None
            
        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Create figure
        plt.figure(figsize=(12, 6))
        
        # Get time series data
        dates = [datetime.strptime(date_str, '%Y-%m-%d').date() 
                for date_str in analysis_data['timestamp_analysis']['responses_by_day'].keys()]
        counts = list(analysis_data['timestamp_analysis']['responses_by_day'].values())
        
        # Sort by date
        date_counts = sorted(zip(dates, counts))
        dates, counts = zip(*date_counts) if date_counts else ([], [])
        
        # Create line chart
        plt.plot(dates, counts, marker='o', linestyle='-', linewidth=2, markersize=8)
        plt.gcf().autofmt_xdate()  # Rotate date labels
        plt.title('Responses Over Time', fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Number of Responses', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Save the chart
        filename = f"{save_dir}/responses_over_time.png"
        plt.savefig(filename, bbox_inches='tight', dpi=300)
        plt.close()
        
        return filename
    
    def generate_question_charts(analysis_data, combined_data, save_dir='static/img'):
        """Generate charts for each question in the form."""
        if 'questions' not in analysis_data or not analysis_data['questions']:
            return {}
            
        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        chart_files = {}
        
        for question_data in analysis_data['questions']:
            question = question_data['question']
            
            # Skip questions with very few responses
            if question_data['response_count'] < 3:
                continue
                
            # For categorical/multiple choice questions
            if 'value_counts' in question_data and question_data['value_counts']:
                # Create figure
                plt.figure(figsize=(12, 6))
                
                # Get data
                labels = list(question_data['value_counts'].keys())
                values = list(question_data['value_counts'].values())
                
                # Limit number of categories shown for readability
                if len(labels) > 10:
                    # Sort by frequency
                    sorted_data = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
                    top_labels, top_values = zip(*sorted_data[:9])
                    
                    # Sum the rest
                    other_sum = sum(sorted_data[9:], key=lambda x: x[1])
                    
                    labels = list(top_labels) + ['Other']
                    values = list(top_values) + [other_sum]
                
                # Create horizontal bar chart
                plt.barh(labels, values, color=sns.color_palette('pastel'))
                plt.xlabel('Count', fontsize=12)
                plt.title(f'Responses for: {question}', fontsize=14)
                plt.grid(True, linestyle='--', alpha=0.7, axis='x')
                
                # Save the chart
                safe_question = question.replace(' ', '_').replace('?', '').replace('/', '_')[:30]
                filename = f"{save_dir}/question_{safe_question}.png"
                plt.savefig(filename, bbox_inches='tight', dpi=300)
                plt.close()
                
                chart_files[question] = filename
                
            # For numeric questions
            elif all(key in question_data for key in ['mean', 'median', 'min', 'max']):
                # Get the actual data from the combined dataset
                if 'data' in combined_data and question in combined_data['data'].columns:
                    numeric_data = combined_data['data'][question].dropna()
                    
                    if len(numeric_data) > 3:  # Only create histogram if we have enough data
                        # Create figure
                        plt.figure(figsize=(10, 6))
                        
                        # Create histogram
                        sns.histplot(numeric_data, kde=True)
                        plt.axvline(question_data['mean'], color='r', linestyle='--', label=f"Mean: {question_data['mean']:.2f}")
                        plt.axvline(question_data['median'], color='g', linestyle='-', label=f"Median: {question_data['median']:.2f}")
                        plt.title(f'Distribution for: {question}', fontsize=14)
                        plt.xlabel('Value', fontsize=12)
                        plt.ylabel('Frequency', fontsize=12)
                        plt.legend()
                        
                        # Save the chart
                        safe_question = question.replace(' ', '_').replace('?', '').replace('/', '_')[:30]
                        filename = f"{save_dir}/question_{safe_question}_hist.png"
                        plt.savefig(filename, bbox_inches='tight', dpi=300)
                        plt.close()
                        
                        chart_files[question] = filename
        
        return chart_files
    
    def generate_cross_tabulation(combined_data, analysis_data, save_dir='static/img'):
        """Generate cross-tabulation charts to show relationships between questions."""
        if 'data' not in combined_data or combined_data['data'].empty:
            return {}
            
        df = combined_data['data']
        
        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        chart_files = {}
        
        # Find categorical columns with reasonable number of categories
        categorical_cols = []
        for question_data in analysis_data['questions']:
            if ('value_counts' in question_data and 
                question_data['value_counts'] and 
                len(question_data['value_counts']) <= 6):
                categorical_cols.append(question_data['question'])
        
        # Generate cross-tabulations for pairs of categorical variables
        if len(categorical_cols) >= 2:
            # Limit to a reasonable number of combinations
            max_combinations = min(5, len(categorical_cols) * (len(categorical_cols) - 1) // 2)
            combinations_count = 0
            
            for i, col1 in enumerate(categorical_cols):
                if combinations_count >= max_combinations:
                    break
                    
                for col2 in categorical_cols[i+1:]:
                    if combinations_count >= max_combinations:
                        break
                        
                    if col1 in df.columns and col2 in df.columns:
                        # Create a cross-tabulation
                        cross_tab = pd.crosstab(df[col1], df[col2])
                        
                        # Skip if too sparse
                        if cross_tab.size <= 1 or cross_tab.empty:
                            continue
                            
                        # Create figure
                        plt.figure(figsize=(10, 8))
                        
                        # Create heatmap
                        sns.heatmap(cross_tab, annot=True, cmap='YlGnBu', fmt='d', cbar=True)
                        plt.title(f'Relationship between {col1} and {col2}', fontsize=14)
                        plt.tight_layout()
                        
                        # Save the chart
                        safe_name = f"{col1[:15]}_{col2[:15]}".replace(' ', '_').replace('?', '').replace('/', '_')
                        filename = f"{save_dir}/crosstab_{safe_name}.png"
                        plt.savefig(filename, bbox_inches='tight', dpi=300)
                        plt.close()
                        
                        chart_files[f"{col1} vs {col2}"] = filename
                        combinations_count += 1
        
        return chart_files
    
    def generate_all_visualizations(analysis_data, combined_data):
        """Generate all visualizations for the report."""
        visualizations = {}
        
        # Language distribution
        lang_chart = generate_language_distribution_chart(analysis_data)
        if lang_chart:
            visualizations['language_distribution'] = lang_chart
        
        # Responses over time
        time_chart = generate_responses_over_time_chart(analysis_data)
        if time_chart:
            visualizations['responses_over_time'] = time_chart
        
        # Question charts
        question_charts = generate_question_charts(analysis_data, combined_data)
        if question_charts:
            visualizations['questions'] = question_charts
        
        # Cross-tabulations
        cross_tabs = generate_cross_tabulation(combined_data, analysis_data)
        if cross_tabs:
            visualizations['cross_tabulations'] = cross_tabs
        
        return visualizations
    
    # Add functions to the visualization module
    visualization_module['generate_language_distribution_chart'] = generate_language_distribution_chart
    visualization_module['generate_responses_over_time_chart'] = generate_responses_over_time_chart
    visualization_module['generate_question_charts'] = generate_question_charts
    visualization_module['generate_cross_tabulation'] = generate_cross_tabulation
    visualization_module['generate_all_visualizations'] = generate_all_visualizations
    
    return visualization_module
