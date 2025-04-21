import os
import json
import shutil
from datetime import datetime
from flask import url_for, send_file
import uuid
import zipfile

def create_sharing_module():
    """Create and configure the sharing module for report distribution."""
    
    # Create a dictionary to store sharing-related functions
    sharing_module = {}
    
    def get_report_url(report_filename, report_type='html'):
        """Get the URL for accessing a report."""
        if report_type == 'html':
            return url_for('static', filename=f'reports/{report_filename}.html', _external=True)
        elif report_type == 'pdf':
            return url_for('static', filename=f'reports/{report_filename}.pdf', _external=True)
        else:
            return None
    
    def create_download_package(report_info, combined_data=None):
        """Create a downloadable package with all report files."""
        # Create a unique package ID
        package_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        package_name = f"form_analysis_{timestamp}_{package_id}"
        
        # Create directory for the package
        package_dir = f"static/packages/{package_name}"
        os.makedirs(package_dir, exist_ok=True)
        
        # Copy report files
        if 'html_path' in report_info and os.path.exists(report_info['html_path']):
            shutil.copy2(report_info['html_path'], f"{package_dir}/report.html")
        
        if 'pdf_path' in report_info and os.path.exists(report_info['pdf_path']):
            shutil.copy2(report_info['pdf_path'], f"{package_dir}/report.pdf")
        
        # Copy visualization images
        img_dir = "static/img"
        if os.path.exists(img_dir):
            os.makedirs(f"{package_dir}/img", exist_ok=True)
            for img_file in os.listdir(img_dir):
                if img_file.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    shutil.copy2(f"{img_dir}/{img_file}", f"{package_dir}/img/{img_file}")
        
        # Include data files
        if combined_data is not None and hasattr(combined_data, 'to_csv'):
            combined_data.to_csv(f"{package_dir}/combined_data.csv", index=False)
        
        # Create a README file
        readme_content = f"""# Form Response Analysis Package

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Contents

- report.html - Interactive HTML report with visualizations
- report.pdf - PDF version of the report
- img/ - Directory containing visualization images
- combined_data.csv - Combined form response data (if available)

## How to Use

1. To view the HTML report, open the report.html file in a web browser
2. To view the PDF report, open the report.pdf file with any PDF viewer
3. The combined_data.csv file can be opened with spreadsheet software for further analysis

## Report ID

{report_info.get('report_id', 'Unknown')}
"""
        
        with open(f"{package_dir}/README.md", 'w') as f:
            f.write(readme_content)
        
        # Create a zip file
        zip_path = f"static/packages/{package_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arcname)
        
        # Clean up the temporary directory
        shutil.rmtree(package_dir)
        
        return {
            'zip_path': zip_path,
            'package_name': package_name
        }
    
    def get_download_url(package_info):
        """Get the URL for downloading a package."""
        return url_for('static', filename=f"packages/{package_info['package_name']}.zip", _external=True)
    
    def create_shareable_link(report_info, expiration_days=30):
        """Create a shareable link for the report with optional expiration."""
        # In a real implementation, this would create a database entry with expiration
        # For this demo, we'll just return the direct URL
        
        # Create a unique sharing ID
        share_id = str(uuid.uuid4())[:12]
        timestamp = datetime.now().strftime('%Y%m%d')
        
        # Create sharing metadata
        sharing_info = {
            'share_id': share_id,
            'report_id': report_info.get('report_id'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'expires_at': (datetime.now() + datetime.timedelta(days=expiration_days)).strftime('%Y-%m-%d %H:%M:%S'),
            'html_path': report_info.get('html_path'),
            'pdf_path': report_info.get('pdf_path')
        }
        
        # In a real implementation, save this to a database
        # For this demo, we'll save it to a JSON file
        os.makedirs('static/shares', exist_ok=True)
        share_path = f"static/shares/{share_id}.json"
        with open(share_path, 'w') as f:
            json.dump(sharing_info, f, indent=2)
        
        # Return the sharing URL
        # In a real implementation, this would be a dedicated sharing endpoint
        return url_for('shared_report', share_id=share_id, _external=True)
    
    # Add functions to the sharing module
    sharing_module['get_report_url'] = get_report_url
    sharing_module['create_download_package'] = create_download_package
    sharing_module['get_download_url'] = get_download_url
    sharing_module['create_shareable_link'] = create_shareable_link
    
    return sharing_module
