#!/usr/bin/env python3
"""
Analysis script for Alta 80 BLE control packets.
This script decodes temperature setpoint controls and system setting changes.
"""

import csv
import re
from typing import List, Tuple, Dict, Any

def parse_csv_data(filename: str) -> List[Tuple[str, bytes]]:
    """Parse the CSV file and return a list of (handle, data) tuples."""
    packets = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['handle'].strip() and row['value'].strip():
                handle = row['handle'].strip()
                # Convert hex string to bytes
                hex_string = row['value'].strip().replace(':', '')
                try:
                    data = bytes.fromhex(hex_string)
                    packets.append((handle, data))
                except ValueError:
                    continue
    return packets

def fahrenheit_to_hex(temp_f: int) -> int:
    """Convert Fahrenheit to the hex value used in BLE packets."""
    # Based on observed pattern, appears to be direct temperature mapping
    return temp_f

def hex_to_fahrenheit(hex_val: int) -> int:
    """Convert hex value back to Fahrenheit."""
    return hex_val

def analyze_temperature_setpoints(packets: List[Tuple[str, bytes]]):
    """Analyze temperature setpoint control patterns."""
    print("=== TEMPERATURE SETPOINT ANALYSIS ===\n")
    
    # Look for short command packets that might be temperature controls
    temp_commands = []
    
    for handle, data in packets:
        if len(data) == 7 and data[0:3] == bytes([0xFE, 0xFE, 0x04]):
            # Pattern: fe:fe:04:05:XX:02:YY or fe:fe:04:06:XX:02:YY
            zone = data[3]  # 0x05 = Zone 1, 0x06 = Zone 2
            temp_hex = data[4]
            unknown1 = data[5] 
            checksum = data[6]
            
            temp_f = hex_to_fahrenheit(temp_hex)
            zone_num = 1 if zone == 0x05 else 2 if zone == 0x06 else zone
            
            temp_commands.append({
                'handle': handle,
                'zone': zone_num,
                'temp_f': temp_f,
                'temp_hex': temp_hex,
                'unknown1': unknown1,
                'checksum': checksum,
                'raw_data': data.hex(':')
            })
    
    # Group by zone and show progression
    zones = {}
    for cmd in temp_commands:
        zone = cmd['zone']
        if zone not in zones:
            zones[zone] = []
        zones[zone].append(cmd)
    
    for zone, commands in zones.items():
        print(f"Zone {zone} Temperature Commands:")
        print("Handle  | Temp °F | Hex | Unknown | Checksum | Raw Data")
        print("-" * 70)
        
        prev_temp = None
        for cmd in commands[:15]:  # Show first 15 for brevity
            temp_f = cmd['temp_f']
            direction = ""
            if prev_temp is not None:
                if temp_f < prev_temp:
                    direction = "↓"
                elif temp_f > prev_temp:
                    direction = "↑"
                else:
                    direction = "="
            
            print(f"{cmd['handle']} | {temp_f:3d}°F {direction:1s} | 0x{cmd['temp_hex']:02X} | "
                  f"  0x{cmd['unknown1']:02X}   |   0x{cmd['checksum']:02X}   | {cmd['raw_data']}")
            prev_temp = temp_f
        
        if len(commands) > 15:
            print(f"... ({len(commands) - 15} more commands)")
        print()

def analyze_system_controls(packets: List[Tuple[str, bytes]]):
    """Analyze eco mode and battery protection control patterns."""
    print("=== SYSTEM CONTROL ANALYSIS ===\n")
    
    # Look for longer command packets (eco mode, battery protection)
    system_commands = []
    
    for handle, data in packets:
        # Look for longer packets that might be system controls
        if len(data) >= 20 and data[0:2] == bytes([0xFE, 0xFE]):
            # Check for specific patterns in the data
            hex_str = data.hex(':')
            
            # Look for patterns that change between commands
            if '21:02:00:01' in hex_str or '21:01:00:01' in hex_str:
                system_commands.append({
                    'handle': handle,
                    'length': len(data),
                    'raw_data': hex_str,
                    'data': data
                })
    
    if system_commands:
        print("System Control Commands (Likely Eco Mode / Battery Protection):")
        print("Handle  | Length | Key Bytes | Raw Data")
        print("-" * 80)
        
        for cmd in system_commands[-20:]:  # Show last 20 commands
            data = cmd['data']
            # Extract key bytes that likely control settings
            if len(data) >= 8:
                key_bytes = f"{data[3]:02x}:{data[6]:02x}:{data[7]:02x}"
            else:
                key_bytes = "N/A"
            
            print(f"{cmd['handle']} | {cmd['length']:2d}     | {key_bytes:8s} | {cmd['raw_data']}")
        print()

