#!/usr/bin/env python3
"""
Test setpoint parsing for Alta 80.
Tests the parsing of temperature setpoints from bytes 8 and 22.
"""

def parse_signed_byte(byte_value):
    """Convert unsigned byte to signed integer."""
    if byte_value > 127:
        return byte_value - 256
    return byte_value

def test_setpoint_parsing():
    """Test parsing of setpoint values."""
    print("=== Testing Setpoint Parsing ===\n")
    
    # Test cases based on expected Fahrenheit values
    test_cases = [
        # (byte_value, expected_fahrenheit, description)
        (68, 68, "68°F (room temp)"),
        (32, 32, "32°F (freezing)"),
        (0, 0, "0°F"),
        (251, -5, "-5°F (minimum Zone 1)"),  # 251 = 256 - 5
        (35, 35, "35°F (maximum Zone 2)"),
        (255, -1, "-1°F"),  # 255 = 256 - 1
    ]
    
    print("Setpoint Value Tests:")
    print("Byte | Signed | Expected | Match")
    print("-" * 35)
    
    for byte_val, expected, desc in test_cases:
        signed_val = parse_signed_byte(byte_val)
        match = "✓" if signed_val == expected else "✗"
        print(f"{byte_val:3d}  | {signed_val:6d} | {expected:8d} | {match} {desc}")

def test_sample_data():
    """Test with sample data that might come from the device."""
    print("\n=== Testing Sample Data ===\n")
    
    # Simulate a 36-byte response with setpoint data
    sample_data = [0] * 36
    
    # Set some example values
    sample_data[8] = 45    # Zone 1 setpoint: 45°F
    sample_data[22] = 25   # Zone 2 setpoint: 25°F
    sample_data[18] = 5    # Zone 1 temp: 5°C
    sample_data[35] = 2    # Zone 2 temp: 2°C
    
    print("Sample Status Data (selected bytes):")
    print("Byte  8 (Zone 1 setpoint): {} -> {}°F".format(sample_data[8], parse_signed_byte(sample_data[8])))
    print("Byte 18 (Zone 1 temp):     {} -> {}°C".format(sample_data[18], parse_signed_byte(sample_data[18])))
    print("Byte 22 (Zone 2 setpoint): {} -> {}°F".format(sample_data[22], parse_signed_byte(sample_data[22])))
    print("Byte 35 (Zone 2 temp):     {} -> {}°C".format(sample_data[35], parse_signed_byte(sample_data[35])))
    
    # Test with negative values
    sample_data[8] = 251   # Zone 1 setpoint: -5°F (minimum)
    sample_data[22] = 255  # Zone 2 setpoint: -1°F (below range)
    
    print("\nSample with Negative Values:")
    print("Byte  8 (Zone 1 setpoint): {} -> {}°F".format(sample_data[8], parse_signed_byte(sample_data[8])))
    print("Byte 22 (Zone 2 setpoint): {} -> {}°F".format(sample_data[22], parse_signed_byte(sample_data[22])))

def test_command_verification():
    """Verify that our commands will set the correct setpoint bytes."""
    print("\n=== Command vs Setpoint Verification ===\n")
    
    # Our command generation uses the same logic
    def create_zone1_temp_command(temp_f):
        temp_f = max(-5, min(68, temp_f))
        temp_hex = temp_f & 0xFF
        return temp_hex
    
    def create_zone2_temp_command(temp_f):
        temp_f = max(0, min(35, temp_f))
        temp_hex = temp_f & 0xFF
        return temp_hex
    
    print("Zone 1 Command Byte vs Expected Setpoint:")
    print("Temp°F | Cmd Byte | Parsed | Match")
    print("-" * 35)
    
    for temp in [68, 50, 32, 0, -5]:
        cmd_byte = create_zone1_temp_command(temp)
        parsed = parse_signed_byte(cmd_byte)
        match = "✓" if parsed == temp else "✗"
        print(f"{temp:4d}°F | {cmd_byte:8d} | {parsed:6d} | {match}")
    
    print("\nZone 2 Command Byte vs Expected Setpoint:")
    print("Temp°F | Cmd Byte | Parsed | Match")
    print("-" * 35)
    
    for temp in [35, 25, 15, 5, 0]:
        cmd_byte = create_zone2_temp_command(temp)
        parsed = parse_signed_byte(cmd_byte)
        match = "✓" if parsed == temp else "✗"
        print(f"{temp:4d}°F | {cmd_byte:8d} | {parsed:6d} | {match}")

def main():
    """Run all tests."""
    print("Alta 80 Temperature Setpoint Parsing Tests")
    print("=" * 50)
    
    test_setpoint_parsing()
    test_sample_data()
    test_command_verification()
    
    print("\n✓ Setpoint parsing tests completed!")
    print("\nNow the integration will:")
    print("  - Read current setpoints from bytes 8 and 22")
    print("  - Display them as sensors in Home Assistant")
    print("  - Use them for proper button increment/decrement")
    print("  - Show them as current values in number entities")

if __name__ == "__main__":
    main()
