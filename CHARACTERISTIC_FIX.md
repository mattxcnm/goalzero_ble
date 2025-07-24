# CHARACTERISTIC SELECTION FIX

## Problem Identified ✅

From your debug logs, the issue is **WRONG CHARACTERISTIC SELECTION**:

### Current (WRONG) Selection:
- **Write**: `0x0003` (Device Name characteristic in Generic Access Service)
- **Read/Notify**: `0x000D` (Correct - Custom service notification characteristic)

### Should Be:
- **Write**: `0x000B` (write-without-response in custom service `00001234`)  
- **Read/Notify**: `0x000D` (Correct - already selected properly)

## Root Cause
The integration was selecting the **first** write characteristic it found (`0x0003` - Device Name), instead of the **correct** write characteristic (`0x000B` - Command characteristic).

Writing commands to the Device Name characteristic obviously doesn't work!

## Fix Applied
Modified characteristic selection logic to:
1. **Prioritize `write-without-response`** characteristics
2. **Prefer characteristics in custom service** (`00001234-...`)
3. **Avoid generic service characteristics** for commands

## Expected Log Changes
After restarting Home Assistant, you should see:

### Before (Wrong):
```
✓ Selected write characteristic: 0x0003
✓ Selected read/notify characteristic: 0x000D
```

### After (Correct):
```
✓ Selected write-without-response characteristic: 0x000B
✓ Selected read/notify characteristic: 0x000D
✓ Using write characteristic 0x000B and read/notify characteristic 0x000D
```

## What to Test
1. **Restart Home Assistant** to load the fixed code
2. **Check the GATT discovery logs** - should now select `0x000B` for write
3. **Look for responses** - the device should now respond to commands
4. **Verify sensor data** - should get actual temperature and status values

## Why This Should Work
- Your logs prove the device **connects successfully** ✅
- Your logs prove **GATT discovery works** ✅  
- Your logs prove the **correct characteristics exist** ✅
- We were just **writing to the wrong characteristic** ❌ → ✅

The device has been ready to respond all along - we were just knocking on the wrong door!

## Signs of Success
Look for:
- `🔔 Alta 80 Notification` messages (responses received)
- Actual temperature values in sensor entities
- No more "No response to command" warnings

This fix should resolve the communication issue completely.
