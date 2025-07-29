#!/usr/bin/env python3
"""
Ultimate Yeti 500 protocol parser that correctly handles multi-fragment responses.
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
    
    hex_string = hex_string.strip('"')
    parts = hex_string.split(':')
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

def fix_yeti_json(json_str: str) -> str:
    """Fix the malformed JSON format used by Yeti devices."""
    # The Yeti format has missing colons and malformed quotes
    
    # First, fix the basic field:value pattern where colon is missing
    # Pattern: "field"value -> "field":value
    fixed = re.sub(r'"([^"]+)"([^":{}\[\],\s])', r'"\1":\2', json_str)
    
    # Fix quoted string values that are missing colons
    # Pattern: "field""string" -> "field":"string"
    fixed = re.sub(r'"([^"]+)""([^"]*)"', r'"\1":"\2"', fixed)
    
    # Fix number values that are missing colons
    # Pattern: "field"123 -> "field":123
    fixed = re.sub(r'"([^"]+)"(\d+\.?\d*)', r'"\1":\2', fixed)
    
    # Fix object/array values that are missing colons
    # Pattern: "field"{...} -> "field":{...}
    fixed = re.sub(r'"([^"]+)"(\{|\[)', r'"\1":\2', fixed)
    
    # Clean up any double colons that might have been created
    fixed = re.sub(r'::+', ':', fixed)
    
    return fixed

def parse_csv_comprehensive(csv_file: str) -> List[Dict[str, Any]]:
    """Parse CSV with comprehensive message reconstruction."""
    print("📖 Comprehensive parsing of Wireshark CSV...")
    
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    messages = []
    i = 0
    
    while i < len(rows):
        row = rows[i]
        
        # Look for 0x0008 length prefixes
        if row['handle'] == '0x0008' and row['value'].startswith('00:00:00:'):
            length_hex = row['value'].split(':')[-1]
            try:
                expected_length = int(length_hex, 16)
                print(f"Row {i+1}: Length prefix = {expected_length}")
                
                # Collect all following 0x0003 fragments until we hit another length or end
                fragments = []
                j = i + 1
                
                while j < len(rows):
                    next_row = rows[j]
                    
                    if next_row['handle'] == '0x0003':
                        decoded = decode_ascii_hex(next_row['value'])
                        fragments.append(decoded)
                        j += 1
                    elif next_row['handle'] == '0x0008':
                        # Next message starts
                        break
                    else:
                        # Other handle, skip
                        j += 1
                
                # Reconstruct complete message
                if fragments:
                    combined = ''.join(fragments)
                    
                    # Extract JSON from the combined text
                    json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', combined)
                    
                    for json_str in json_matches:
                        if len(json_str) > 20:  # Ignore tiny fragments
                            try:
                                # Fix and parse the JSON
                                fixed_json = fix_yeti_json(json_str)
                                parsed = parse_yeti_message(fixed_json, json_str)
                                
                                if parsed:
                                    messages.append({
                                        'row_start': i + 1,
                                        'row_end': j,
                                        'raw_json': json_str,
                                        'fixed_json': fixed_json,
                                        'expected_length': expected_length,
                                        'actual_length': len(json_str),
                                        'parsed': parsed
                                    })
                                    
                                    method = parsed.get('method', 'unknown')
                                    msg_type = parsed.get('type', 'unknown')
                                    msg_id = parsed.get('id', '?')
                                    print(f"  ✅ {method} {msg_type} (ID: {msg_id}) - {len(json_str)} chars")
                                
                            except Exception as e:
                                print(f"  ❌ Parse error: {e}")
                
                i = j  # Move to next length prefix
                
            except ValueError:
                i += 1
        else:
            i += 1
    
    return messages

def parse_yeti_message(json_str: str, original: str) -> Dict[str, Any] | None:
    """Parse a Yeti JSON message."""
    try:
        # Try standard JSON parsing
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError:
            # If that fails, do manual extraction
            parsed = {}
            
            # Extract basic fields
            id_match = re.search(r'"id"\s*:\s*(\d+)', json_str)
            if id_match:
                parsed['id'] = int(id_match.group(1))
            
            method_match = re.search(r'"method"\s*:\s*"([^"]+)"', json_str)
            if method_match:
                parsed['method'] = method_match.group(1)
            
            src_match = re.search(r'"src"\s*:\s*"([^"]+)"', json_str)
            if src_match:
                parsed['src'] = src_match.group(1)
        
        # Determine message type and extract data
        if 'result' in json_str:
            parsed['type'] = 'response'
            parsed['result'] = extract_response_data(json_str)
        elif 'params' in json_str:
            parsed['type'] = 'request'
            parsed['params'] = extract_request_params(json_str)
        else:
            parsed['type'] = 'request'
        
        return parsed
        
    except Exception as e:
        print(f"    Parse error: {e}")
        return None

def extract_response_data(json_str: str) -> Dict[str, Any]:
    """Extract structured data from response body."""
    data = {}
    
    # Device information
    fw_match = re.search(r'"fw"\s*:\s*"([^"]+)"', json_str)
    if fw_match:
        data['firmware'] = fw_match.group(1)
    
    sn_match = re.search(r'"sn"\s*:\s*"([^"]+)"', json_str)
    if sn_match:
        data['serial_number'] = sn_match.group(1)
    
    # Battery data - comprehensive extraction
    battery_fields = {
        'soc': r'"soc"\s*:\s*(\d+)',
        'whRem': r'"whRem"\s*:\s*(\d+)',
        'v': r'"v"\s*:\s*([\d.]+)',
        'cyc': r'"cyc"\s*:\s*(\d+)',
        'cTmp': r'"cTmp"\s*:\s*([\d.]+)',
        'whIn': r'"whIn"\s*:\s*(\d+)',
        'whOut': r'"whOut"\s*:\s*(\d+)',
        'aNetAvg': r'"aNetAvg"\s*:\s*([\d.]+)',
        'aNet': r'"aNet"\s*:\s*([\d.]+)',
        'wNetAvg': r'"wNetAvg"\s*:\s*(\d+)',
        'wNet': r'"wNet"\s*:\s*(\d+)',
        'mTtef': r'"mTtef"\s*:\s*(\d+)',
    }
    
    battery_data = {}
    for field, pattern in battery_fields.items():
        match = re.search(pattern, json_str)
        if match:
            value = match.group(1)
            battery_data[field] = float(value) if '.' in value else int(value)
    
    if battery_data:
        data['battery'] = battery_data
    
    # Port data - all ports
    port_patterns = {
        'acOut': r'"acOut"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"w"\s*:\s*(\d+)[^}]*"v"\s*:\s*(\d+)[^}]*"a"\s*:\s*([\d.]+)',
        'v12Out': r'"v12Out"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"w"\s*:\s*(\d+)',
        'usbOut': r'"usbOut"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"w"\s*:\s*(\d+)',
        'acIn': r'"acIn"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"v"\s*:\s*(\d+)[^}]*"a"\s*:\s*([\d.]+)[^}]*"w"\s*:\s*(\d+)',
        'lvDcIn': r'"lvDcIn"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"v"\s*:\s*(\d+)[^}]*"a"\s*:\s*([\d.]+)[^}]*"w"\s*:\s*(\d+)',
    }
    
    ports_data = {}
    for port_name, pattern in port_patterns.items():
        match = re.search(pattern, json_str)
        if match:
            port_info = {
                'status': int(match.group(1)),
                'watts': int(match.group(2))
            }
            
            # Add voltage/amperage if available
            groups = match.groups()
            if len(groups) >= 3 and port_name in ['acOut', 'acIn', 'lvDcIn']:
                port_info['voltage'] = int(groups[2])  # type: ignore
            if len(groups) >= 4:
                port_info['amperage'] = float(groups[3])  # type: ignore
            
            ports_data[port_name] = port_info
    
    if ports_data:
        data['ports'] = ports_data
    
    # Charge profile
    chg_patterns = {
        'min': r'"min"\s*:\s*(\d+)',
        'max': r'"max"\s*:\s*(\d+)',
        'rchg': r'"rchg"\s*:\s*(\d+)',
    }
    
    charge_profile = {}
    for field, pattern in chg_patterns.items():
        match = re.search(pattern, json_str)
        if match:
            charge_profile[field] = int(match.group(1))
    
    if charge_profile:
        data['charge_profile'] = charge_profile
    
    return data

def extract_request_params(json_str: str) -> Dict[str, Any]:
    """Extract parameters from request messages."""
    params = {}
    
    # Action parameter
    action_match = re.search(r'"action"\s*:\s*"([^"]+)"', json_str)
    if action_match:
        params['action'] = action_match.group(1)
    
    # Port control
    port_control_match = re.search(r'"ports"\s*:\s*\{[^}]*"(\w+)"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)', json_str)
    if port_control_match:
        params['port'] = port_control_match.group(1)
        params['state'] = int(port_control_match.group(2))
    
    return params

def generate_complete_entities(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate complete entity list from all messages."""
    entities = {
        'sensors': set(),
        'switches': set(),
        'numbers': set(),
        'device_info': {},
        'methods': defaultdict(int)
    }
    
    print(f"\n📊 Analyzing {len(messages)} messages for entities...")
    
    for msg in messages:
        parsed = msg['parsed']
        method = parsed.get('method', 'unknown')
        msg_type = parsed.get('type', 'unknown')
        entities['methods'][f"{method}_{msg_type}"] += 1
        
        if msg_type == 'response':
            result = parsed.get('result', {})
            
            # Device info
            if 'firmware' in result:
                entities['device_info']['firmware'] = result['firmware']
            if 'serial_number' in result:
                entities['device_info']['serial_number'] = result['serial_number']
            
            # Battery sensors
            if 'battery' in result:
                battery = result['battery']
                for field, value in battery.items():
                    sensor_name = {
                        'soc': 'battery_state_of_charge',
                        'whRem': 'battery_remaining_wh',
                        'v': 'battery_voltage',
                        'cyc': 'battery_cycles',
                        'cTmp': 'battery_temperature',
                        'whIn': 'battery_input_wh',
                        'whOut': 'battery_output_wh',
                        'aNetAvg': 'battery_current_net_avg',
                        'aNet': 'battery_current_net',
                        'wNetAvg': 'battery_power_net_avg',
                        'wNet': 'battery_power_net',
                        'mTtef': 'battery_time_to_empty',
                    }.get(field, f'battery_{field}')
                    entities['sensors'].add(sensor_name)
            
            # Port entities
            if 'ports' in result:
                ports = result['ports']
                for port_name, port_data in ports.items():
                    # Status sensor
                    entities['sensors'].add(f"{port_name}_status")
                    
                    # Power sensors
                    if 'watts' in port_data:
                        entities['sensors'].add(f"{port_name}_watts")
                    if 'voltage' in port_data:
                        entities['sensors'].add(f"{port_name}_voltage")
                    if 'amperage' in port_data:
                        entities['sensors'].add(f"{port_name}_amperage")
                    
                    # Control switches for output ports
                    if 'Out' in port_name:
                        entities['switches'].add(f"{port_name}_switch")
            
            # Charge profile controls
            if 'charge_profile' in result:
                profile = result['charge_profile']
                if 'min' in profile:
                    entities['numbers'].add('charge_profile_min_soc')
                if 'max' in profile:
                    entities['numbers'].add('charge_profile_max_soc')
                if 'rchg' in profile:
                    entities['numbers'].add('charge_profile_recharge_soc')
        
        elif msg_type == 'request' and 'params' in parsed:
            params = parsed['params']
            
            # Control requests reveal controllable entities
            if 'port' in params and 'Out' in params['port']:
                entities['switches'].add(f"{params['port']}_switch")
    
    return entities

