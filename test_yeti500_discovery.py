#!/usr/bin/env python3
"""
Test script for Yeti 500 device detection and discovery functionality.
This script tests the device registry, detection patterns, and basic discovery setup.
"""

import sys
import logging
import asyncio
from typing import Any

# Add the custom component path
sys.path.insert(0, 'custom_components/goalzero_ble')

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import with proper module path
from custom_components.goalzero_ble.device_registry import DeviceRegistry
from custom_components.goalzero_ble.devices.yeti500 import Yeti500Device
from custom_components.goalzero_ble.const import DEVICE_TYPE_YETI500, YETI_500_MODEL

def test_device_patterns():
    """Test Yeti 500 device name pattern detection."""
    print("=== Testing Yeti 500 Device Pattern Detection ===")
    
    # Test valid Yeti 500 device names
    valid_names = [
        "gzy5c-1A2B3C4D5E6F",
        "gzy5c-AABBCCDDEEFF", 
        "gzy5c-123456789ABC",
        "GZY5C-1A2B3C4D5E6F"  # Test case insensitive
    ]
    
    # Test invalid device names
    invalid_names = [
        "gzy5c-123",  # Too short
        "gzy5c-1A2B3C4D5E6FG",  # Too long
        "gzy5d-1A2B3C4D5E6F",  # Wrong prefix
        "gzf1-80-1A2B3C",  # Alta 80 pattern
        "random-device-name"
    ]
    
    print("Testing VALID device names:")
    for name in valid_names:
        device_type = DeviceRegistry.detect_device_type(name)
        is_supported = DeviceRegistry.is_supported_device(name)
        model = DeviceRegistry.get_device_model(device_type) if device_type else "Unknown"
        
        print(f"  {name} -> Type: {device_type}, Supported: {is_supported}, Model: {model}")
        assert device_type == DEVICE_TYPE_YETI500, f"Expected Yeti 500, got {device_type}"
        assert is_supported, f"Device {name} should be supported"
        assert model == YETI_500_MODEL, f"Expected {YETI_500_MODEL}, got {model}"
    
    print("\nTesting INVALID device names:")
    for name in invalid_names:
        device_type = DeviceRegistry.detect_device_type(name)
        is_supported = DeviceRegistry.is_supported_device(name)
        
        print(f"  {name} -> Type: {device_type}, Supported: {is_supported}")
        assert device_type != DEVICE_TYPE_YETI500, f"Device {name} should not be detected as Yeti 500"
        assert not is_supported or device_type != DEVICE_TYPE_YETI500, f"Device {name} should not be supported as Yeti 500"
    
    print("✅ All device pattern tests passed!")

def test_device_creation():
    """Test Yeti 500 device instance creation."""
    print("\n=== Testing Yeti 500 Device Creation ===")
    
    device_name = "gzy5c-1A2B3C4D5E6F"
    device_address = "AA:BB:CC:DD:EE:FF"
    
    # Test device type detection
    device_type = DeviceRegistry.detect_device_type(device_name)
    print(f"Detected device type: {device_type}")
    
    # Test device creation
    assert device_type is not None, f"Device type should not be None for {device_name}"
    device = DeviceRegistry.create_device(device_type, device_address, device_name)
    print(f"Created device: {device}")
    print(f"Device type: {type(device).__name__}")
    assert device is not None, "Device creation should not return None"
    print(f"Device address: {device.address}")
    print(f"Device name: {device.name}")
    print(f"Device model: {device.model}")
    
    assert isinstance(device, Yeti500Device), f"Expected Yeti500Device, got {type(device)}"
    assert device.address == device_address, f"Address mismatch"
    assert device.name == device_name, f"Name mismatch"
    assert device.model == YETI_500_MODEL, f"Model mismatch"
    
    print("✅ Device creation test passed!")

def test_device_capabilities():
    """Test Yeti 500 device capabilities and interface."""
    print("\n=== Testing Yeti 500 Device Capabilities ===")
    
    device = Yeti500Device("AA:BB:CC:DD:EE:FF", "gzy5c-1A2B3C4D5E6F")
    
    # Test sensor definitions (should be empty in discovery phase)
    sensors = device.get_sensors()
    print(f"Sensors defined: {len(sensors)}")
    print(f"Sensor list: {sensors}")
    
    # Test button definitions (should be empty in discovery phase)
    buttons = device.get_buttons()
    print(f"Buttons defined: {len(buttons)}")
    print(f"Button list: {buttons}")
    
    # Test default data structure
    default_data = device._get_default_data()
    print(f"Default data: {default_data}")
    
    assert len(sensors) == 0, "Yeti 500 should have no sensors in discovery phase"
    assert len(buttons) == 0, "Yeti 500 should have no buttons in discovery phase"
    assert isinstance(default_data, dict), "Default data should be a dictionary"
    
    print("✅ Device capabilities test passed!")

def test_config_flow_preview():
    """Test how the device would appear in the Home Assistant config flow."""
    print("\n=== Testing Config Flow Preview ===")
    
    device_name = "gzy5c-AABBCCDDEEFF"
    device_type = DeviceRegistry.detect_device_type(device_name)
    assert device_type is not None, f"Device type should not be None for {device_name}"
    model = DeviceRegistry.get_device_model(device_type)
    
    # Simulate what the user would see in the config flow
    preview_title = f"{model} ({device_name})"
    preview_description = f"Do you want to set up the Goal Zero device **{device_name}** ({model}) at address AA:BB:CC:DD:EE:FF?"
    
    print(f"Config flow preview:")
    print(f"  Title: {preview_title}")
    print(f"  Description: {preview_description}")
    
    assert "Yeti 500" in preview_title, "Preview should show Yeti 500"
    assert device_name in preview_title, "Preview should show device name"
    assert "gzy5c-" in preview_description, "Description should include device name"
    
    print("✅ Config flow preview test passed!")

async def test_discovery_simulation():
    """Simulate the discovery process without actual BLE connection."""
    print("\n=== Testing Discovery Simulation ===")
    
    device = Yeti500Device("AA:BB:CC:DD:EE:FF", "gzy5c-TESTDEVICE12")
    
    # Test default data without BLE manager
    try:
        data = device._get_default_data()
        print(f"Default data structure: {data}")
        
        # Test parsing with empty responses
        parsed = device._parse_gatt_responses([])
        print(f"Parsed empty responses: {parsed}")
        
        # Test parsing with sample data
        sample_responses = ["FEFE0301020012345678", "AABBCCDDEEFF"]
        parsed_sample = device._parse_gatt_responses(sample_responses)
        print(f"Parsed sample responses: {parsed_sample}")
        
        print("✅ Discovery simulation test passed!")
        
    except Exception as e:
        print(f"❌ Discovery simulation failed: {e}")
        raise

def main():
    """Run all tests."""
    print("Starting Yeti 500 Integration Tests")
    print("=" * 50)
    
    try:
        test_device_patterns()
        test_device_creation()
        test_device_capabilities()
        test_config_flow_preview()
        asyncio.run(test_discovery_simulation())
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("Yeti 500 device detection and discovery is ready!")
        print("\nNext steps:")
        print("1. Install the integration in Home Assistant")
        print("2. Try auto-discovery with a real Yeti 500 device")
        print("3. Check the debug logs for GATT discovery information")
        print("4. Develop entities based on the discovered protocol")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
