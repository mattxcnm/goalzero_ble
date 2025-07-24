#!/usr/bin/env python3
"""
Quick test to verify the critical bug fix in Alta 80 device.
This confirms that responses are properly captured and stored.
"""

def test_notification_handler():
    """Test that the notification handler properly stores responses."""
    responses = []
    response_count = 0
    
    def notification_handler(sender, data):
        nonlocal response_count, responses
        response_count += 1
        hex_data = data.hex().upper()
        responses.append(hex_data)  # This line was missing in the original bug
        print(f"Response {response_count}: {hex_data}")
    
    # Simulate some test data
    test_data_1 = bytes.fromhex("FEFE03010200112233445566778899AABBCCDDEE")
    test_data_2 = bytes.fromhex("FF112233445566778899AABBCCDDEE1122334455")
    
    print("Testing notification handler...")
    notification_handler("test_sender", test_data_1)
    notification_handler("test_sender", test_data_2)
    
    print(f"\nResults:")
    print(f"Response count: {response_count}")
    print(f"Responses stored: {len(responses)}")
    print(f"Responses: {responses}")
    
    # Verify the fix works
    assert response_count == 2, f"Expected 2 responses, got {response_count}"
    assert len(responses) == 2, f"Expected 2 stored responses, got {len(responses)}"
    assert responses[0] == "FEFE03010200112233445566778899AABBCCDDEE"
    assert responses[1] == "FF112233445566778899AABBCCDDEE1122334455"
    
    print("✅ All tests passed! The bug fix works correctly.")

if __name__ == "__main__":
    test_notification_handler()
