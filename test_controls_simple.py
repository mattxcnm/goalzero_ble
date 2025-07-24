#!/usr/bin/env python3
"""
Simple test for Alta 80 control command generation.
Tests just the command bytes without Home Assistant dependencies.
"""

def create_zone1_temp_command(temp_f: int) -> bytes:
    """Create Zone 1 temperature setpoint command."""
    temp_f = max(-5, min(68, temp_f))  # Clamp to valid range
    temp_hex = temp_f & 0xFF  # Handle negative temps with 2's complement
    checksum = (0x04 + 0x05 + temp_hex + 0x02) & 0xFF
    
    return bytes([0xFE, 0xFE, 0x04, 0x05, temp_hex, 0x02, checksum])

def create_zone2_temp_command(temp_f: int) -> bytes:
    """Create Zone 2 temperature setpoint command."""
    temp_f = max(0, min(35, temp_f))  # Clamp to valid range
    temp_hex = temp_f & 0xFF
    checksum = (0x04 + 0x06 + temp_hex + 0x02) & 0xFF
    
    return bytes([0xFE, 0xFE, 0x04, 0x06, temp_hex, 0x02, checksum])

def create_eco_mode_command(enabled: bool) -> bytes:
    """Create eco mode on/off command."""
    eco_byte = 0x02 if enabled else 0x01
    return bytes([0xFE, 0xFE, 0x21, eco_byte, 0x00, 0x01, 0x00, 0x00, 0x00, 0x44,
                  0xFC, 0x04, 0x00, 0x01, 0xFE, 0xFE, 0x02, 0x00, 0x03, 0x64])

def create_battery_protection_command(level: str) -> bytes:
    """Create battery protection level command."""
    level_map = {"low": 0x00, "med": 0x01, "high": 0x02}
    
    if level not in level_map:
        raise ValueError(f"Level must be 'low', 'med', or 'high', got: {level}")
    
    level_byte = level_map[level]
    return bytes([0xFE, 0xFE, 0x21, 0x02, 0x00, 0x01, 0x01, level_byte, 0x00, 0x44,
                  0xFC, 0x04, 0x00, 0x01, 0xFE, 0xFE, 0x02, 0x00, 0x03, 0x64])

def test_temperature_commands():
    """Test temperature command generation."""
    print("=== Temperature Command Tests ===\n")
    
    # Test Zone 1 commands
    print("Zone 1 Temperature Commands:")
    test_temps = [68, 50, 32, 0, -5]
    for temp in test_temps:
        cmd = create_zone1_temp_command(temp)
        print(f"  {temp:3d}°F: {cmd.hex(':').upper()}")
    
    # Test Zone 2 commands
    print("\nZone 2 Temperature Commands:")
    test_temps = [35, 25, 15, 5, 0]
    for temp in test_temps:
        cmd = create_zone2_temp_command(temp)
        print(f"  {temp:3d}°F: {cmd.hex(':').upper()}")

def test_system_commands():
    """Test system command generation."""
    print("\n=== System Command Tests ===\n")
    
    # Test eco mode
    print("Eco Mode Commands:")
    for state in [True, False]:
        cmd = create_eco_mode_command(state)
        state_str = "ON " if state else "OFF"
        print(f"  Eco {state_str}: {cmd.hex(':').upper()}")
    
    # Test battery protection
    print("\nBattery Protection Commands:")
    for level in ["low", "med", "high"]:
        cmd = create_battery_protection_command(level)
        print(f"  {level.upper()}: {cmd.hex(':').upper()}")

def verify_against_analysis():
    """Verify commands match the BLE packet analysis."""
    print("\n=== Verification Against Analysis ===\n")
    
    # Verify Zone 1 temp command for 68°F (0x44)
    cmd = create_zone1_temp_command(68)
    expected = "FE:FE:04:05:44:02:4F"
    actual = cmd.hex(':').upper()
    
    print(f"Zone 1 68°F Command:")
    print(f"  Expected: {expected}")
    print(f"  Actual:   {actual}")
    print(f"  Match:    {'✓' if actual == expected else '✗'}")
    
    # Verify Zone 2 temp command for 35°F (0x23)
    cmd = create_zone2_temp_command(35)
    expected = "FE:FE:04:06:23:02:2F"
    actual = cmd.hex(':').upper()
    
    print(f"\nZone 2 35°F Command:")
    print(f"  Expected: {expected}")
    print(f"  Actual:   {actual}")
    print(f"  Match:    {'✓' if actual == expected else '✗'}")
    
    # Test checksum calculation
    print(f"\nChecksum Verification:")
    temp_hex = 0x44  # 68°F
    calc_checksum = (0x04 + 0x05 + temp_hex + 0x02) & 0xFF
    print(f"  Zone 1 68°F: 0x04+0x05+0x44+0x02 = 0x{calc_checksum:02X} (should be 0x4F)")
    
    temp_hex = 0x23  # 35°F
    calc_checksum = (0x04 + 0x06 + temp_hex + 0x02) & 0xFF
    print(f"  Zone 2 35°F: 0x04+0x06+0x23+0x02 = 0x{calc_checksum:02X} (should be 0x2F)")

def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n=== Edge Case Tests ===\n")
    
    print("Zone 1 Boundary Tests:")
    # Test clamping
    cmd_low = create_zone1_temp_command(-10)  # Should clamp to -5
    cmd_high = create_zone1_temp_command(100)  # Should clamp to 68
    print(f"  -10°F (clamped to -5):  {cmd_low.hex(':').upper()}")
    print(f"  100°F (clamped to 68):  {cmd_high.hex(':').upper()}")
    
    print("\nZone 2 Boundary Tests:")
    cmd_low = create_zone2_temp_command(-5)   # Should clamp to 0
    cmd_high = create_zone2_temp_command(50)  # Should clamp to 35
    print(f"  -5°F (clamped to 0):    {cmd_low.hex(':').upper()}")
    print(f"  50°F (clamped to 35):   {cmd_high.hex(':').upper()}")

def main():
    """Run all tests."""
    print("Goal Zero Alta 80 Control Command Verification")
    print("=" * 60)
    
    test_temperature_commands()
    test_system_commands()
    verify_against_analysis()
    test_edge_cases()
    
    print("\n✓ All command generation tests completed!")
    print("\nThese commands can now be used in Home Assistant through:")
    print("  - Button entities for individual adjustments")
    print("  - Number entities for direct setpoint control")
    print("  - Automations and scripts for advanced control")

if __name__ == "__main__":
    main()
