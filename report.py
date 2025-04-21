import os
import json
import pandas as pd
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import pdfkit
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
import base64
from io import BytesIO
import uuid

def create_report_module(visualization_module):
    """Create and configure the report generation module."""
    
    # Create a dictionary to store report-related functions
    report_module = {}
    
    def generate_html_report(analysis_data, combined_data, visualizations, report_title="Form Response Analysis Report"):
        """Generate an HTML report with visualizations."""
        # Create directories if they don't exist
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static/reports', exist_ok=True)
        
        # Create a unique report ID
        report_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"report_{timestamp}_{report_id}"
        
        # Create HTML template if it doesn't exist
        create_report_template()
        
        # Prepare data for the template
        template_data = {
            'report_title': report_title,
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_responses': analysis_data['summary']['total_responses'],
                'responses_by_language': analysis_data['summary']['responses_by_language']
            },
            'visualizations': {},
            'questions': [],
            'timestamp_analysis': {}
        }
        
        # Add language distribution chart
        if 'language_distribution' in visualizations:
            template_data['visualizations']['language_distribution'] = os.path.relpath(
                visualizations['language_distribution'], 'static')
        
        # Add responses over time chart
        if 'responses_over_time' in visualizations:
            template_data['visualizations']['responses_over_time'] = os.path.relpath(
                visualizations['responses_over_time'], 'static')
        
        # Add timestamp analysis
        if 'timestamp_analysis' in analysis_data:
            template_data['timestamp_analysis'] = {
                'first_response': analysis_data['timestamp_analysis'].get('first_response', 'N/A'),
                'last_response': analysis_data['timestamp_analysis'].get('last_response', 'N/A')
            }
        
        # Add question analysis and charts
        for question_data in analysis_data['questions']:
            question = question_data['question']
            question_info = {
                'question': question,
                'response_count': question_data['response_count'],
                'missing_count': question_data['missing_count']
            }
            
            # Add chart if available
            if ('questions' in visualizations and 
                question in visualizations['questions']):
                question_info['chart'] = os.path.relpath(
                    visualizations['questions'][question], 'static')
            
            # Add value counts for categorical questions
            if 'value_counts' in question_data:
                question_info['is_categorical'] = True
                question_info['values'] = []
                
                # Sort by frequency
                sorted_items = sorted(
                    question_data['value_percentages'].items(), 
                    key=lambda x: question_data['value_counts'].get(x[0], 0), 
                    reverse=True
                )
                
                for value, percentage in sorted_items:
                    count = question_data['value_counts'].get(value, 0)
                    question_info['values'].append({
                        'value': value,
                        'count': count,
                        'percentage': percentage
                    })
            
            # Add statistics for numeric questions
            elif all(key in question_data for key in ['mean', 'median', 'min', 'max']):
                question_info['is_numeric'] = True
                question_info['mean'] = round(question_data['mean'], 2)
                question_info['median'] = round(question_data['median'], 2)
                question_info['min'] = round(question_data['min'], 2)
                question_info['max'] = round(question_data['max'], 2)
                question_info['std'] = round(question_data['std'], 2)
            
            template_data['questions'].append(question_info)
        
        # Add cross-tabulation charts
        if 'cross_tabulations' in visualizations:
            template_data['visualizations']['cross_tabulations'] = []
            for title, chart_path in visualizations['cross_tabulations'].items():
                template_data['visualizations']['cross_tabulations'].append({
                    'title': title,
                    'chart': os.path.relpath(chart_path, 'static')
                })
        
        # Render the template
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report_template.html')
        html_content = template.render(**template_data)
        
        # Save the HTML report
        html_path = f"static/reports/{report_filename}.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        return {
            'html_path': html_path,
            'report_id': report_id,
            'report_filename': report_filename
        }
    
    def generate_pdf_report(html_report_path, output_filename=None):
        """Generate a PDF report from the HTML report."""
        if not output_filename:
            output_filename = html_report_path.replace('.html', '.pdf')
        
        try:
            # Configure pdfkit options
            options = {
                'page-size': 'Letter',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': 'UTF-8',
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            # Convert HTML to PDF
            pdfkit.from_file(html_report_path, output_filename, options=options)
            
            return output_filename
        except Exception as e:
            print(f"Error generating PDF: {e}")
            
            # Fallback to a simpler PDF generation if pdfkit fails
            return generate_simple_pdf_report(html_report_path, output_filename)
    
    def generate_simple_pdf_report(html_report_path, output_filename=None):
        """Generate a simpler PDF report using ReportLab as a fallback."""
        if not output_filename:
            output_filename = html_report_path.replace('.html', '_simple.pdf')
        
        # Extract data from the HTML report path
        report_id = os.path.basename(html_report_path).split('_')[2]
        
        # Create a PDF document
        doc = SimpleDocTemplate(output_filename, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30
        )
        
        heading_style = ParagraphStyle(
            'Heading1',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12
        )
        
        subheading_style = ParagraphStyle(
            'Heading2',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        )
        
        normal_style = styles['Normal']
        
        # Build the PDF content
        content = []
        
        # Title
        content.append(Paragraph("Form Response Analysis Report", title_style))
        content.append(Paragraph(f"Report ID: {report_id}", normal_style))
        content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Add visualizations if available
        img_dir = os.path.dirname(html_report_path).replace('reports', 'img')
        
        # Look for language distribution chart
        lang_dist_path = os.path.join(img_dir, 'language_distribution.png')
        if os.path.exists(lang_dist_path):
            content.append(Paragraph("Language Distribution", heading_style))
            content.append(Image(lang_dist_path, width=6*inch, height=4*inch))
            content.append(Spacer(1, 0.25*inch))
        
        # Look for responses over time chart
        time_chart_path = os.path.join(img_dir, 'responses_over_time.png')
        if os.path.exists(time_chart_path):
            content.append(Paragraph("Responses Over Time", heading_style))
            content.append(Image(time_chart_path, width=6*inch, height=3*inch))
            content.append(Spacer(1, 0.25*inch))
        
        # Add a note about the simple format
        content.append(Paragraph("Note: This is a simplified PDF report. For the full interactive report, please refer to the HTML version.", normal_style))
        
        # Build and save the PDF
        doc.build(content)
        
        return output_filename
    
    def create_report_template():
        """Create the HTML template for the report."""
        template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #ddd;
        }
        .header h1 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .header p {
            color: #7f8c8d;
        }
        .section {
            margin-bottom: 40px;
        }
        .section h2 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .section h3 {
            color: #2c3e50;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        .summary-box {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .summary-item {
            margin-bottom: 10px;
        }
        .summary-label {
            font-weight: bold;
            display: inline-block;
            width: 200px;
        }
        .visualization {
            text-align: center;
            margin: 30px 0;
        }
        .visualization img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .question-box {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .question-title {
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        .question-stats {
            margin-bottom: 15px;
            font-size: 14px;
            color: #7f8c8d;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .numeric-stats {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 15px;
        }
        .stat-item {
            flex: 1;
            min-width: 120px;
            background-color: #e8f4f8;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
        }
        .stat-label {
            font-size: 14px;
            color: #7f8c8d;
        }
        .cross-tab-section {
            display: flex;
            flex-wrap: wrap;
            gap: 30px;
            justify-content: center;
        }
        .cross-tab-item {
            flex: 1;
            min-width: 300px;
            max-width: 500px;
            margin-bottom: 30px;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 14px;
        }
        @media print {
            .visualization img {
                max-width: 100%;
                page-break-inside: avoid;
            }
            .question-box {
                page-break-inside: avoid;
            }
            .section {
                page-break-before: always;
            }
            .header {
                page-break-before: avoid;
                page-break-after: avoid;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ report_title }}</h1>
        <p>Generated on: {{ generation_date }}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div class="summary-box">
            <div class="summary-item">
                <span class="summary-label">Total Responses:</span>
                <span>{{ summary.total_responses }}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Languages:</span>
                <span>
                    {% for lang, count in summary.responses_by_language.items() %}
                        {{ lang }} ({{ count }} responses){% if not loop.last %}, {% endif %}
                    {% endfor %}
                </span>
            </div>
            {% if timestamp_analysis %}
            <div class="summary-item">
                <span class="summary-label">First Response:</span>
                <span>{{ timestamp_analysis.first_response }}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Last Response:</span>
                <span>{{ timestamp_analysis.last_response }}</span>
            </div>
            {% endif %}
        </div>

        {% if visualizations.language_distribution %}
        <div class="visualization">
            <h3>Response Distribution by Language</h3>
            <img src="/{{ visualizations.language_distribution }}" alt="Language Distribution Chart">
        </div>
        {% endif %}

        {% if visualizations.responses_over_time %}
        <div class="visualization">
            <h3>Responses Over Time</h3>
            <img src="/{{ visualizations.responses_over_time }}" alt="Responses Over Time Chart">
        </div>
        {% endif %}
    </div>

    <div class="section">
        <h2>Question Analysis</h2>
        
        {% for question in questions %}
        <div class="question-box">
            <d
(Content truncated due to size limit. Use line ranges to read in chunks)