def analyze_patterns(packets: List[Tuple[str, bytes]]):
    """Look for repeating patterns and protocol structure."""
    print("=== PROTOCOL PATTERN ANALYSIS ===\n")
    
    # Analyze command/response patterns
    handles = {}
    for handle, data in packets:
        if handle not in handles:
            handles[handle] = []
        handles[handle].append(data)
    
    print("Handle Analysis:")
    for handle, data_list in handles.items():
        unique_lengths = set(len(d) for d in data_list)
        print(f"{handle}: {len(data_list)} packets, lengths: {sorted(unique_lengths)}")
    
    print("\nCommon Packet Prefixes:")
    prefixes = {}
    for handle, data in packets:
        if len(data) >= 4:
            prefix = data[:4].hex(':')
            if prefix not in prefixes:
                prefixes[prefix] = 0
            prefixes[prefix] += 1
    
    for prefix, count in sorted(prefixes.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {prefix}: {count} packets")

def generate_control_functions():
    """Generate Python functions for controlling the Alta 80."""
    print("\n=== GENERATED CONTROL FUNCTIONS ===\n")
    
    control_code = '''
class Alta80Controls:
    """Control commands for Goal Zero Alta 80."""
    
    def __init__(self, ble_manager):
        self.ble_manager = ble_manager
    
    def set_zone1_temperature(self, temp_fahrenheit: int) -> bytes:
        """Set Zone 1 temperature setpoint.
        
        Args:
            temp_fahrenheit: Temperature in Fahrenheit (-5 to 68)
            
        Returns:
            Command bytes to send
        """
        if not (-5 <= temp_fahrenheit <= 68):
            raise ValueError("Temperature must be between -5°F and 68°F")
        
        temp_hex = temp_fahrenheit & 0xFF  # Handle negative temps
        checksum = (0x04 + 0x05 + temp_hex + 0x02) & 0xFF
        
        return bytes([0xFE, 0xFE, 0x04, 0x05, temp_hex, 0x02, checksum])
    
    def set_zone2_temperature(self, temp_fahrenheit: int) -> bytes:
        """Set Zone 2 temperature setpoint.
        
        Args:
            temp_fahrenheit: Temperature in Fahrenheit (0 to 35)
            
        Returns:
            Command bytes to send
        """
        if not (0 <= temp_fahrenheit <= 35):
            raise ValueError("Temperature must be between 0°F and 35°F")
        
        temp_hex = temp_fahrenheit & 0xFF
        checksum = (0x04 + 0x06 + temp_hex + 0x02) & 0xFF
        
        return bytes([0xFE, 0xFE, 0x04, 0x06, temp_hex, 0x02, checksum])
    
    def set_eco_mode(self, enabled: bool) -> bytes:
        """Set eco mode on/off.
        
        Args:
            enabled: True to enable eco mode, False to disable
            
        Returns:
            Command bytes to send
        """
        # Based on pattern analysis - this needs refinement with more data
        eco_byte = 0x02 if enabled else 0x01
        
        base_cmd = [0xFE, 0xFE, 0x21, eco_byte, 0x00, 0x01, 0x00, 0x00, 0x00, 0x44, 
                   0xFC, 0x04, 0x00, 0x01, 0xFE, 0xFE, 0x02, 0x00, 0x03, 0x64]
        
        return bytes(base_cmd)
    
    def set_battery_protection(self, level: str) -> bytes:
        """Set battery protection level.
        
        Args:
            level: "low", "med", or "high"
            
        Returns:
            Command bytes to send
        """
        level_map = {
            "low": 0x00,
            "med": 0x01, 
            "high": 0x02
        }
        
        if level not in level_map:
            raise ValueError("Level must be 'low', 'med', or 'high'")
        
        level_byte = level_map[level]
        
        # This is a complex command - needs more analysis
        base_cmd = [0xFE, 0xFE, 0x1C, 0x02, 0x00, 0x01, 0x01, level_byte, 0x00, 0x44,
                   0xFC, 0x04, 0x00, 0x01, 0xFE, 0xFE, 0x02, 0x00, 0x23, 0x00,
                   0x00, 0x04, 0xFE, 0xFE, 0x02, 0x00, 0x00, 0x00, 0x00, 0x07]
        
        # Calculate checksum for last byte
        checksum = sum(base_cmd[20:29]) & 0xFF
        base_cmd.append(checksum)
        
        return bytes(base_cmd)
    
    async def send_command(self, command: bytes) -> bool:
        """Send a command to the Alta 80.
        
        Args:
            command: Command bytes to send
            
        Returns:
            True if command was sent successfully
        """
        try:
            await self.ble_manager.send_command(command)
            return True
        except Exception as e:
            print(f"Failed to send command: {e}")
            return False

# Usage examples:
# controls = Alta80Controls(ble_manager)
# 
# # Set zone 1 to 50°F
# cmd = controls.set_zone1_temperature(50)
# await controls.send_command(cmd)
#
# # Set zone 2 to 25°F  
# cmd = controls.set_zone2_temperature(25)
# await controls.send_command(cmd)
#
# # Enable eco mode
# cmd = controls.set_eco_mode(True)
# await controls.send_command(cmd)
#
# # Set battery protection to medium
# cmd = controls.set_battery_protection("med")
# await controls.send_command(cmd)
'''
    
    print(control_code)

def main():
    """Main analysis function."""
    filename = "testing/Alta80_full_range_noStatus.csv"
    
    print("Goal Zero Alta 80 BLE Control Analysis")
    print("=" * 50)
    
    try:
        packets = parse_csv_data(filename)
        print(f"Loaded {len(packets)} BLE packets\n")
        
        analyze_temperature_setpoints(packets)
        analyze_system_controls(packets)
        analyze_patterns(packets)
        generate_control_functions()
        
    except FileNotFoundError:
        print(f"Error: Could not find {filename}")
        print("Make sure the CSV file is in the correct location.")
    except Exception as e:
        print(f"Error analyzing data: {e}")

if __name__ == "__main__":
    main()
