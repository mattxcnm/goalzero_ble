"""GATT service discovery utility for Goal Zero devices."""
import asyncio
import logging
from typing import Dict, List, Optional, Tuple

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

_LOGGER = logging.getLogger(__name__)


class GoalZeroGATTDiscovery:
    """GATT service discovery for Goal Zero devices."""

    def __init__(self):
        """Initialize the GATT discovery utility."""
        self.discovered_services: Dict[str, Dict] = {}

    async def find_device_by_name(self, device_name: str, timeout: int = 10) -> Optional[str]:
        """Find device by exact name match and return address."""
        _LOGGER.debug("Scanning for device: %s", device_name)
        devices = await BleakScanner.discover(timeout=timeout)
        
        for device in devices:
            if device.name == device_name:
                _LOGGER.info("Found device: %s (%s)", device.name, device.address)
                return device.address
        
        _LOGGER.warning("Device '%s' not found", device_name)
        _LOGGER.debug("Available devices: %s", [d.name or 'Unknown' for d in devices])
        return None

    async def discover_device_services(
        self, 
        device_address: str
    ) -> Dict[str, Dict]:
        """Discover all GATT services, characteristics, and handles for a device."""
        try:
            async with BleakClient(device_address) as client:
                _LOGGER.info("Connected to device at %s", device_address)
                
                services_info = {}
                services = client.services
                
                for service in services.services.values():
                    service_info = {
                        "uuid": str(service.uuid),
                        "handle": service.handle,
                        "characteristics": {}
                    }
                    
                    for char in service.characteristics:
                        char_info = {
                            "uuid": str(char.uuid),
                            "handle": char.handle,
                            "properties": list(char.properties),
                            "descriptors": []
                        }
                        
                        # Add descriptor information
                        for descriptor in char.descriptors:
                            desc_info = {
                                "uuid": str(descriptor.uuid),
                                "handle": descriptor.handle
                            }
                            char_info["descriptors"].append(desc_info)
                        
                        service_info["characteristics"][char.handle] = char_info
                    
                    services_info[service.handle] = service_info
                
                self.discovered_services[device_address] = services_info
                return services_info
                
        except Exception as e:
            _LOGGER.error("Error discovering services for %s: %s", device_address, e)
            return {}

    async def test_gatt_communication(
        self,
        device_address: str,
        write_handle: int,
        read_handle: int,
        command_hex: str,
        expected_responses: int = 2,
        timeout: int = 10
    ) -> List[str]:
        """Test GATT communication with specific handles."""
        responses = []
        response_count = 0
        
        def notification_handler(sender, data):
            nonlocal response_count, responses
            response_count += 1
            hex_data = data.hex().upper()
            _LOGGER.debug("Response %d: %s", response_count, hex_data)
            responses.append(hex_data)

        try:
            async with BleakClient(device_address) as client:
                _LOGGER.info("Testing communication with %s", device_address)
                
                # Find characteristics by handle
                write_char = None
                read_char = None
                
                services = client.services
                for service in services.services.values():
                    for char in service.characteristics:
                        if char.handle == write_handle:
                            write_char = char
                        if char.handle == read_handle:
                            read_char = char
                
                if not write_char or not read_char:
                    _LOGGER.error(
                        "Required handles not found. Write: 0x%04X (%s), Read: 0x%04X (%s)",
                        write_handle, write_char is not None,
                        read_handle, read_char is not None
                    )
                    return []
                
                # Start notifications
                await client.start_notify(read_char, notification_handler)
                
                # Send command
                command_bytes = bytes.fromhex(command_hex)
                await client.write_gatt_char(write_char, command_bytes)
                _LOGGER.debug("Sent command to 0x%04X: %s", write_handle, command_hex)
                
                # Wait for responses
                elapsed = 0
                while response_count < expected_responses and elapsed < timeout:
                    await asyncio.sleep(0.1)
                    elapsed += 0.1
                
                # Stop notifications
                await client.stop_notify(read_char)
                
                _LOGGER.info(
                    "Communication test completed. Received %d/%d responses",
                    len(responses), expected_responses
                )
                
                return responses
                
        except Exception as e:
            _LOGGER.error("Error testing communication: %s", e)
            return []

    def print_service_summary(self, device_address: str) -> None:
        """Print a formatted summary of discovered services."""
        if device_address not in self.discovered_services:
            _LOGGER.warning("No services discovered for %s", device_address)
            return
        
        services = self.discovered_services[device_address]
        
        print(f"\n🔍 GATT SERVICES SUMMARY FOR {device_address}")
        print("=" * 60)
        
        for service_handle, service_info in services.items():
            print(f"\n🔧 Service: {service_info['uuid']}")
            print(f"   Handle: 0x{service_handle:04X}")
            
            for char_handle, char_info in service_info["characteristics"].items():
                properties = ", ".join(char_info["properties"])
                print(f"   📡 Characteristic: {char_info['uuid']}")
                print(f"      Handle: 0x{char_handle:04X}")
                print(f"      Properties: {properties}")
                
                for desc_info in char_info["descriptors"]:
                    print(f"      📝 Descriptor: {desc_info['uuid']}")
                    print(f"         Handle: 0x{desc_info['handle']:04X}")
        
        print("=" * 60)

    def get_write_read_handles(self, device_address: str) -> List[Tuple[int, int]]:
        """Get potential write/read handle pairs from discovered services."""
        if device_address not in self.discovered_services:
            return []
        
        services = self.discovered_services[device_address]
        handle_pairs = []
        
        write_handles = []
        read_handles = []
        
        for service_info in services.values():
            for char_info in service_info["characteristics"].values():
                properties = char_info["properties"]
                handle = char_info["handle"]
                
                if "write" in properties or "write-without-response" in properties:
                    write_handles.append(handle)
                
                if "notify" in properties or "indicate" in properties or "read" in properties:
                    read_handles.append(handle)
        
        # Create pairs (each write handle with each read handle)
        for write_handle in write_handles:
            for read_handle in read_handles:
                if write_handle != read_handle:
                    handle_pairs.append((write_handle, read_handle))
        
        return handle_pairs


async def discover_alta80_device(device_name: str = "gzf1-80-F14D2A") -> Dict:
    """Discover and test Alta 80 device communication."""
    discovery = GoalZeroGATTDiscovery()
    
    # Find device
    device_address = await discovery.find_device_by_name(device_name)
    if not device_address:
        return {"error": f"Device {device_name} not found"}
    
    # Discover services
    services = await discovery.discover_device_services(device_address)
    if not services:
        return {"error": "Failed to discover services"}
    
    # Print summary
    discovery.print_service_summary(device_address)
    
    # Test known handles (from goalzero_gatt.py)
    write_handle = 0x000A
    read_handle = 0x000C
    command = "FEFE03010200"
    
    responses = await discovery.test_gatt_communication(
        device_address, write_handle, read_handle, command
    )
    
    return {
        "device_address": device_address,
        "services": services,
        "test_responses": responses,
        "handle_pairs": discovery.get_write_read_handles(device_address)
    }


if __name__ == "__main__":
    # Example usage
    result = asyncio.run(discover_alta80_device())
    print(f"\nDiscovery Result: {result}")
