"""Goal Zero device definitions and detection."""
from .base import GoalZeroDevice
from .yeti500 import Yeti500Device
from .alta80 import Alta80Device

DEVICE_CLASSES = {
    "yeti500": Yeti500Device,
    "alta80": Alta80Device,
}

def detect_device_type(device_name: str, manufacturer_data: bytes | None = None) -> str | None:
    """Detect Goal Zero device type from BLE advertisement data."""
    if not device_name:
        return None
    
    device_name_lower = device_name.lower()
    
    if "yeti" in device_name_lower and "500" in device_name_lower:
        return "yeti500"
    elif "alta" in device_name_lower and "80" in device_name_lower:
        return "alta80"
    elif "goal zero" in device_name_lower or "goalzero" in device_name_lower:
        # Generic Goal Zero device - default to basic implementation
        return "yeti500"  # Use Yeti500 as base for unknown devices
    
    return None

def create_device(device_type: str, address: str, name: str) -> GoalZeroDevice | None:
    """Create a device instance based on detected type."""
    device_class = DEVICE_CLASSES.get(device_type)
    if device_class:
        return device_class(address, name)
    return None
