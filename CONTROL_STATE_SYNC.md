# Control State Synchronization - Implementation Summary

## Overview
Updated the Yeti 500 BLE integration to ensure control entity states (switches, numbers, buttons) are synchronized with the actual device status from regular interval polling, rather than using optimistic updates.

## Changes Made

### 1. Device Data Mapping (`yeti500.py`)
**✅ Added control state mappings in `update_data()` method:**
```python
# Control entity states (switches) - map device status to switch states
combined_data.update({
    "acOut_switch": bool(combined_data.get("acOut_status", 0)),
    "v12Out_switch": bool(combined_data.get("v12Out_status", 0)),
    "usbOut_switch": bool(combined_data.get("usbOut_status", 0)),
})
```

**✅ Removed optimistic updates from control commands:**
- `_control_port()` - Now relies on status polling for state updates
- `_set_charge_profile()` - Now relies on config polling for state updates  
- `_set_display_settings()` - Now relies on config polling for state updates

### 2. Switch Entity Updates (`switch.py`)
**✅ Updated `is_on` property to use device data:**
```python
@property
def is_on(self) -> bool | None:
    """Return True if entity is on."""
    if self.coordinator.data:
        # Check if there's a direct mapping for this switch key
        switch_value = self.coordinator.data.get(self._key)
        if switch_value is not None:
            return bool(switch_value)
        # ... legacy fallbacks
```

**✅ Updated turn_on/turn_off methods to use Yeti 500 commands:**
- Now calls `device.set_switch_state()` for Yeti 500
- Falls back to `device.create_switch_command()` for other devices
- Requests immediate coordinator refresh after successful commands

### 3. Number Entity Updates (`number.py`)
**✅ Updated `async_set_native_value()` method:**
- Now calls `device.set_number_value()` for Yeti 500
- Falls back to `device.create_number_set_command()` for other devices
- Requests immediate coordinator refresh after successful commands

**✅ `native_value` property already properly uses device data:**
- Uses `self.coordinator.data.get(self._key)` which picks up our mapped values

### 4. Button Entity Updates (`button.py`)
**✅ Updated `async_press()` method:**
- Now calls `device.send_button_command()` for Yeti 500
- Falls back to `device.create_button_command()` for other devices
- Requests immediate coordinator refresh after successful commands

## Data Flow

### Status Reading (Every 30 seconds by default)
1. **Device Info**: `method: "device"` → Updates device metadata
2. **Config**: `method: "config"` → Updates charge_profile and display settings
3. **Status**: `method: "status"` → Updates battery, ports, system data

### Control Command Flow
1. **User Action**: User toggles switch/changes number/presses button
2. **Command Sent**: JSON-RPC command sent via BLE
3. **No Optimistic Update**: Local state is NOT immediately updated
4. **Immediate Refresh**: Coordinator requests immediate data refresh
5. **State Sync**: Next status poll reads actual device state
6. **Entity Update**: Control entities reflect actual device state

### Entity State Mapping
```
Device Status → Control Entity State
─────────────────────────────────────
ports.acOut.s → acOut_switch
ports.v12Out.s → v12Out_switch  
ports.usbOut.s → usbOut_switch
charge_profile.min → charge_profile_min_soc
charge_profile.max → charge_profile_max_soc
charge_profile.rchg → charge_profile_recharge_soc
display.blackout_time → display_blackout_time
display.brightness → display_brightness
```

## Benefits

### ✅ **True State Synchronization**
- Control entities always reflect actual device state
- No discrepancy between UI and device
- Handles external changes (e.g., physical buttons on device)

### ✅ **Immediate Feedback**  
- Commands trigger immediate coordinator refresh
- Users see state changes within seconds
- No waiting for next regular polling cycle

### ✅ **Robust Error Handling**
- If command fails, entity state remains accurate
- No "stuck" entity states from failed optimistic updates
- Clear distinction between command success and state change

### ✅ **User-Configurable Polling**
- `device.set_status_update_frequency(seconds)` controls how often states sync
- Default 30 seconds, minimum 1 second
- Balances responsiveness with battery/performance

## Result

The integration now ensures that all control entity states (switches, numbers) are always synchronized with the actual device status as captured from regular interval checking, exactly as requested. Users will see control entities update to reflect the true device state within seconds of status changes, whether from Home Assistant commands or external device interactions.
