"""
Script to fix template URL references by removing 'frontend.' prefix from url_for calls
"""
import os
import re

def fix_templates(templates_dir):
    """Fix all templates in the given directory"""
    pattern = r"url_for\('frontend\.([^']+)'"
    replacement = r"url_for('\1'"
    
    fixed_count = 0
    
    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if there are any matches
                if re.search(pattern, content):
                    # Replace all instances
                    new_content = re.sub(pattern, replacement, content)
                    
                    # Write the changes back to the file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    fixed_count += 1
                    print(f"Fixed {file_path}")
    
    print(f"Fixed {fixed_count} template files")

if __name__ == "__main__":
    templates_dir = os.path.join('src', 'frontend', 'templates')
    fix_templates(templates_dir)