def main():
    """Main comprehensive analysis."""
    csv_file = "testing/Wireshark_filtered_decode.csv"
    
    # Parse all messages
    messages = parse_csv_comprehensive(csv_file)
    
    if messages:
        print(f"\n✅ Successfully parsed {len(messages)} complete JSON messages")
        
        # Generate complete entity list
        entities = generate_complete_entities(messages)
        
        # Create comprehensive output
        output = {
            'protocol_analysis': {
                'total_messages': len(messages),
                'methods': dict(entities['methods']),
                'ble_communication': {
                    'length_handle': '0x0008',
                    'data_handle': '0x0003',
                    'ack_handle': '0x0005',
                    'description': 'JSON-RPC over BLE with length prefixes'
                }
            },
            'entities': {
                'sensors': sorted(entities['sensors']),
                'switches': sorted(entities['switches']),
                'numbers': sorted(entities['numbers']),
                'device_info': entities['device_info']
            },
            'sample_messages': messages[:5],  # First 5 for reference
            'all_messages': messages
        }
        
        # Save comprehensive results
        with open('yeti500_final_entities.json', 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\n📊 Final Entity Summary:")
        print(f"  Sensors:  {len(entities['sensors']):2} total")
        print(f"  Switches: {len(entities['switches']):2} total")
        print(f"  Numbers:  {len(entities['numbers']):2} total")
        print(f"  Methods:  {', '.join(entities['methods'].keys())}")
        
        print(f"\n🔋 Battery Sensors:")
        battery_sensors = [s for s in entities['sensors'] if 'battery' in s]
        for sensor in sorted(battery_sensors)[:10]:
            print(f"    - {sensor}")
        
        print(f"\n🔌 Port Entities:")
        port_entities = [e for e in entities['sensors'] | entities['switches'] if any(p in e for p in ['acOut', 'acIn', 'usbOut', 'v12Out', 'lvDcIn'])]
        for entity in sorted(port_entities)[:10]:
            print(f"    - {entity}")
        
        print(f"\n💾 Complete analysis saved to: yeti500_final_entities.json")
        
    else:
        print("❌ No messages could be parsed")

if __name__ == "__main__":
    main()
