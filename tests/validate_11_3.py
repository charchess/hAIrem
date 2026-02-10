import os

def check_transparency():
    agent_name = "test_model"
    base_path = f"apps/a2ui/public/assets/agents/{agent_name}/"
    expressions = ["neutral", "happy", "angry", "sad", "alert"]
    png_signature = b'\x89PNG\r\n\x1a\n'
    
    print(f"--- Validating transparency for {agent_name} ---")
    
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
                # Basic check for alpha channel in PNG
                # A PNG with alpha will have an 'IHDR' chunk (always first)
                # with Color Type 6 (RGBA) or 4 (Grayscale+Alpha)
                f.seek(8) # Skip signature
                chunk_len = int.from_bytes(f.read(4), 'big')
                chunk_type = f.read(4)
                if chunk_type == b'IHDR':
                    width = int.from_bytes(f.read(4), 'big')
                    height = int.from_bytes(f.read(4), 'big')
                    bit_depth = f.read(1)[0]
                    color_type = f.read(1)[0]
                    if color_type in [4, 6]:
                        print(f"PASS: {filename} has Alpha Channel (Color Type {color_type}).")
                    else:
                        print(f"FAIL: {filename} is NOT transparent (Color Type {color_type}).")
                        all_pass = False
        except Exception as e:
            print(f"FAIL: {filename} could not be read: {e}")
            all_pass = False
            
    return all_pass

if __name__ == "__main__":
    if check_transparency():
        print("\nSUMMARY: Transparency validation successful.")
        exit(0)
    else:
        print("\nSUMMARY: Transparency validation failed.")
        exit(1)
