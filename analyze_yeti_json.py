#!/usr/bin/env python3
"""
Extract and format JSON data from the ASCII-converted Wireshark export.
"""

import csv
import json
import re

def extract_json_from_row(value_str):
    """
    Extract JSON string from ASCII-converted value field.
    
    Args:
        value_str: ASCII-converted value string with colons between characters
        
    Returns:
        Reconstructed string, or None if not convertible
    """
    if not value_str or ':' not in value_str:
        return None
        
    # Split by colons and join ASCII characters, keep hex bytes as-is
    parts = value_str.split(':')
    reconstructed = ""
    
    for part in parts:
        part = part.strip('"')  # Remove any quotes added by CSV
        if len(part) == 1:
            # Single character (converted ASCII)
            reconstructed += part
        elif len(part) == 2 and all(c in '0123456789ABCDEFabcdef' for c in part):
            # Hex byte - convert to character if possible
            try:
                byte_val = int(part, 16)
                if 32 <= byte_val <= 126:
                    reconstructed += chr(byte_val)
                else:
                    reconstructed += f"\\x{part}"
            except ValueError:
                reconstructed += part
        else:
            # Multi-character string, keep as-is
            reconstructed += part
    
    return reconstructed

def analyze_converted_csv(input_file):
    """
    Analyze the ASCII-converted CSV file and extract readable JSON.
    
    Args:
        input_file: Path to the ASCII-converted CSV file
    """
    print(f"📖 Analyzing: {input_file}")
    print("=" * 80)
    
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            json_messages = []
            
            for i, row in enumerate(reader):
                handle = row['handle']
                value = row['value']
                
                # Try to extract readable text
                reconstructed = extract_json_from_row(value)
                
                if reconstructed and ('{' in reconstructed or 'gzy5c' in reconstructed):
                    print(f"\n📨 Message {i+1} - Handle: {handle}")
                    print(f"Raw: {value[:100]}{'...' if len(value) > 100 else ''}")
                    print(f"Text: {reconstructed}")
                    
                    # Try to parse as JSON if it looks like JSON
                    if reconstructed.strip().startswith('{') and reconstructed.strip().endswith('}'):
                        try:
                            json_obj = json.loads(reconstructed)
                            print(f"📋 Formatted JSON:")
                            print(json.dumps(json_obj, indent=2))
                            json_messages.append({
                                'handle': handle,
                                'message_id': i+1,
                                'json': json_obj
                            })
                        except json.JSONDecodeError as e:
                            print(f"⚠️  JSON parsing failed: {e}")
                    
                    print("-" * 60)
            
            print(f"\n📊 Summary:")
            print(f"Total JSON messages found: {len(json_messages)}")
            
            # Show message types
            if json_messages:
                methods = set()
                for msg in json_messages:
                    if 'method' in msg['json']:
                        methods.add(msg['json']['method'])
                
                if methods:
                    print(f"Message types: {', '.join(sorted(methods))}")
                
    except Exception as e:
        print(f"Error analyzing file: {e}")

def main():
    """Main function."""
    input_file = "testing/Wireshark_filtered_export_ascii_converted.csv"
    analyze_converted_csv(input_file)

if __name__ == "__main__":
    main()
