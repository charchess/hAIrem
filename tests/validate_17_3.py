import os

def validate_17_3():
    print("--- Validating 17.3: Crew Panel Enhancements ---")
    
    # Check agent.py for total_tokens and differentiation
    with open('apps/h-core/src/domain/agent.py', 'r') as f:
        content = f.read()
        if 'self.total_tokens = 0' in content and 'self.prompt_tokens = 0' in content:
            print("✅ Backend (Agent): Differentiated token tracking found.")
        else:
            print("❌ Backend (Agent): Token tracking MISSING or not differentiated.")

    # Check main.py for API exposure
    with open('apps/h-core/src/main.py', 'r') as f:
        content = f.read()
        if '"prompt_tokens": getattr(agent.ctx, \'prompt_tokens\', 0)' in content:
            print("✅ Backend (API): Differentiated tokens exposed.")
        else:
            print("❌ Backend (API): Differentiated tokens MISSING.")

    # Check renderer.js for UI display and robust update check
    with open('apps/a2ui/js/renderer.js', 'r') as f:
        content = f.read()
        if 'pTokens !== undefined && pTokens !== null' in content:
            print("✅ JS: Robust token update check found.")
        else:
            print("❌ JS: Robust token update check MISSING.")

if __name__ == "__main__":
    validate_17_3()

