#!/usr/bin/env python3
"""
Fixed Yeti 500 JSON protocol parser that handles the malformed JSON format correctly.
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

def fix_malformed_json(json_str: str) -> str:
    """Fix the malformed JSON format used by Yeti devices."""
    # The format has missing colons after field names
    # Convert: "field"value to "field":value
    fixed = re.sub(r'"([^"]+)"(\d+|"[^"]*"|\{|\[)', r'"\1":\2', json_str)
    
    # Fix some specific patterns
    fixed = re.sub(r'"method""([^"]+)"', r'"method":"\1"', fixed)
    fixed = re.sub(r'"src""([^"]+)"', r'"src":"\1"', fixed)
    fixed = re.sub(r'"action""([^"]+)"', r'"action":"\1"', fixed)
    
    return fixed

def parse_csv_to_messages(csv_file: str) -> List[Dict[str, Any]]:
    """Parse the CSV file and reconstruct complete JSON messages."""
    print("📖 Parsing Wireshark CSV for complete message reconstruction...")
    
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    messages = []
    current_length = None
    current_fragments = []
    
    for i, row in enumerate(rows):
        handle = row['handle']
        value = row['value']
        
        if handle == '0x0008':
            # Length indicator
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
            if combined.count('}') > 0:
                # Extract the JSON
                json_match = re.search(r'\{.*?\}', combined, re.DOTALL)
                if json_match:
                    raw_json = json_match.group(0)
                    
                    # Fix and parse the JSON
                    fixed_json = fix_malformed_json(raw_json)
                    parsed = parse_yeti_json(fixed_json, raw_json)
                    
                    if parsed:
                        messages.append({
                            'row': i + 1,
                            'raw_json': raw_json,
                            'fixed_json': fixed_json,
                            'decoded_length': current_length,
                            'actual_length': len(raw_json),
                            'parsed': parsed
                        })
                        method = parsed.get('method', 'unknown')
                        msg_type = parsed.get('type', 'request')
                        print(f"  ✅ Extracted: {method} {msg_type} (ID: {parsed.get('id', '?')})")
                
                # Reset for next message
                current_length = None
                current_fragments = []
    
    return messages

def parse_yeti_json(json_str: str, original: str) -> Dict[str, Any] | None:
    """Parse a fixed Yeti JSON message."""
    try:
        # Try to parse the fixed JSON
        parsed = json.loads(json_str)
        
        # Determine message type
        if 'result' in parsed:
            parsed['type'] = 'response'
        elif 'params' in parsed:
            parsed['type'] = 'request'
        else:
            parsed['type'] = 'request'
        
        return parsed
        
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON parse failed: {e}")
        print(f"     Original: {original[:50]}...")
        print(f"     Fixed:    {json_str[:50]}...")
        return None

def extract_all_entities(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract all entities from the parsed messages."""
    entities = {
        'sensors': set(),
        'controls': set(),
        'device_info': {},
        'methods': defaultdict(list)
    }
    
    for msg in messages:
        parsed = msg['parsed']
        method = parsed.get('method', 'unknown')
        entities['methods'][method].append(parsed)
        
        if method == 'device' and parsed.get('type') == 'response':
            result = parsed.get('result', {})
            body = result.get('body', {})
            
            # Extract device info
            if 'fw' in body:
                entities['device_info']['firmware'] = body['fw']
            if 'sn' in body:
                entities['device_info']['serial_number'] = body['sn']
            if 'identity' in body:
                identity = body['identity']
                if 'thingName' in identity:
                    entities['device_info']['thing_name'] = identity['thingName']
                if 'local' in identity:
                    entities['device_info']['local_name'] = identity['local']
        
        elif method == 'status' and parsed.get('type') == 'response':
            result = parsed.get('result', {})
            body = result.get('body', {})
            
            # Battery entities
            if 'batt' in body:
                batt = body['batt']
                for key in ['soc', 'whRem', 'v', 'cyc', 'cTmp', 'whIn', 'whOut']:
                    if key in batt:
                        sensor_name = {
                            'soc': 'battery_soc',
                            'whRem': 'battery_remaining_wh',
                            'v': 'battery_voltage',
                            'cyc': 'battery_cycles',
                            'cTmp': 'battery_temperature',
                            'whIn': 'battery_input_wh',
                            'whOut': 'battery_output_wh'
                        }.get(key, f'battery_{key}')
                        entities['sensors'].add(sensor_name)
            
            # Port entities
            if 'ports' in body:
                ports = body['ports']
                for port_name, port_data in ports.items():
                    # Status sensor
                    entities['sensors'].add(f"{port_name}_status")
                    
                    # Power/voltage sensors
                    if 'w' in port_data:
                        entities['sensors'].add(f"{port_name}_watts")
                    if 'v' in port_data:
                        entities['sensors'].add(f"{port_name}_voltage")
                    if 'a' in port_data:
                        entities['sensors'].add(f"{port_name}_amperage")
                    
                    # Control switches for output ports
                    if 'Out' in port_name:
                        entities['controls'].add(f"{port_name}_switch")
        
        elif method == 'config' and parsed.get('type') == 'response':
            result = parsed.get('result', {})
            body = result.get('body', {})
            
            # Charge profile controls
            if 'chgPrfl' in body:
                chg_profile = body['chgPrfl']
                if 'min' in chg_profile:
                    entities['controls'].add('charge_profile_min')
                if 'max' in chg_profile:
                    entities['controls'].add('charge_profile_max')
                if 'rchg' in chg_profile:
                    entities['controls'].add('charge_profile_current')
        
        elif parsed.get('type') == 'request' and 'params' in parsed:
            params = parsed['params']
            
            # Control requests reveal controllable entities
            if 'action' in params and params['action'] == 'PATCH':
                if 'body' in params and 'ports' in params['body']:
                    # Port control
                    ports = params['body']['ports']
                    for port_name in ports.keys():
                        if 'Out' in port_name:
                            entities['controls'].add(f"{port_name}_switch")
    
    return entities

