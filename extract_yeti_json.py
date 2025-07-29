#!/usr/bin/env python3
"""
Better JSON extractor for Yeti 500 Wireshark data.
"""

import csv
import json
import re

def clean_ascii_string(ascii_value):
    """
    Convert ASCII-converted colon-separated string back to readable text.
    
    Args:
        ascii_value: String like "H:e:l:l:o" or mixed ASCII/hex
        
    Returns:
        Clean readable string
    """
    if not ascii_value:
        return ""
    
    # Remove quotes that CSV might have added
    ascii_value = ascii_value.strip('"')
    
    # Split by colons
    parts = ascii_value.split(':')
    result = ""
    
    for part in parts:
        if len(part) == 1:
            # Single ASCII character
            result += part
        elif len(part) == 2:
            # Could be hex byte
            try:
                byte_val = int(part, 16)
                if 32 <= byte_val <= 126:  # Printable ASCII
                    result += chr(byte_val)
                else:
                    result += f"[{part}]"  # Non-printable byte
            except ValueError:
                result += part
        else:
            # Multi-character, keep as-is
            result += part
    
    return result

def extract_complete_json_messages(csv_file):
    """
    Extract complete JSON messages by combining fragments.
    """
    print(f"📖 Extracting JSON from: {csv_file}")
    print("=" * 80)
    
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            # Group messages by handle and try to reconstruct complete JSON
            handle_data = {}
            
            for row in reader:
                handle = row['handle']
                value = row['value']
                
                if handle not in handle_data:
                    handle_data[handle] = []
                
                # Convert to readable text
                text = clean_ascii_string(value)
                handle_data[handle].append(text)
            
            # Process each handle to find JSON messages
            json_count = 0
            
            for handle, texts in handle_data.items():
                print(f"\n🔍 Handle {handle}:")
                
                # Try to combine fragments into complete JSON
                combined_text = "".join(texts)
                
                # Look for JSON patterns
                json_matches = re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', combined_text)
                
                for match in json_matches:
                    json_str = match.group()
                    
                    # Clean up the JSON string
                    json_str = re.sub(r'([{,])([a-zA-Z_][a-zA-Z0-9_]*)', r'\1"\2"', json_str)  # Add quotes to keys
                    json_str = re.sub(r':([a-zA-Z_][a-zA-Z0-9_.-]*)', r':"\1"', json_str)  # Add quotes to string values
                    json_str = re.sub(r':"(\d+\.?\d*)"', r':\1', json_str)  # Remove quotes from numbers
                    json_str = re.sub(r':"\[([^\]]*)\]"', r':[\1]', json_str)  # Fix arrays
                    
                    try:
                        # Try to parse as JSON
                        json_obj = json.loads(json_str)
                        json_count += 1
                        
                        print(f"  📨 JSON Message {json_count}:")
                        print(f"     Raw: {json_str[:100]}...")
                        print(f"     Parsed:")
                        print(json.dumps(json_obj, indent=6))
                        print()
                        
                    except json.JSONDecodeError:
                        # Show raw text for manual inspection
                        if len(json_str) > 50:
                            print(f"  📄 Text Fragment: {json_str[:200]}...")
                
                # Also show readable text for non-JSON data
                readable_parts = [text for text in texts if text and not text.startswith('{')]
                if readable_parts:
                    print(f"  📝 Other Data: {' '.join(readable_parts)[:200]}...")
                    
            print(f"\n📊 Summary: Found {json_count} JSON messages")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function."""
    csv_file = "testing/Wireshark_filtered_export_ascii_converted.csv"
    extract_complete_json_messages(csv_file)

if __name__ == "__main__":
    main()
