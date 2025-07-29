#!/usr/bin/env python3
"""
Complete Yeti 500 JSON protocol parser from Wireshark capture.
This extracts all commands, responses, and entity data.
"""

import csv
import json
import re
from typing import Dict, List, Any, Tuple
from collections import defaultdict

def decode_ascii_hex(hex_string: str) -> str:
    """Convert colon-separated ASCII hex values to readable text."""
    if not hex_string:
        return ""
    
    # Remove quotes if present
    hex_string = hex_string.strip('"')
    
    # Split on colons and convert each hex value
    parts = hex_string.split(':')
    result = ""
    
    for part in parts:
        if len(part) == 1:
            # Single character
            result += part
        elif len(part) == 2:
            try:
                # Two-character hex value
                byte_val = int(part, 16)
                if 32 <= byte_val <= 126:  # Printable ASCII
                    result += chr(byte_val)
                else:
                    result += f"[{part}]"
            except ValueError:
                result += part
        else:
            # Longer string, just add as-is
            result += part
    
    return result

def parse_csv_to_messages(csv_file: str) -> List[Dict[str, Any]]:
    """Parse the CSV file and reconstruct complete JSON messages."""
    print("📖 Parsing Wireshark CSV for complete message reconstruction...")
    
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    messages = []
    current_length = None
    current_fragments = []
    current_id = None
    
    for i, row in enumerate(rows):
        handle = row['handle']
        value = row['value']
        
        if handle == '0x0008':
            # Length indicator - last byte is the message length
            if value.startswith('00:00:00:'):
                length_hex = value.split(':')[-1]
                try:
                    current_length = int(length_hex, 16)
                    current_fragments = []
                    print(f"Row {i+1}: New message, length={current_length}")
                except ValueError:
                    current_length = None
                    
        elif handle == '0x0003' and current_length is not None:
            # JSON data fragment
            decoded = decode_ascii_hex(value)
            current_fragments.append(decoded)
            
            # Check if we have a complete message
            combined = ''.join(current_fragments)
            if len(combined) >= current_length or combined.count('}') > 0:
                # Try to extract complete JSON
                json_match = re.search(r'\{.*\}', combined, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    
                    # Parse the JSON manually since it has non-standard format
                    parsed = parse_yeti_json_message(json_str)
                    if parsed:
                        messages.append({
                            'row': i + 1,
                            'raw_json': json_str,
                            'decoded_length': current_length,
                            'actual_length': len(json_str),
                            'parsed': parsed
                        })
                        print(f"  ✅ Extracted: {parsed.get('method', 'unknown')} (ID: {parsed.get('id', '?')})")
                
                # Reset for next message
                current_length = None
                current_fragments = []
    
    return messages

def parse_yeti_json_message(json_str: str) -> Dict[str, Any] | None:
    """Parse a Yeti JSON message into structured data."""
    try:
        # Clean up the JSON string
        cleaned = json_str.replace('""', '"').replace('""', '"')
        
        # Try standard JSON parsing first
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Manual parsing for the specific Yeti format
        message = {}
        
        # Extract basic fields
        id_match = re.search(r'"id"\s*:\s*(\d+)', json_str)
        if id_match:
            message['id'] = int(id_match.group(1))
        
        method_match = re.search(r'"method"\s*:\s*"([^"]+)"', json_str)
        if method_match:
            message['method'] = method_match.group(1)
        
        src_match = re.search(r'"src"\s*:\s*"([^"]+)"', json_str)
        if src_match:
            message['src'] = src_match.group(1)
        
        # Check if it's a request or response
        if '"result"' in json_str:
            message['type'] = 'response'
            message['result'] = extract_result_body(json_str)
        elif '"params"' in json_str:
            message['type'] = 'request'
            message['params'] = extract_params(json_str)
        else:
            message['type'] = 'request'
        
        return message
        
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return None

def extract_result_body(json_str: str) -> Dict[str, Any]:
    """Extract the result body from a response."""
    result = {}
    
    # Extract common fields from body
    patterns = {
        'firmware': r'"fw"\s*:\s*"([^"]+)"',
        'serial_number': r'"sn"\s*:\s*"([^"]+)"',
        'battery_soc': r'"soc"\s*:\s*(\d+)',
        'battery_voltage': r'"v"\s*:\s*([\d.]+)',
        'battery_remaining': r'"whRem"\s*:\s*(\d+)',
        'battery_input': r'"whIn"\s*:\s*(\d+)',
        'battery_output': r'"whOut"\s*:\s*(\d+)',
        'battery_cycles': r'"cyc"\s*:\s*(\d+)',
        'battery_temp': r'"cTmp"\s*:\s*([\d.]+)',
        'charge_profile_min': r'"min"\s*:\s*(\d+)',
        'charge_profile_max': r'"max"\s*:\s*(\d+)',
        'charge_profile_current': r'"rchg"\s*:\s*(\d+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, json_str)
        if match:
            try:
                value = match.group(1)
                if '.' in value:
                    result[key] = float(value)
                else:
                    result[key] = int(value)
            except ValueError:
                result[key] = value
    
    # Extract port status
    ports = {}
    port_patterns = {
        'acOut': r'"acOut"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"w"\s*:\s*(\d+)[^}]*"v"\s*:\s*(\d+)[^}]*"a"\s*:\s*([\d.]+)',
        'v12Out': r'"v12Out"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"w"\s*:\s*(\d+)',
        'usbOut': r'"usbOut"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"w"\s*:\s*(\d+)',
        'acIn': r'"acIn"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"v"\s*:\s*(\d+)[^}]*"a"\s*:\s*([\d.]+)[^}]*"w"\s*:\s*(\d+)',
        'lvDcIn': r'"lvDcIn"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"v"\s*:\s*(\d+)[^}]*"a"\s*:\s*([\d.]+)[^}]*"w"\s*:\s*(\d+)',
    }
    
    for port_name, pattern in port_patterns.items():
        match = re.search(pattern, json_str)
        if match:
            port_data: Dict[str, Any] = {'status': int(match.group(1))}
            if len(match.groups()) >= 2:
                port_data['watts'] = int(match.group(2))
            if len(match.groups()) >= 3:
                if port_name in ['acOut', 'acIn', 'lvDcIn']:
                    voltage_str = match.group(3)
                    port_data['voltage'] = int(voltage_str) if '.' not in voltage_str else float(voltage_str)
            if len(match.groups()) >= 4:
                port_data['amperage'] = float(match.group(4))
            ports[port_name] = port_data
    
    if ports:
        result['ports'] = ports
    
    return result

def extract_params(json_str: str) -> Dict[str, Any]:
    """Extract parameters from a request."""
    params = {}
    
    # Extract action and body for control commands
    action_match = re.search(r'"action"\s*:\s*"([^"]+)"', json_str)
    if action_match:
        params['action'] = action_match.group(1)
    
    # Extract port control commands
    if 'ports' in json_str:
        port_match = re.search(r'"ports"\s*:\s*\{[^}]*"(\w+)"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)', json_str)
        if port_match:
            params['port'] = port_match.group(1)
            params['state'] = int(port_match.group(2))
    
    return params

def analyze_protocol_comprehensive(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Comprehensive analysis of the protocol."""
    analysis = {
        'total_messages': len(messages),
        'methods': defaultdict(lambda: {'requests': 0, 'responses': 0, 'examples': []}),
        'entities': {
            'sensors': [],
            'controls': [],
            'device_info': {}
        },
        'ble_handles': {
            '0x0008': 'Message length prefix',
            '0x0003': 'JSON message data',
            '0x0005': 'Response status/acknowledgment'
        }
    }
    
    print(f"\n📊 Comprehensive Protocol Analysis")
    print("=" * 60)
    
    # Analyze by method
    for msg in messages:
        parsed = msg['parsed']
        method = parsed.get('method', 'unknown')
        msg_type = parsed.get('type', 'unknown')
        
        analysis['methods'][method][f'{msg_type}s'] += 1
        if len(analysis['methods'][method]['examples']) < 3:
            analysis['methods'][method]['examples'].append(parsed)
    
    # Extract all unique sensor entities from status responses
    status_sensors = set()
    control_entities = set()
    device_info = {}
    
    for msg in messages:
        parsed = msg['parsed']
        if parsed.get('method') == 'status' and parsed.get('type') == 'response':
            result = parsed.get('result', {})
            
            # Battery sensors
            for key in ['battery_soc', 'battery_voltage', 'battery_remaining', 'battery_input', 
                       'battery_output', 'battery_cycles', 'battery_temp']:
                if key in result:
                    status_sensors.add(key)
            
            # Port sensors and controls
            ports = result.get('ports', {})
            for port_name, port_data in ports.items():
                status_sensors.add(f"{port_name}_status")
                status_sensors.add(f"{port_name}_watts")
                if 'voltage' in port_data:
                    status_sensors.add(f"{port_name}_voltage")
                if 'amperage' in port_data:
                    status_sensors.add(f"{port_name}_amperage")
                
                # Add as controllable if it's an output port
                if 'Out' in port_name:
                    control_entities.add(f"{port_name}_switch")
        
        elif parsed.get('method') == 'device' and parsed.get('type') == 'response':
            result = parsed.get('result', {})
            if 'firmware' in result:
                device_info['firmware'] = result['firmware']
            if 'serial_number' in result:
                device_info['serial_number'] = result['serial_number']
        
        elif parsed.get('method') == 'config' and parsed.get('type') == 'response':
            result = parsed.get('result', {})
            for key in ['charge_profile_min', 'charge_profile_max', 'charge_profile_current']:
                if key in result:
                    control_entities.add(key)
    
    analysis['entities']['sensors'] = sorted(list(status_sensors))
    analysis['entities']['controls'] = sorted(list(control_entities))
    analysis['entities']['device_info'] = device_info
    
    # Print analysis
    print(f"📋 Methods Found:")
    for method, data in analysis['methods'].items():
        print(f"  {method:12} -> {data['requests']:2} req, {data['responses']:2} resp")
    
    print(f"\n🔍 Entities Discovered:")
    print(f"  Sensors:  {len(analysis['entities']['sensors']):2} -> {', '.join(analysis['entities']['sensors'][:5])}...")
    print(f"  Controls: {len(analysis['entities']['controls']):2} -> {', '.join(analysis['entities']['controls'][:5])}...")
    
    return analysis

def main():
    """Main analysis function."""
    csv_file = "testing/Wireshark_filtered_decode.csv"
    
    # Parse all messages
    messages = parse_csv_to_messages(csv_file)
    
    if messages:
        print(f"\n✅ Successfully parsed {len(messages)} complete JSON messages")
        
        # Comprehensive analysis
        analysis = analyze_protocol_comprehensive(messages)
        
        # Save complete results
        output = {
            'messages': messages,
            'analysis': analysis
        }
        
        with open('yeti500_complete_protocol.json', 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\n💾 Complete protocol analysis saved to: yeti500_complete_protocol.json")
        
        # Show some sample messages
        print(f"\n📝 Sample Messages:")
        for method in ['device', 'status', 'config']:
            method_msgs = [m for m in messages if m['parsed'].get('method') == method]
            if method_msgs:
                sample = method_msgs[0]
                print(f"  {method.upper()}:")
                print(f"    Length: {sample['decoded_length']} -> {sample['actual_length']}")
                print(f"    Parsed: {sample['parsed']}")
                print()
    
    else:
        print("❌ No messages could be parsed")

if __name__ == "__main__":
    main()
