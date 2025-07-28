#!/usr/bin/env python3
"""Test script to verify imports and basic functionality of the Goal Zero BLE integration."""

import sys
import os
import logging

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        from goalzero_ble.devices.alta80 import Alta80Device
        logger.info("✅ Alta80Device import successful")
        
        from goalzero_ble.ble_manager import BLEManager
        logger.info("✅ BLEManager import successful")
        
        from goalzero_ble.coordinator import GoalZeroCoordinator
        logger.info("✅ GoalZeroCoordinator import successful")
        
        # Test device instantiation
        device = Alta80Device("Test Device", "AA:BB:CC:DD:EE:FF")
        logger.info("✅ Alta80Device instantiation successful")
        
        # Test sensor creation
        sensors = device.get_sensors()
        logger.info(f"✅ Created {len(sensors)} sensors")
        
        # Check for dual byte entities
        byte_sensors = [s for s in sensors if 'status_byte_' in s['key']]
        discrete_sensors = [s for s in byte_sensors if 'discrete' in s['key']]
        regular_sensors = [s for s in byte_sensors if 'discrete' not in s['key']]
        
        logger.info(f"✅ Regular byte sensors: {len(regular_sensors)}")
        logger.info(f"✅ Discrete byte sensors: {len(discrete_sensors)}")
        
        # Test control creation
        switches = device.get_switches()
        selects = device.get_selects()
        numbers = device.get_numbers()
        
        logger.info(f"✅ Switches: {len(switches)}")
        logger.info(f"✅ Selects: {len(selects)}")
        logger.info(f"✅ Numbers: {len(numbers)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_persistent_connection():
    """Test that BLEManager has the new persistent connection methods."""
    try:
        from goalzero_ble.ble_manager import BLEManager
        
        # Check that the new methods exist
        ble_manager = BLEManager("test_device", "AA:BB:CC:DD:EE:FF")
        
        assert hasattr(ble_manager, 'start_persistent_connection'), "start_persistent_connection method missing"
        assert hasattr(ble_manager, '_maintain_connection'), "_maintain_connection method missing"
        assert hasattr(ble_manager, '_on_disconnect'), "_on_disconnect method missing"
        
        logger.info("✅ BLEManager has all persistent connection methods")
        return True
        
    except Exception as e:
        logger.error(f"❌ Persistent connection test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting Goal Zero BLE integration tests...")
    
    success = True
    success &= test_imports()
    success &= test_persistent_connection()
    
    if success:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed!")
        sys.exit(1)
