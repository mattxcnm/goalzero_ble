#!/usr/bin/env python3
"""
Comprehensive analysis of Yeti 500 JSON protocol from Wireshark capture.
"""

import csv
import json
import re
from typing import Dict, List, Any

def clean_ascii_string(ascii_value: str) -> str:
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

def extract_all_json_messages(csv_file: str) -> List[Dict[str, Any]]:
    """Extract all JSON messages from the CSV file."""
    print("📖 Extracting all JSON messages from Wireshark capture...")
    
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            rows = list(reader)
        
        # Group 0x0003 messages and reconstruct JSON
        json_fragments = []
        current_fragments = []
        
        for i, row in enumerate(rows):
            if row['handle'] == '0x0003':
                text = clean_ascii_string(row['value'])
                current_fragments.append(text)
                
                # Check if this completes a JSON message
                combined = ''.join(current_fragments)
                if combined.count('{') > 0 and combined.count('{') == combined.count('}'):
                    json_fragments.append({
                        'row': i + 1,
                        'combined_text': combined,
                        'fragments': current_fragments.copy()
                    })
                    current_fragments = []
            elif current_fragments and row['handle'] != '0x0003':
                # Non-0x0003 message, reset current fragments
                current_fragments = []
        
        # Parse JSON messages
        parsed_messages = []
        for frag in json_fragments:
            combined = frag['combined_text']
            
            # Try to extract valid JSON objects
            json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', combined)
            
            for json_str in json_objects:
                try:
                    # Clean up JSON string for parsing
                    cleaned = json_str
                    
                    # Try basic parsing first
                    if cleaned.startswith('{') and cleaned.endswith('}'):
                        # Manual parsing for the specific format
                        message = parse_yeti_json(cleaned)
                        if message:
                            parsed_messages.append({
                                'row': frag['row'],
                                'raw_json': json_str,
                                'parsed': message
                            })
                            
                except Exception as e:
                    print(f"Failed to parse JSON at row {frag['row']}: {e}")
                    print(f"Raw: {json_str[:100]}...")
        
        return parsed_messages
        
    except Exception as e:
        print(f"Error extracting JSON: {e}")
        return []

def parse_yeti_json(json_str: str) -> Dict[str, Any] | None:
    """Parse Yeti-specific JSON format."""
    try:
        # The JSON is in a specific format, let's manually parse key components
        message = {}
        
        # Extract ID
        id_match = re.search(r'"?id"?(\d+)', json_str)
        if id_match:
            message['id'] = int(id_match.group(1))
        
        # Extract method
        method_match = re.search(r'"?method"?"?([^"]+)"?', json_str)
        if method_match:
            message['method'] = method_match.group(1).strip('"')
        
        # Extract src
        src_match = re.search(r'"?src"?"?([^"]+)"?', json_str)
        if src_match:
            message['src'] = src_match.group(1).strip('"')
        
        # Extract result if present
        if 'result' in json_str:
            message['type'] = 'response'
            # Try to extract body content
            if 'body' in json_str:
                message['has_body'] = True
        else:
            message['type'] = 'request'
        
        # Extract specific data fields for different message types
        if message.get('method') == 'status':
            extract_status_fields(json_str, message)
        elif message.get('method') == 'device':
            extract_device_fields(json_str, message)
        elif message.get('method') == 'config':
            extract_config_fields(json_str, message)
        
        return message
        
    except Exception as e:
        print(f"Parse error: {e}")
        return None

def extract_status_fields(json_str: str, message: Dict[str, Any]) -> None:
    """Extract status-specific fields."""
    # Battery data
    soc_match = re.search(r'"?soc"?(\d+)', json_str)
    if soc_match:
        message['battery_soc'] = int(soc_match.group(1))
    
    voltage_match = re.search(r'"?v"?(\d+\.?\d*)', json_str)
    if voltage_match:
        message['battery_voltage'] = float(voltage_match.group(1))
    
    # Power data
    wh_rem_match = re.search(r'"?whRem"?(\d+)', json_str)
    if wh_rem_match:
        message['wh_remaining'] = int(wh_rem_match.group(1))
    
    wh_in_match = re.search(r'"?whIn"?(\d+)', json_str)
    if wh_in_match:
        message['wh_input'] = int(wh_in_match.group(1))
    
    wh_out_match = re.search(r'"?whOut"?(\d+)', json_str)
    if wh_out_match:
        message['wh_output'] = int(wh_out_match.group(1))

def extract_device_fields(json_str: str, message: Dict[str, Any]) -> None:
    """Extract device-specific fields."""
    fw_match = re.search(r'"?fw"?"?([^"]+)"?', json_str)
    if fw_match:
        message['firmware'] = fw_match.group(1).strip('"')
    
    sn_match = re.search(r'"?sn"?"?([^"]+)"?', json_str)
    if sn_match:
        message['serial_number'] = sn_match.group(1).strip('"')

def extract_config_fields(json_str: str, message: Dict[str, Any]) -> None:
    """Extract config-specific fields."""
    # Charging profile
    if 'chgPrfl' in json_str:
        message['has_charge_profile'] = True

def analyze_protocol(messages: List[Dict[str, Any]]) -> None:
    """Analyze the complete protocol."""
    print(f"\n📊 Protocol Analysis ({len(messages)} messages)")
    print("=" * 60)
    
    # Group by method
    methods = {}
    for msg in messages:
        method = msg['parsed'].get('method', 'unknown')
        if method not in methods:
            methods[method] = []
        methods[method].append(msg)
    
    print(f"📋 Discovered Methods:")
    for method, msgs in methods.items():
        requests = [m for m in msgs if m['parsed'].get('type') == 'request']
        responses = [m for m in msgs if m['parsed'].get('type') == 'response']
        print(f"  {method:12} -> {len(requests):2} requests, {len(responses):2} responses")
    
    # Analyze status messages in detail
    if 'status' in methods:
        print(f"\n📈 Status Message Analysis:")
        status_msgs = methods['status']
        
        # Find all unique fields in status responses
        all_fields = set()
        for msg in status_msgs:
            if msg['parsed'].get('type') == 'response':
                for key in msg['parsed'].keys():
                    if key not in ['id', 'type', 'method', 'has_body']:
                        all_fields.add(key)
        
        print(f"  Status fields found: {sorted(all_fields)}")
    
    # Show sample messages
    print(f"\n📝 Sample Messages:")
    for method in ['device', 'status', 'config']:
        if method in methods:
            sample = methods[method][0]
            print(f"  {method.upper()}:")
            print(f"    Raw: {sample['raw_json'][:80]}...")
            print(f"    Parsed: {sample['parsed']}")

def main():
    """Main analysis function."""
    csv_file = "testing/Wireshark_filtered_decode.csv"
    
    messages = extract_all_json_messages(csv_file)
    
    if messages:
        analyze_protocol(messages)
        
        # Save analysis results
        with open('yeti500_protocol_analysis.json', 'w') as f:
            json.dump(messages, f, indent=2, default=str)
        
        print(f"\n💾 Full analysis saved to: yeti500_protocol_analysis.json")
    else:
        print("❌ No JSON messages could be extracted")

if __name__ == "__main__":
    main()
