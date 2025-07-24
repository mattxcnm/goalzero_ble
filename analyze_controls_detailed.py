#!/usr/bin/env python3
"""
Detailed analysis and verification of Alta 80 control commands.
"""

def verify_temperature_commands():
    """Verify the temperature command structure and checksums."""
    print("=== TEMPERATURE COMMAND VERIFICATION ===\n")
    
    # Test Zone 1 commands
    print("Zone 1 Temperature Commands:")
    print("Temp °F | Command Bytes | Checksum Calculation")
    print("-" * 55)
    
    for temp in [68, 50, 25, 0, -5]:
        temp_hex = temp & 0xFF
        # Checksum: sum of bytes 2-5 (04 + 05 + temp + 02)
        checksum = (0x04 + 0x05 + temp_hex + 0x02) & 0xFF
        cmd = f"FE FE 04 05 {temp_hex:02X} 02 {checksum:02X}"
        calc = f"0x04+0x05+0x{temp_hex:02X}+0x02 = 0x{checksum:02X}"
        print(f"{temp:3d}°F   | {cmd} | {calc}")
    
    print("\nZone 2 Temperature Commands:")
    print("Temp °F | Command Bytes | Checksum Calculation")
    print("-" * 55)
    
    for temp in [35, 25, 15, 5, 0]:
        temp_hex = temp & 0xFF
        # Checksum: sum of bytes 2-5 (04 + 06 + temp + 02)  
        checksum = (0x04 + 0x06 + temp_hex + 0x02) & 0xFF
        cmd = f"FE FE 04 06 {temp_hex:02X} 02 {checksum:02X}"
        calc = f"0x04+0x06+0x{temp_hex:02X}+0x02 = 0x{checksum:02X}"
        print(f"{temp:3d}°F   | {cmd} | {calc}")

def analyze_system_commands():
    """Analyze eco mode and battery protection patterns."""
    print("\n=== SYSTEM COMMAND ANALYSIS ===\n")
    
    # From the data, we can see these patterns:
    # Eco mode appears to be controlled by byte 3 (01=off, 02=on)
    # Battery protection appears to be in bytes 6-7 (eco mode, protection level)
    
    print("Eco Mode Commands (from packet analysis):")
    print("fe:fe:21:01:00:01:00:00:00:44:fc:04:00:01:fe:fe:02:00:03:64  # Eco OFF")
    print("fe:fe:21:02:00:01:xx:xx:00:44:fc:04:00:01:fe:fe:02:00:03:64  # Eco ON")
    print("")
    
    print("Battery Protection Commands (from packet analysis):")
    print("Based on the pattern fe:fe:21:02:00:01:01:xx:00...")
    print("Byte 7 appears to control battery protection level:")
    print("  00 = Low")
    print("  01 = Medium") 
    print("  02 = High")
    
    print("\nComplex Battery Protection Commands (longer format):")
    print("fe:fe:1c:02:00:01:01:xx:00:44:fc:04:00:01:fe:fe:02:00:23:00:00:04:fe:fe:02:00:00:00:00:07:xx")
    print("Where xx is the protection level (00/01/02)")

def generate_button_entities():
    """Generate button entity definitions for Home Assistant."""
    print("\n=== HOME ASSISTANT BUTTON ENTITIES ===\n")
    
    button_code = '''
# Add these to the Alta80Device class in devices/alta80.py

def get_button_definitions(self) -> list[dict[str, Any]]:
    """Get button entity definitions for Alta 80 controls."""
    return [
        {
            "name": "Zone 1 Temp Up",
            "key": "zone1_temp_up",
            "icon": "mdi:thermometer-plus",
            "command": self._create_zone1_temp_command(self._zone1_temp + 1),
        },
        {
            "name": "Zone 1 Temp Down", 
            "key": "zone1_temp_down",
            "icon": "mdi:thermometer-minus",
            "command": self._create_zone1_temp_command(self._zone1_temp - 1),
        },
        {
            "name": "Zone 2 Temp Up",
            "key": "zone2_temp_up", 
            "icon": "mdi:thermometer-plus",
            "command": self._create_zone2_temp_command(self._zone2_temp + 1),
        },
        {
            "name": "Zone 2 Temp Down",
            "key": "zone2_temp_down",
            "icon": "mdi:thermometer-minus", 
            "command": self._create_zone2_temp_command(self._zone2_temp - 1),
        },
        {
            "name": "Toggle Eco Mode",
            "key": "toggle_eco_mode",
            "icon": "mdi:leaf",
            "command": self._create_eco_mode_command(not self._eco_mode),
        },
        {
            "name": "Cycle Battery Protection",
            "key": "cycle_battery_protection",
            "icon": "mdi:battery-heart",
            "command": self._create_battery_protection_cycle_command(),
        },
    ]

def _create_zone1_temp_command(self, temp_f: int) -> bytes:
    """Create Zone 1 temperature command."""
    temp_f = max(-5, min(68, temp_f))  # Clamp to valid range
    temp_hex = temp_f & 0xFF
    checksum = (0x04 + 0x05 + temp_hex + 0x02) & 0xFF
    return bytes([0xFE, 0xFE, 0x04, 0x05, temp_hex, 0x02, checksum])

def _create_zone2_temp_command(self, temp_f: int) -> bytes:
    """Create Zone 2 temperature command.""" 
    temp_f = max(0, min(35, temp_f))  # Clamp to valid range
    temp_hex = temp_f & 0xFF
    checksum = (0x04 + 0x06 + temp_hex + 0x02) & 0xFF
    return bytes([0xFE, 0xFE, 0x04, 0x06, temp_hex, 0x02, checksum])

def _create_eco_mode_command(self, enabled: bool) -> bytes:
    """Create eco mode command."""
    eco_byte = 0x02 if enabled else 0x01
    return bytes([0xFE, 0xFE, 0x21, eco_byte, 0x00, 0x01, 0x00, 0x00, 0x00, 0x44,
                  0xFC, 0x04, 0x00, 0x01, 0xFE, 0xFE, 0x02, 0x00, 0x03, 0x64])

def _create_battery_protection_cycle_command(self) -> bytes:
    """Create battery protection cycle command."""
    # Cycle through low(0) -> med(1) -> high(2) -> low(0)
    current_level = self._battery_protection_level
    next_level = (current_level + 1) % 3
    
    return bytes([0xFE, 0xFE, 0x21, 0x02, 0x00, 0x01, 0x01, next_level, 0x00, 0x44,
                  0xFC, 0x04, 0x00, 0x01, 0xFE, 0xFE, 0x02, 0x00, 0x03, 0x64])
'''
    
    print(button_code)

def main():
    """Run all analyses."""
    verify_temperature_commands()
    analyze_system_commands() 
    generate_button_entities()

if __name__ == "__main__":
    main()
