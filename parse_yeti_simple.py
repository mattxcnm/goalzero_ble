#!/usr/bin/env python3
"""
Simple and accurate Yeti 500 protocol parser focused on complete messages.
"""

import csv
import json
import re
from typing import Dict, List, Any
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

def simple_parse_csv(csv_file: str) -> List[Dict[str, Any]]:
    """Simple parsing focused on complete message reconstruction."""
    print("📖 Simple parsing for complete messages...")
    
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Find all the large response messages by looking for multi-line 0x0003 sequences
    large_messages = []
    
    i = 0
    while i < len(rows):
        row = rows[i]
        
        # Look for 0x0008 length prefix
        if row['handle'] == '0x0008':
            length_hex = row['value'].split(':')[-1]
            try:
                expected_length = int(length_hex, 16)
                
                # Collect all 0x0003 data that follows
                all_text = ""
                j = i + 1
                
                while j < len(rows) and rows[j]['handle'] == '0x0003':
                    decoded = decode_ascii_hex(rows[j]['value'])
                    all_text += decoded
                    j += 1
                
                if len(all_text) > 50:  # Only large messages
                    large_messages.append({
                        'start_row': i + 1,
                        'end_row': j,
                        'expected_length': expected_length,
                        'text': all_text,
                        'actual_length': len(all_text)
                    })
                    print(f"Row {i+1}: Large message found - {len(all_text)} chars")
                
                i = j
            except ValueError:
                i += 1
        else:
            i += 1
    
    return large_messages

