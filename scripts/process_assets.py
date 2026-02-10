#!/usr/bin/env python3
import os
import sys
import argparse

try:
    from rembg import remove
    from PIL import Image
    import io
except ImportError:
    print("Error: Missing dependencies. Please install them using:")
    print("pip install rembg pillow onnxruntime")
    sys.exit(1)

def process_image(input_path, output_path):
    """Removes background from a single image."""
    try:
        with open(input_path, 'rb') as i:
            input_data = i.read()
            # rembg.remove handles the background removal logic
            output_data = remove(input_data)
            
            with open(output_path, 'wb') as o:
                o.write(output_data)
        return True
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="hAIrem Asset Post-Processor (Background Removal)")
    parser.add_argument("input_dir", help="Directory containing raw PNGs")
    parser.add_argument("--output_dir", help="Directory to save processed PNGs (default: input_dir/processed)")
    
    args = parser.parse_args()
    
    input_dir = args.input_dir
    output_dir = args.output_dir or os.path.join(input_dir, "processed")
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} does not exist.")
        sys.exit(1)
        
    os.makedirs(output_dir, exist_ok=True)
    
    files = [f for f in os.listdir(input_dir) if f.lower().endswith('.png')]
    print(f"Found {len(files)} PNG files in {input_dir}. Starting processing...")
    
    success_count = 0
    for filename in files:
        # Avoid re-processing already processed files if output_dir is a subfolder
        if "processed" in filename.lower():
            continue
            
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        print(f"Processing {filename}...")
        if process_image(input_path, output_path):
            success_count += 1
            
    print(f"\nProcessing complete. Successfully cleaned {success_count} assets.")
    print(f"Output location: {output_dir}")

if __name__ == "__main__":
    main()
