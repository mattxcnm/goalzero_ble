#!/usr/bin/env python3
"""
Correlate Handle 0x0008 messages with JSON messages to understand the pattern.
"""

import csv
import json
import re

def clean_ascii_string(ascii_value):
    """Convert ASCII-converted colon-separated string back to readable text."""
    if not ascii_value:
        return ""
    
    ascii_value = ascii_value.strip('"')
    parts = ascii_value.split(':')
    result = ""
    
    for part in parts:
        if len(part) == 1:
            result += part
        elif len(part) == 2:
            try:
                byte_val = int(part, 16)
                if 32 <= byte_val <= 126:
                    result += chr(byte_val)
                else:
                    result += f"[{part}]"
            except ValueError:
                result += part
        else:
            result += part
    
    return result

def analyze_correlation(csv_file):
    """
    Analyze the correlation between 0x0008 messages and JSON data.
    """
    print("🔗 Correlating Handle 0x0008 with JSON Messages")
    print("=" * 60)
    
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            rows = list(reader)
            
        # Find 0x0008 messages and their context
        handle_0x0008_indices = []
        for i, row in enumerate(rows):
            if row['handle'] == '0x0008':
                handle_0x0008_indices.append(i)
        
        print(f"Found {len(handle_0x0008_indices)} Handle 0x0008 messages\n")
        
        # Analyze each 0x0008 message with its surrounding context
        for i, idx in enumerate(handle_0x0008_indices):
            print(f"🔍 Analysis {i+1}: Handle 0x0008 at row {idx+1}")
            
            # Get the 0x0008 message
            handle_msg = rows[idx]
            print(f"   Value: {handle_msg['value']}")
            
            # Get last byte and convert to decimal
            last_byte = None
            try:
                parts = handle_msg['value'].split(':')
                if len(parts) == 4:
                    last_part = parts[3]
                    if len(last_part) == 1:
                        last_byte = ord(last_part)
                    elif len(last_part) == 2:
                        last_byte = int(last_part, 16)
                    
                    if last_byte is not None:
                        print(f"   Last byte: {last_byte} (0x{last_byte:02X})")
            except:
                print(f"   Last byte: Could not decode")
            
            # Look for preceding and following JSON messages
            json_before = []
            json_after = []
            
            # Check 5 messages before
            for j in range(max(0, idx-5), idx):
                if rows[j]['handle'] == '0x0003':
                    text = clean_ascii_string(rows[j]['value'])
                    if '{' in text or 'method' in text or 'result' in text:
                        json_before.append((j+1, text[:100] + '...' if len(text) > 100 else text))
            
            # Check 5 messages after  
            for j in range(idx+1, min(len(rows), idx+6)):
                if rows[j]['handle'] == '0x0003':
                    text = clean_ascii_string(rows[j]['value'])
                    if '{' in text or 'method' in text or 'result' in text:
                        json_after.append((j+1, text[:100] + '...' if len(text) > 100 else text))
            
            # Show context
            if json_before:
                print(f"   📨 JSON Before:")
                for row_num, text in json_before[-2:]:  # Show last 2 before
                    print(f"      Row {row_num}: {text}")
            
            if json_after:
                print(f"   📨 JSON After:")
                for row_num, text in json_after[:2]:  # Show first 2 after
                    print(f"      Row {row_num}: {text}")
            
            # Try to find JSON message length correlation
            if json_after and last_byte is not None:
                # Get the next complete JSON message
                next_json_rows = []
                for j in range(idx+1, min(len(rows), idx+10)):
                    if rows[j]['handle'] == '0x0003':
                        next_json_rows.append(rows[j]['value'])
                
                if next_json_rows:
                    # Combine all JSON parts
                    combined_json = ''.join([clean_ascii_string(part) for part in next_json_rows])
                    
                    # Look for complete JSON objects
                    json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', combined_json)
                    
                    if json_objects:
                        json_obj = json_objects[0]
                        json_length = len(json_obj)
                        print(f"   📏 Next JSON length: {json_length} chars")
                        print(f"   🔢 Length correlation: 0x0008 value {last_byte} vs JSON length {json_length}")
                        
                        if abs(last_byte - json_length) < 5:
                            print(f"   ✅ POSSIBLE LENGTH MATCH! (difference: {abs(last_byte - json_length)})")
                        else:
                            print(f"   ❌ No length correlation (difference: {abs(last_byte - json_length)})")
            
            print("-" * 50)
        
        print(f"\n📊 Summary Analysis:")
        print("=" * 30)
        
        # Collect all last bytes and try to find patterns
        last_bytes = []
        for idx in handle_0x0008_indices:
            try:
                parts = rows[idx]['value'].split(':')
                if len(parts) == 4:
                    last_part = parts[3]
                    if len(last_part) == 1:
                        last_bytes.append(ord(last_part))
                    elif len(last_part) == 2:
                        last_bytes.append(int(last_part, 16))
            except:
                pass
        
        if last_bytes:
            print(f"All last byte values: {last_bytes}")
            unique_values = sorted(set(last_bytes))
            print(f"Unique values: {unique_values}")
            
            # Convert to hex for better readability
            hex_values = [f"0x{b:02X}" for b in unique_values]
            print(f"In hex: {hex_values}")
            
            print(f"\n💡 Final Hypothesis:")
            print("Handle 0x0008 appears to be a **message length indicator**")
            print("- Format: 00:00:00:XX where XX is the length")
            print("- Sent before JSON messages on handle 0x0003")
            print("- Helps the receiver know how much data to expect")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function."""
    csv_file = "testing/Wireshark_filtered_decode.csv"
    analyze_correlation(csv_file)

if __name__ == "__main__":
    main()
