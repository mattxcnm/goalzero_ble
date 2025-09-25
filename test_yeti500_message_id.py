#!/usr/bin/env python3
"""
Test script to verify Yeti 500 message ID incrementation.
Verifies that message IDs start at 1 and increment properly for each command.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "custom_components"))

from goalzero_ble.devices.yeti500 import Yeti500Device

def test_message_id_incrementation():
    """Test that message IDs start at 1 and increment properly."""
    print("🧪 Testing Yeti 500 Message ID Incrementation")
    print("=" * 50)
    
    device = Yeti500Device("AA:BB:CC:DD:EE:FF", "Test Yeti 500")
    
    # Test initial state
    print("\n🔍 Testing Initial State...")
    if device._message_id != 1:
        print(f"❌ Expected initial message ID 1, got {device._message_id}")
        return False
    print("✅ Initial message ID is 1")
    
    # Test _get_next_message_id incrementation
    print("\n🔍 Testing Message ID Incrementation...")
    expected_sequence = [1, 2, 3, 4, 5]
    actual_sequence = []
    
    for expected_id in expected_sequence:
        actual_id = device._get_next_message_id()
        actual_sequence.append(actual_id)
        if actual_id != expected_id:
            print(f"❌ Expected ID {expected_id}, got {actual_id}")
            return False
    
    print(f"✅ Message IDs increment correctly: {actual_sequence}")
    
    # Test reset functionality
    print("\n🔍 Testing Message ID Reset...")
    device.reset_message_id()
    if device._message_id != 1:
        print(f"❌ Expected message ID reset to 1, got {device._message_id}")
        return False
    print("✅ Message ID reset works correctly")
    
    # Test that after reset, IDs start from 1 again
    print("\n🔍 Testing Post-Reset Incrementation...")
    first_id_after_reset = device._get_next_message_id()
    if first_id_after_reset != 1:
        print(f"❌ Expected first ID after reset to be 1, got {first_id_after_reset}")
        return False
    
    second_id_after_reset = device._get_next_message_id()
    if second_id_after_reset != 2:
        print(f"❌ Expected second ID after reset to be 2, got {second_id_after_reset}")
        return False
    
    print(f"✅ Post-reset IDs start correctly: {first_id_after_reset}, {second_id_after_reset}")
    
    return True

def test_command_sequence():
    """Test that a typical command sequence uses correct IDs."""
    print("\n🔍 Testing Typical Command Sequence...")
    
    device = Yeti500Device("AA:BB:CC:DD:EE:FF", "Test Yeti 500")
    
    # Simulate the sequence that happens during update_data()
    device.reset_message_id()  # This happens at start of update_data()
    
    # Simulate the three read commands that happen during update
    device_info_id = device._get_next_message_id()  # Should be 1
    config_id = device._get_next_message_id()       # Should be 2  
    status_id = device._get_next_message_id()       # Should be 3
    
    expected_ids = [1, 2, 3]
    actual_ids = [device_info_id, config_id, status_id]
    
    if actual_ids != expected_ids:
        print(f"❌ Expected command sequence {expected_ids}, got {actual_ids}")
        return False
    
    print(f"✅ Command sequence uses correct IDs: {actual_ids}")
    
    # Test control commands continue the sequence
    port_control_id = device._get_next_message_id()  # Should be 4
    charge_profile_id = device._get_next_message_id()  # Should be 5
    
    if port_control_id != 4 or charge_profile_id != 5:
        print(f"❌ Expected control command IDs 4, 5 got {port_control_id}, {charge_profile_id}")
        return False
    
    print(f"✅ Control commands continue sequence: {port_control_id}, {charge_profile_id}")
    
    return True

def test_multiple_sessions():
    """Test that multiple update sessions each start with ID 1."""
    print("\n🔍 Testing Multiple Update Sessions...")
    
    device = Yeti500Device("AA:BB:CC:DD:EE:FF", "Test Yeti 500")
    
    # Simulate first update session
    device.reset_message_id()
    session1_ids = [device._get_next_message_id() for _ in range(3)]
    
    # Simulate second update session  
    device.reset_message_id()
    session2_ids = [device._get_next_message_id() for _ in range(3)]
    
    # Simulate third update session
    device.reset_message_id()
    session3_ids = [device._get_next_message_id() for _ in range(3)]
    
    expected_session_ids = [1, 2, 3]
    
    if session1_ids != expected_session_ids:
        print(f"❌ Session 1 expected {expected_session_ids}, got {session1_ids}")
        return False
    
    if session2_ids != expected_session_ids:
        print(f"❌ Session 2 expected {expected_session_ids}, got {session2_ids}")
        return False
        
    if session3_ids != expected_session_ids:
        print(f"❌ Session 3 expected {expected_session_ids}, got {session3_ids}")
        return False
    
    print(f"✅ All sessions start with IDs: {expected_session_ids}")
    print(f"   Session 1: {session1_ids}")
    print(f"   Session 2: {session2_ids}")
    print(f"   Session 3: {session3_ids}")
    
    return True

def main():
    """Run all message ID tests."""
    tests = [
        test_message_id_incrementation,
        test_command_sequence,
        test_multiple_sessions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} FAILED")
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL MESSAGE ID TESTS PASSED!")
        print("✅ Implementation Summary:")
        print("   • Message IDs start at 1 for each new connection/session")
        print("   • Message IDs increment by 1 for each command sent")  
        print("   • Message IDs reset to 1 for each update_data() call")
        print("   • Multiple sessions each start with ID 1, 2, 3, ...")
        print("   • Control commands continue the sequence within a session")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)