def extract_complete_json_responses(large_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract complete JSON responses from large messages."""
    responses = []
    
    for msg in large_messages:
        text = msg['text']
        
        # Look for complete JSON responses (they contain "result" and have proper structure)
        if '"result"' in text and '"body"' in text:
            # Try to extract the complete JSON response
            # Find the outermost { } pair
            brace_count = 0
            start_pos = text.find('{')
            if start_pos != -1:
                json_end = start_pos
                for i, char in enumerate(text[start_pos:], start_pos):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i
                            break
                
                if brace_count == 0:
                    json_str = text[start_pos:json_end + 1]
                    
                    # Parse this large response
                    parsed = parse_large_response(json_str)
                    if parsed:
                        responses.append({
                            'start_row': msg['start_row'],
                            'raw_json': json_str,
                            'parsed': parsed,
                            'length': len(json_str)
                        })
                        print(f"  ✅ Extracted {parsed.get('method', 'unknown')} response (ID: {parsed.get('id', '?')})")
    
    return responses

def parse_large_response(json_str: str) -> Dict[str, Any] | None:
    """Parse a large JSON response to extract all entity data."""
    try:
        # Clean up the malformed JSON
        # The main issue is missing colons after field names
        
        # Step 1: Add colons where missing between quoted fields and values
        # Pattern: "field"value -> "field":value
        cleaned = re.sub(r'"([^"]+)"([^":{}\[\],\s])', r'"\1":\2', json_str)
        
        # Step 2: Fix quoted string patterns: "field""value" -> "field":"value"
        cleaned = re.sub(r'"([^"]+)""([^"]*)"', r'"\1":"\2"', cleaned)
        
        # Step 3: Fix array/object patterns: "field"[...] or "field"{...}
        cleaned = re.sub(r'"([^"]+)"(\[|\{)', r'"\1":\2', cleaned)
        
        # Step 4: Clean up multiple colons
        cleaned = re.sub(r'::+', ':', cleaned)
        
        # Manual extraction since JSON parsing might still fail
        data: Dict[str, Any] = {'type': 'response'}
        
        # Extract ID
        id_match = re.search(r'"id"\s*:\s*(\d+)', cleaned)
        if id_match:
            data['id'] = int(id_match.group(1))
        
        # Extract method (sometimes in original request context)
        method_match = re.search(r'"method"\s*:\s*"([^"]+)"', cleaned)
        if method_match:
            data['method'] = method_match.group(1)
        
        # Extract src
        src_match = re.search(r'"src"\s*:\s*"([^"]+)"', cleaned)
        if src_match:
            data['src'] = src_match.group(1)
        
        # Extract all the important data fields
        result_data = {}
        
        # Device info
        fw_match = re.search(r'"fw"\s*:\s*"([^"]+)"', cleaned)
        if fw_match:
            result_data['firmware'] = fw_match.group(1)
        
        sn_match = re.search(r'"sn"\s*:\s*"([^"]+)"', cleaned)
        if sn_match:
            result_data['serial_number'] = sn_match.group(1)
        
        # Battery data (comprehensive)
        battery_data = {}
        battery_patterns = {
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
            'pctHtsRh': r'"pctHtsRh"\s*:\s*(\d+)',
            'cHtsTmp': r'"cHtsTmp"\s*:\s*([\d.]+)',
        }
        
        for field, pattern in battery_patterns.items():
            match = re.search(pattern, cleaned)
            if match:
                value = match.group(1)
                battery_data[field] = float(value) if '.' in value else int(value)
        
        if battery_data:
            result_data['battery'] = battery_data
        
        # Port data (all ports with comprehensive data)
        ports_data = {}
        
        # AC Output
        ac_out_match = re.search(r'"acOut"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"w"\s*:\s*(\d+)[^}]*"v"\s*:\s*(\d+)[^}]*"a"\s*:\s*([\d.]+)', cleaned)
        if ac_out_match:
            ports_data['acOut'] = {
                'status': int(ac_out_match.group(1)),
                'watts': int(ac_out_match.group(2)),
                'voltage': int(ac_out_match.group(3)),
                'amperage': float(ac_out_match.group(4))
            }
        
        # AC Input  
        ac_in_match = re.search(r'"acIn"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"v"\s*:\s*(\d+)[^}]*"a"\s*:\s*([\d.]+)[^}]*"w"\s*:\s*(\d+)[^}]*"fastChg"\s*:\s*(\d+)', cleaned)
        if ac_in_match:
            ports_data['acIn'] = {
                'status': int(ac_in_match.group(1)),
                'voltage': int(ac_in_match.group(2)),
                'amperage': float(ac_in_match.group(3)),
                'watts': int(ac_in_match.group(4)),
                'fast_charging': int(ac_in_match.group(5))
            }
        
        # 12V Output
        v12_out_match = re.search(r'"v12Out"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"w"\s*:\s*(\d+)', cleaned)
        if v12_out_match:
            ports_data['v12Out'] = {
                'status': int(v12_out_match.group(1)),
                'watts': int(v12_out_match.group(2))
            }
        
        # USB Output
        usb_out_match = re.search(r'"usbOut"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"w"\s*:\s*(\d+)', cleaned)
        if usb_out_match:
            ports_data['usbOut'] = {
                'status': int(usb_out_match.group(1)),
                'watts': int(usb_out_match.group(2))
            }
        
        # Low Voltage DC Input
        lv_dc_in_match = re.search(r'"lvDcIn"\s*:\s*\{[^}]*"s"\s*:\s*(\d+)[^}]*"v"\s*:\s*(\d+)[^}]*"a"\s*:\s*([\d.]+)[^}]*"w"\s*:\s*(\d+)', cleaned)
        if lv_dc_in_match:
            ports_data['lvDcIn'] = {
                'status': int(lv_dc_in_match.group(1)),
                'voltage': int(lv_dc_in_match.group(2)),
                'amperage': float(lv_dc_in_match.group(3)),
                'watts': int(lv_dc_in_match.group(4))
            }
        
        if ports_data:
            result_data['ports'] = ports_data
        
        # Charge profile
        charge_profile = {}
        chg_profile_match = re.search(r'"chgPrfl"\s*:\s*\{[^}]*"min"\s*:\s*(\d+)[^}]*"max"\s*:\s*(\d+)[^}]*"rchg"\s*:\s*(\d+)', cleaned)
        if chg_profile_match:
            charge_profile = {
                'min': int(chg_profile_match.group(1)),
                'max': int(chg_profile_match.group(2)),
                'rchg': int(chg_profile_match.group(3))
            }
            result_data['charge_profile'] = charge_profile
        
        # Display settings
        display_match = re.search(r'"dsp"\s*:\s*\{[^}]*"blkOut"\s*:\s*(\d+)[^}]*"brt"\s*:\s*(\d+)', cleaned)
        if display_match:
            result_data['display'] = {
                'blackout_time': int(display_match.group(1)),
                'brightness': int(display_match.group(2))
            }
        
        data['result'] = result_data
        return data
        
    except Exception as e:
        print(f"    Error parsing response: {e}")
        return None

def generate_yeti_entities(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate complete Yeti 500 entity definitions."""
    entities = {
        'sensors': set(),
        'switches': set(), 
        'numbers': set(),
        'device_info': {}
    }
    
    for resp in responses:
        result = resp['parsed'].get('result', {})
        
        # Device info
        if 'firmware' in result:
            entities['device_info']['firmware'] = result['firmware']
        if 'serial_number' in result:
            entities['device_info']['serial_number'] = result['serial_number']
        
        # Battery sensors
        if 'battery' in result:
            battery = result['battery']
            for field in battery.keys():
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
                    'mTtef': 'battery_time_to_empty_minutes',
                    'pctHtsRh': 'battery_heater_relative_humidity',
                    'cHtsTmp': 'battery_heater_temperature',
                }.get(field, f'battery_{field}')
                entities['sensors'].add(sensor_name)
        
        # Port sensors and switches
        if 'ports' in result:
            ports = result['ports']
            for port_name, port_data in ports.items():
                # Status sensor for all ports
                entities['sensors'].add(f"{port_name}_status")
                
                # Power sensors
                if 'watts' in port_data:
                    entities['sensors'].add(f"{port_name}_watts")
                if 'voltage' in port_data:
                    entities['sensors'].add(f"{port_name}_voltage")  
                if 'amperage' in port_data:
                    entities['sensors'].add(f"{port_name}_amperage")
                
                # Special sensors
                if 'fast_charging' in port_data:
                    entities['sensors'].add(f"{port_name}_fast_charging")
                
                # Control switches for output ports
                if 'Out' in port_name:
                    entities['switches'].add(f"{port_name}_switch")
        
        # Charge profile numbers
        if 'charge_profile' in result:
            entities['numbers'].add('charge_profile_min_soc')
            entities['numbers'].add('charge_profile_max_soc') 
            entities['numbers'].add('charge_profile_recharge_soc')
        
        # Display numbers
        if 'display' in result:
            entities['numbers'].add('display_blackout_time')
            entities['numbers'].add('display_brightness')
    
    return entities

