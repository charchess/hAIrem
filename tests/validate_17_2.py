import os

def validate_17_2():
    print("--- Validating 17.2: Control Panel ---")
    
    # Check main.py for system.config_update
    with open('apps/h-core/src/main.py', 'r') as f:
        content = f.read()
        if 'system.config_update' in content and 'log_handler.set_level' in content:
            print("✅ Backend: system.config_update handler found.")
        else:
            print("❌ Backend: system.config_update handler MISSING.")

    # Check index.html for select and status indicators
    with open('apps/a2ui/index.html', 'r') as f:
        content = f.read()
        if 'id="log-level-select"' in content and 'id="status-ws-admin"' in content:
            print("✅ Frontend: Admin UI elements found.")
        else:
            print("❌ Frontend: Admin UI elements MISSING.")

    # Check renderer.js for send call
    with open('apps/a2ui/js/renderer.js', 'r') as f:
        content = f.read()
        if "window.network.send('system.config_update'" in content:
            print("✅ JS: Config update emission found.")
        else:
            print("❌ JS: Config update emission MISSING.")

if __name__ == "__main__":
    validate_17_2()
