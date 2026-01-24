import os

def validate_assets():
    agent_name = "test_model"
    base_path = f"apps/a2ui/public/assets/agents/{agent_name}/"
    expressions = ["neutral", "happy", "angry", "sad", "alert"]
    png_signature = b'\x89PNG\r\n\x1a\n'
    
    print(f"--- Validating assets for {agent_name} (No-PIL mode) ---")
    
    if not os.path.exists(base_path):
        print(f"FAIL: Directory {base_path} not found.")
        return False

    all_pass = True
    for expr in expressions:
        filename = f"{agent_name}_{expr}_01.png"
        file_path = os.path.join(base_path, filename)
        
        if not os.path.exists(file_path):
            print(f"FAIL: {filename} missing.")
            all_pass = False
            continue
            
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if header != png_signature:
                    print(f"FAIL: {filename} is not a valid PNG (Bad Signature)")
                    all_pass = False
                else:
                    print(f"PASS: {filename} found and has valid PNG signature.")
        except Exception as e:
            print(f"FAIL: {filename} could not be read: {e}")
            all_pass = False
            
    return all_pass

if __name__ == "__main__":
    if validate_assets():
        print("\nSUMMARY: All assets validated successfully.")
        exit(0)
    else:
        print("\nSUMMARY: Validation failed.")
        exit(1)