def main():
    """Main analysis function."""
    csv_file = "testing/Wireshark_filtered_decode.csv"
    
    # Parse for large messages
    large_messages = simple_parse_csv(csv_file)
    
    # Extract complete JSON responses
    responses = extract_complete_json_responses(large_messages)
    
    if responses:
        print(f"\n✅ Successfully extracted {len(responses)} complete responses")
        
        # Generate entities
        entities = generate_yeti_entities(responses)
        
        # Create final output
        output = {
            'protocol_summary': {
                'total_responses': len(responses),
                'communication_pattern': {
                    'request': 'Short JSON on 0x0003 after 0x0008 length',
                    'response': 'Large multi-fragment JSON on 0x0003',
                    'handles': {
                        '0x0008': 'Message length prefix (4 bytes: 00:00:00:XX)',
                        '0x0003': 'JSON message data (fragmented)',
                        '0x0005': 'Status/acknowledgment'
                    }
                }
            },
            'entities': {
                'sensors': sorted(entities['sensors']),
                'switches': sorted(entities['switches']),
                'numbers': sorted(entities['numbers']),
                'device_info': entities['device_info'],
                'total_entities': len(entities['sensors']) + len(entities['switches']) + len(entities['numbers'])
            },
            'sample_responses': responses[:3],
            'all_responses': responses
        }
        
        # Save results
        with open('yeti500_complete_entities.json', 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\n📊 Complete Entity Analysis:")
        print(f"  Total Entities: {output['entities']['total_entities']}")
        print(f"  Sensors:  {len(entities['sensors']):2}")
        print(f"  Switches: {len(entities['switches']):2}")
        print(f"  Numbers:  {len(entities['numbers']):2}")
        
        print(f"\n🔋 Battery Sensors ({len([s for s in entities['sensors'] if 'battery' in s])}):")
        for sensor in sorted([s for s in entities['sensors'] if 'battery' in s])[:8]:
            print(f"    - {sensor}")
        
        print(f"\n🔌 Port Entities ({len([e for e in entities['sensors'] | entities['switches'] if any(p in e for p in ['acOut', 'acIn', 'usbOut', 'v12Out', 'lvDcIn'])])}):")
        port_entities = [e for e in entities['sensors'] | entities['switches'] if any(p in e for p in ['acOut', 'acIn', 'usbOut', 'v12Out', 'lvDcIn'])]
        for entity in sorted(port_entities)[:8]:
            print(f"    - {entity}")
        
        print(f"\n⚙️  Control Entities ({len(entities['switches']) + len(entities['numbers'])}):")
        for control in sorted(entities['switches'] | entities['numbers'])[:6]:
            print(f"    - {control}")
        
        print(f"\n💾 Complete analysis saved to: yeti500_complete_entities.json")
    
    else:
        print("❌ No complete responses found")

if __name__ == "__main__":
    main()
