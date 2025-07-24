"""Constants for the Goal Zero BLE integration."""

DOMAIN = "goalzero_ble"
MANUFACTURER = "Goal Zero"

# Configuration keys
CONF_DEVICE_NAME = "device_name"
CONF_UPDATE_INTERVAL = "update_interval"

# Default values
DEFAULT_UPDATE_INTERVAL = 30  # seconds
MIN_UPDATE_INTERVAL = 10
MAX_UPDATE_INTERVAL = 300

# Device name patterns
ALTA_PATTERN = "gzf1-80-"
YETI500_PATTERN = "gzy5c-"

# Device types
DEVICE_TYPE_ALTA80 = "alta80"
DEVICE_TYPE_YETI500 = "yeti500"

# Device models
ALTA_80_MODEL = "Alta 80"
YETI_500_MODEL = "Yeti 500"

# BLE Configuration
BLE_SCAN_TIMEOUT = 30
BLE_CONNECT_TIMEOUT = 12  # Reduced from 15 to avoid 10+2s timeout pattern
BLE_DISCONNECT_TIMEOUT = 5  # Reduced from 10 to disconnect faster
BLE_COMMAND_TIMEOUT = 8    # Increased from 5 for better reliability

# Alta 80 GATT Configuration
ALTA80_WRITE_HANDLE = 0x000A
ALTA80_READ_HANDLE = 0x000C
ALTA80_STATUS_COMMAND = "FEFE03010200"

# Yeti 500 GATT Configuration (to be discovered)
YETI500_WRITE_HANDLE = 0x000A  # Placeholder
YETI500_READ_HANDLE = 0x000C   # Placeholder
YETI500_STATUS_COMMAND = "FEFE03010200"  # Placeholder

# Command definitions for each device type
DEVICE_COMMANDS = {
    DEVICE_TYPE_ALTA80: {
        "status_request": "FEFE03010200",
        "temp_down": "FEFE040501020600",
        "temp_up": "FEFE040500020500",
        "power_on": "FEFE050100000000",   # To be verified
        "power_off": "FEFE050101000000",  # To be verified
        "eco_on": "FEFE060100000000",     # To be verified
        "eco_off": "FEFE060101000000",    # To be verified
    },
    DEVICE_TYPE_YETI500: {
        "status_request": "FEFE03010200",  # To be verified
        "power_on": "FEFE050100000000",    # To be verified
        "power_off": "FEFE050101000000",   # To be verified
    }
}

# Device GATT handles
DEVICE_HANDLES = {
    DEVICE_TYPE_ALTA80: {
        "write": ALTA80_WRITE_HANDLE,
        "read": ALTA80_READ_HANDLE,
    },
    DEVICE_TYPE_YETI500: {
        "write": YETI500_WRITE_HANDLE,
        "read": YETI500_READ_HANDLE,
    }
}
