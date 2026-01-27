import os

def validate_17_4():
    print("--- Validating 17.4: Visual Addressing ---")
    
    # Check index.html for select box
    with open('apps/a2ui/index.html', 'r') as f:
        content = f.read()
        if 'id="target-agent-select"' in content:
            print("✅ Frontend: target-agent-select found in HTML.")
        else:
            print("❌ Frontend: target-agent-select MISSING in HTML.")

    # Check renderer.js for population and usage
    with open('apps/a2ui/js/renderer.js', 'r') as f:
        content = f.read()
        if 'updateAgentCards' in content and 'target-agent-select' in content and 'window.network.sendUserMessage(text, target)' in content:
            print("✅ JS: Target selection logic found.")
        else:
            print("❌ JS: Target selection logic MISSING or incomplete.")

    # Check network.js for parameter support
    with open('apps/a2ui/js/network.js', 'r') as f:
        content = f.read()
        if 'sendUserMessage(text, target = "broadcast")' in content:
            print("✅ JS (Network): sendUserMessage supports target.")
        else:
            print("❌ JS (Network): sendUserMessage MISSING target param.")

if __name__ == "__main__":
    validate_17_4()
