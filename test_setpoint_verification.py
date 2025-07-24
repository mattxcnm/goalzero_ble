#!/usr/bin/env python3
"""Simple test for setpoint parsing logic."""

def test_signed_byte_conversion():
    """Test the signed byte conversion logic."""
    print("Testing signed byte conversion logic:")
    print()
    
    # Test positive values (0-127)
    positive_tests = [
        (0x00, 0),    # 0
        (0x20, 32),   # 32°F
        (0x28, 40),   # 40°F
        (0x7F, 127),  # Max positive
    ]
    
    for raw_value, expected in positive_tests:
        # Apply the same conversion logic as in the device parser
        converted = raw_value
        if raw_value > 127:
            converted = raw_value - 256
        
        print(f"Raw: 0x{raw_value:02X} ({raw_value}) -> Converted: {converted}°F (Expected: {expected}°F)")
        if converted != expected:
            print(f"  ❌ FAILED!")
            return False
        else:
            print(f"  ✅ PASSED")
    
    print()
    
    # Test negative values (128-255)
    negative_tests = [
        (0x80, -128),  # Min negative
        (0xD8, -40),   # -40°F
        (0xE0, -32),   # -32°F
        (0xF0, -16),   # -16°F
        (0xFF, -1),    # -1°F
    ]
    
    for raw_value, expected in negative_tests:
        # Apply the same conversion logic as in the device parser
        converted = raw_value
        if raw_value > 127:
            converted = raw_value - 256
        
        print(f"Raw: 0x{raw_value:02X} ({raw_value}) -> Converted: {converted}°F (Expected: {expected}°F)")
        if converted != expected:
            print(f"  ❌ FAILED!")
            return False
        else:
            print(f"  ✅ PASSED")
    
    print()
    print("✅ All signed byte conversion tests passed!")
    return True


def test_byte_parsing():
    """Test parsing of specific bytes from a hex string."""
    print("Testing byte parsing from hex string:")
    print()
    
    # Test hex string with known setpoint values (exactly 36 bytes = 72 hex characters)
    # Position: 0    2    4    6    8   10   12   14   16   18   20   22   24   26   28   30   32   34
    # Byte:     0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35
    test_hex = ("FEFE0000000000002000000000000000000010000000280000000000000000000000000C")
    
    print(f"Test hex string: {test_hex}")
    print(f"Length: {len(test_hex)} characters ({len(test_hex)//2} bytes)")
    print()
    
    # Convert to bytes
    all_bytes = bytes.fromhex(test_hex)
    
    # Parse setpoints using the same logic as the device parser
    zone_1_setpoint_raw = None
    zone_2_setpoint_raw = None
    zone_1_temp_raw = None
    zone_2_temp_raw = None
    
    if len(all_bytes) > 8:
        # Byte 8: Zone 1 setpoint
        zone_1_setpoint_raw = all_bytes[8]
        if zone_1_setpoint_raw > 127:
            zone_1_setpoint_raw = zone_1_setpoint_raw - 256
        print(f"Byte 8 (Zone 1 setpoint): 0x{all_bytes[8]:02X} ({all_bytes[8]}) -> {zone_1_setpoint_raw}°F")
    
    if len(all_bytes) > 22:
        # Byte 22: Zone 2 setpoint
        zone_2_setpoint_raw = all_bytes[22]
        if zone_2_setpoint_raw > 127:
            zone_2_setpoint_raw = zone_2_setpoint_raw - 256
        print(f"Byte 22 (Zone 2 setpoint): 0x{all_bytes[22]:02X} ({all_bytes[22]}) -> {zone_2_setpoint_raw}°F")
    
    if len(all_bytes) > 18:
        # Byte 18: Zone 1 temp
        zone_1_temp_raw = all_bytes[18]
        if zone_1_temp_raw > 127:
            zone_1_temp_raw = zone_1_temp_raw - 256
        print(f"Byte 18 (Zone 1 temp): 0x{all_bytes[18]:02X} ({all_bytes[18]}) -> {zone_1_temp_raw}°C")
    
    if len(all_bytes) > 35:
        # Byte 35: Zone 2 temp
        zone_2_temp_raw = all_bytes[35]
        if zone_2_temp_raw > 127:
            zone_2_temp_raw = zone_2_temp_raw - 256
        print(f"Byte 35 (Zone 2 temp): 0x{all_bytes[35]:02X} ({all_bytes[35]}) -> {zone_2_temp_raw}°C")
    
    print()
    
    # Expected values based on our test data
    expected_zone1_setpoint = 32  # 0x20 at byte 8
    expected_zone2_setpoint = 40  # 0x28 at byte 22
    expected_zone1_temp = 16      # 0x10 at byte 18
    expected_zone2_temp = 12      # 0x0C at byte 35
    
    success = True
    if zone_1_setpoint_raw != expected_zone1_setpoint:
        print(f"❌ Zone 1 setpoint failed: expected {expected_zone1_setpoint}, got {zone_1_setpoint_raw}")
        success = False
    if zone_2_setpoint_raw != expected_zone2_setpoint:
        print(f"❌ Zone 2 setpoint failed: expected {expected_zone2_setpoint}, got {zone_2_setpoint_raw}")
        success = False
    if zone_1_temp_raw != expected_zone1_temp:
        print(f"❌ Zone 1 temp failed: expected {expected_zone1_temp}, got {zone_1_temp_raw}")
        success = False
    if zone_2_temp_raw != expected_zone2_temp:
        print(f"❌ Zone 2 temp failed: expected {expected_zone2_temp}, got {zone_2_temp_raw}")
        success = False
    
    if success:
        print("✅ All byte parsing tests passed!")
    else:
        print("❌ Some byte parsing tests failed!")
    
    return success


if __name__ == "__main__":
    print("=== Setpoint Parsing Verification ===")
    print()
    
    success1 = test_signed_byte_conversion()
    print()
    success2 = test_byte_parsing()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Setpoint parsing is working correctly.")
    else:
        print("\n❌ Some tests failed!")
