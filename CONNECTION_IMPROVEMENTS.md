# Connection Issue Fixes for Alta 80

## Problems Identified

Based on the error logs, three main connection issues were identified:

1. **ESP_GATT_CONN_FAIL_ESTABLISH** - BLE connection establishment failures
2. **No responses received within 5s** - Device connects but doesn't respond to commands
3. **Connection timeout** - Overall connection timeout issues

## Root Causes

1. **Device Sleep State**: Alta 80 may enter sleep mode and need time to wake up
2. **Connection Timing**: Device needs stabilization time after connection
3. **Command Timing**: Device may need retry logic for commands
4. **Scan Reliability**: Single scan attempts may miss the device

## Solutions Implemented

### 1. Enhanced Device Scanning (`devices/alta80.py`)

**Improvements:**
- Increased scan timeout from 15s to 20s
- Added retry logic with 2 scan attempts
- Better logging of discovered devices
- Longer pause (3s) between scan attempts

```python
# Try scanning twice with longer timeout
for scan_attempt in range(2):
    devices = await BleakScanner.discover(timeout=20.0)
    # ... retry logic
```

### 2. Robust Connection Management

**Connection Retry Logic:**
- Implemented `_connect_and_read_data()` with retry mechanism  
- Different retry delays for different error types:
  - `ESP_GATT_CONN_FAIL_ESTABLISH`: 5 second delay
  - `TimeoutError`: 3 second delay
  - Other errors: 3 second delay
- Maximum 2 connection attempts per update cycle

**Connection Stabilization:**
- Added disconnection callback for better connection tracking
- Increased stabilization delay from 0.5s to 1.0s after connection
- Better error classification and logging

### 3. Improved Command Handling

**Command Retry Logic:**
- Commands now retry up to 2 times if no initial response
- Wait 3 seconds for initial response before retry
- 1 second delay between command attempts

**Enhanced Timeouts:**
- Increased command response timeout from 5s to 12s
- Added notification setup delay (0.5s)
- Better response counting and validation

### 4. Better Error Handling and Logging

**Detailed Error Classification:**
- Specific handling for `ESP_GATT_CONN_FAIL_ESTABLISH`
- Separate handling for `asyncio.TimeoutError`
- Better error type reporting

**Enhanced Logging:**
- Connection attempt tracking
- Response timing information
- Available device discovery logging
- GATT characteristic discovery details

## Code Changes

### Main Implementation (`devices/alta80.py`)

1. **`update_data()` method**: Split into smaller methods for better error handling
2. **`_connect_and_read_data()`**: New method with connection retry logic
3. **`_read_device_data()`**: Improved command handling with retries
4. **Enhanced scanning**: Better device discovery with retry logic

### Testing Tools

1. **`connection_test.py`**: New standalone test script for connection issues
2. **`diagnostic_tool.py`**: Updated with retry logic
3. **`testing/goalzero_gatt_dynamic.py`**: Updated with improved connection handling

## Expected Results

With these improvements, the integration should:

1. **Reduce ESP_GATT_CONN_FAIL_ESTABLISH errors** through retry logic and proper delays
2. **Improve response rates** through command retry and longer timeouts  
3. **Better handle sleeping devices** through enhanced scanning and stabilization
4. **Provide better diagnostics** through detailed error logging

## Testing

### Test the improvements:

```bash
# Test standalone connection
python3 connection_test.py [device_name]

# Test with diagnostic tool
python3 diagnostic_tool.py [device_address] [device_name]

# Test with updated GATT script
python3 testing/goalzero_gatt_dynamic.py
```

### Monitor Home Assistant logs:

Look for these improvements in the logs:
- "✓ Found target device" - Better device discovery
- "Connection attempt X/Y" - Retry logic working
- "Got response on attempt X" - Command retry success
- "Successfully parsed Alta 80 data" - Overall success

## Configuration Recommendations

For best results with the Alta 80:

1. **Update Interval**: Use 30-60 seconds to avoid overwhelming the device
2. **Device Placement**: Ensure device is within good BLE range
3. **Home Assistant**: Monitor logs during initial setup to verify connection patterns

## Backward Compatibility

All changes maintain compatibility with the existing Home Assistant integration. The improvements are transparent to users and only affect the internal connection logic.