def generate_entity_definitions(entities: Dict[str, Any]) -> str:
    """Generate entity definitions for the Yeti 500 device."""
    sensors = sorted(entities['sensors'])
    controls = sorted(entities['controls'])
    
    definition = f"""
# Yeti 500 Entity Definitions
# Generated from Wireshark protocol analysis

## Device Information
{json.dumps(entities['device_info'], indent=2)}

## Sensors ({len(sensors)} total)
{chr(10).join(f"- {sensor}" for sensor in sensors)}

## Controls ({len(controls)} total)
{chr(10).join(f"- {control}" for control in controls)}

## Methods Available
{chr(10).join(f"- {method}: {len(msgs)} messages" for method, msgs in entities['methods'].items())}
"""
    return definition

def main():
    """Main analysis function."""
    csv_file = "testing/Wireshark_filtered_decode.csv"
    
    # Parse all messages
    messages = parse_csv_to_messages(csv_file)
    
    if messages:
        print(f"\n✅ Successfully parsed {len(messages)} complete JSON messages")
        
        # Extract entities
        entities = extract_all_entities(messages)
        
        # Generate comprehensive analysis
        analysis = {
            'total_messages': len(messages),
            'methods': {method: len(msgs) for method, msgs in entities['methods'].items()},
            'entities_found': {
                'sensors': sorted(entities['sensors']),
                'controls': sorted(entities['controls']),
                'device_info': entities['device_info']
            }
        }
        
        # Save complete results
        output = {
            'messages': messages,
            'analysis': analysis,
            'entities': {
                'sensors': sorted(entities['sensors']),
                'controls': sorted(entities['controls']),
                'device_info': entities['device_info']
            }
        }
        
        with open('yeti500_entities_complete.json', 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        # Generate entity definitions
        definitions = generate_entity_definitions(entities)
        with open('yeti500_entity_definitions.md', 'w') as f:
            f.write(definitions)
        
        print(f"\n📊 Protocol Analysis Summary:")
        print(f"  Total Messages: {len(messages)}")
        print(f"  Methods: {', '.join(analysis['methods'].keys())}")
        print(f"  Sensors: {len(entities['sensors'])}")
        print(f"  Controls: {len(entities['controls'])}")
        
        print(f"\n💾 Files saved:")
        print(f"  - yeti500_entities_complete.json (complete data)")
        print(f"  - yeti500_entity_definitions.md (readable summary)")
        
        # Show key entities
        print(f"\n📋 Key Entities Found:")
        print(f"  Battery: {[s for s in entities['sensors'] if 'battery' in s][:5]}")
        print(f"  Ports: {[s for s in entities['sensors'] if any(p in s for p in ['acOut', 'acIn', 'usbOut', 'v12Out'])][:5]}")
        print(f"  Controls: {list(entities['controls'])[:5]}")
    
    else:
        print("❌ No messages could be parsed")

if __name__ == "__main__":
    main()
