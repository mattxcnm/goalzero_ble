"""Constants for the Goal Zero BLE integration."""

DOMAIN = "goalzero_ble"
MANUFACTURER = "Goal Zero"

# Device models
ALTA_80 = "Alta 80"

# BLE Configuration
BLE_SCAN_TIMEOUT = 30
BLE_CONNECT_TIMEOUT = 10
BLE_DISCONNECT_TIMEOUT = 5

# Command payloads
COMMANDS = {
    "status_request": "FEFE03010200",
    "left_setpoint_down": "FEFE040501020600", 
    "left_setpoint_up": "FEFE040500020500",
    "right_setpoint_down": "FEFE040624022A00",
    "right_setpoint_up": "FEFE040623022900",
}

# Eco mode commands (placeholder - will need actual values)
ECO_COMMANDS = {
    "eco_on": "FEFE050100000000",  # Placeholder
    "eco_off": "FEFE050101000000",  # Placeholder
}

# Battery protection commands (placeholder - will need actual values)  
BATTERY_PROTECTION_COMMANDS = {
    "high": "FEFE060100000000",  # Placeholder
    "med": "FEFE060101000000",   # Placeholder
    "low": "FEFE060102000000",   # Placeholder
}

# BLE Service and Characteristic UUIDs (will need to be discovered)
SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"  # Placeholder
WRITE_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # Placeholder
NOTIFY_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # Placeholder

# Update intervals
UPDATE_INTERVAL = 30  # seconds
