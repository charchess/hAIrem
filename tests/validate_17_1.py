import os

def check_file_content(file_path, search_strings):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
        
    all_found = True
    for s in search_strings:
        if s not in content:
            print(f"❌ Missing string in {file_path}: '{s}'")
            all_found = False
    
    if all_found:
        print(f"✅ {file_path} checks passed.")
    return all_found

def validate_ui_structure():
    print("--- Validating UI Structure for Story 17.1 ---")
    
    # Check index.html
    html_checks = [
        'id="nav-admin"',
        'id="nav-crew"',
        'id="admin-panel"',
        'id="crew-panel"',
        'class="hidden panel-overlay"'
    ]
    check_file_content('apps/a2ui/index.html', html_checks)

    # Check renderer.js
    js_checks = [
        "switchView('admin')",
        "switchView('crew')",
        "this.layers.adminPanel",
        "document.getElementById('nav-admin').onclick",
        "renderer.switchView('stage')" # Escape/Click outside
    ]
    check_file_content('apps/a2ui/js/renderer.js', js_checks)

    # Check style.css
    css_checks = [
        ".panel-overlay",
        ".panel-header"
    ]
    check_file_content('apps/a2ui/style.css', css_checks)

if __name__ == "__main__":
    validate_ui_structure()
