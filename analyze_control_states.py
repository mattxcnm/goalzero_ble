#!/usr/bin/env python3
"""
Alta 80 Control State Analysis Script

This script helps identify which bytes in the 36-byte status response 
correspond to control states (power, eco mode, battery protection).

Usage:
1. Run script and capture baseline status
2. Change one control setting on the device 
3. Capture status again and compare differences
4. Repeat for each control to map bytes to states

Run with: python analyze_control_states.py
"""

import asyncio
import logging
from bleak import BleakClient, BleakScanner
import time
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

# Device configuration
DEVICE_NAME = "gzf1-80-"  # Partial name match for Alta 80
STATUS_COMMAND = bytes.fromhex("FEFE03010200")

class ControlStateAnalyzer:
    """Analyzes Alta 80 status responses to identify control state bytes."""
    
    def __init__(self):
        self.device = None
        self.write_char = None
        self.read_char = None
        self.responses = []
        self.captured_states = []
        
    async def find_device(self) -> bool:
        """Find the Alta 80 device."""
        _LOGGER.info("Scanning for Alta 80 device...")
        
        devices = await BleakScanner.discover(timeout=10.0)
        for device in devices:
            if device.name and DEVICE_NAME in device.name:
                self.device = device
                _LOGGER.info(f"✓ Found device: {device.name} ({device.address})")
                return True
                
        _LOGGER.error("❌ No Alta 80 device found")
        return False
        
    async def discover_characteristics(self, client: BleakClient) -> bool:
        """Discover GATT characteristics for reading/writing."""
        _LOGGER.info("Discovering GATT services and characteristics...")
        
        services = client.services
        for service in services:
            _LOGGER.debug(f"Service: {service.uuid}")
            
            for char in service.characteristics:
                _LOGGER.debug(f"  Characteristic: {char.uuid} - {char.properties}")
                
                # Find write characteristic (write-without-response)
                if "write-without-response" in char.properties and not self.write_char:
                    self.write_char = char
                    _LOGGER.info(f"✓ Write characteristic: {char.uuid}")
                    
                # Find read characteristic (notify or indicate)
                if ("notify" in char.properties or "indicate" in char.properties) and not self.read_char:
                    self.read_char = char
                    _LOGGER.info(f"✓ Read characteristic: {char.uuid}")
                    
        return self.write_char is not None and self.read_char is not None
        
    def notification_handler(self, sender, data: bytearray):
        """Handle BLE notifications with response data."""
        hex_data = data.hex().upper()
        self.responses.append(hex_data)
        _LOGGER.debug(f"Received: {hex_data}")
        
    async def capture_status(self, client: BleakClient, label: str) -> List[int]:
        """Capture device status and return as byte array."""
        _LOGGER.info(f"📡 Capturing status: {label}")
        
        # Clear previous responses
        self.responses = []
        
        # Start notifications
        await client.start_notify(self.read_char, self.notification_handler)
        
        # Send status request
        await client.write_gatt_char(self.write_char, STATUS_COMMAND, response=False)
        
        # Wait for responses (Alta 80 sends 2x 18-byte responses)
        await asyncio.sleep(2.0)
        
        # Stop notifications
        await client.stop_notify(self.read_char)
        
        if len(self.responses) >= 2:
            # Concatenate responses
            combined_hex = "".join(self.responses)
            byte_array = [int(combined_hex[i:i+2], 16) for i in range(0, len(combined_hex), 2)]
            
            # Store capture with metadata
            capture = {
                "label": label,
                "timestamp": time.time(),
                "bytes": byte_array,
                "hex": combined_hex
            }
            self.captured_states.append(capture)
            
            _LOGGER.info(f"✓ Captured {len(byte_array)} bytes: {combined_hex}")
            return byte_array
        else:
            _LOGGER.error(f"❌ Incomplete response for {label}")
            return []
            
    def compare_captures(self, capture1: Dict, capture2: Dict) -> Dict[int, Dict]:
        """Compare two captures and return differences."""
        differences = {}
        
        bytes1 = capture1["bytes"]
        bytes2 = capture2["bytes"]
        
        min_len = min(len(bytes1), len(bytes2))
        
        for i in range(min_len):
            if bytes1[i] != bytes2[i]:
                differences[i] = {
                    "byte_pos": i,
                    "before": bytes1[i],
                    "after": bytes2[i],
                    "hex_before": f"0x{bytes1[i]:02X}",
                    "hex_after": f"0x{bytes2[i]:02X}",
                    "binary_before": f"{bytes1[i]:08b}",
                    "binary_after": f"{bytes2[i]:08b}"
                }
                
        return differences
        
    def print_analysis(self):
        """Print analysis of all captured states."""
        _LOGGER.info("\n" + "="*60)
        _LOGGER.info("CONTROL STATE ANALYSIS RESULTS")
        _LOGGER.info("="*60)
        
        if len(self.captured_states) < 2:
            _LOGGER.warning("Need at least 2 captures to analyze differences")
            return
            
        # Compare consecutive captures
        for i in range(1, len(self.captured_states)):
            prev_capture = self.captured_states[i-1]
            curr_capture = self.captured_states[i]
            
            _LOGGER.info(f"\n📊 COMPARISON: {prev_capture['label']} → {curr_capture['label']}")
            _LOGGER.info("-" * 40)
            
            differences = self.compare_captures(prev_capture, curr_capture)
            
            if not differences:
                _LOGGER.info("  ✓ No differences found")
            else:
                for byte_pos, diff in differences.items():
                    _LOGGER.info(f"  Byte {byte_pos:2d}: {diff['hex_before']} → {diff['hex_after']} "
                               f"({diff['before']:3d} → {diff['after']:3d}) "
                               f"[{diff['binary_before']} → {diff['binary_after']}]")
                    
        # Summary of most frequently changing bytes
        _LOGGER.info(f"\n📈 SUMMARY")
        _LOGGER.info("-" * 20)
        
        change_count = {}
        for i in range(1, len(self.captured_states)):
            prev_capture = self.captured_states[i-1]
            curr_capture = self.captured_states[i]
            differences = self.compare_captures(prev_capture, curr_capture)
            
            for byte_pos in differences.keys():
                change_count[byte_pos] = change_count.get(byte_pos, 0) + 1
                
        if change_count:
            _LOGGER.info("Most frequently changing bytes (likely control states):")
            sorted_changes = sorted(change_count.items(), key=lambda x: x[1], reverse=True)
            for byte_pos, count in sorted_changes:
                _LOGGER.info(f"  Byte {byte_pos:2d}: changed {count} times")
        else:
            _LOGGER.info("No byte changes detected across captures")
            
    async def run_analysis(self):
        """Run the interactive control state analysis."""
        if not await self.find_device():
            return
            
        try:
            async with BleakClient(self.device, timeout=15.0) as client:
                _LOGGER.info(f"✓ Connected to {self.device.name}")
                
                if not await self.discover_characteristics(client):
                    _LOGGER.error("❌ Could not find required characteristics")
                    return
                    
                # Interactive capture loop
                _LOGGER.info("\n" + "="*60)
                _LOGGER.info("INTERACTIVE CONTROL STATE ANALYSIS")
                _LOGGER.info("="*60)
                _LOGGER.info("Instructions:")
                _LOGGER.info("1. First capture will establish baseline")
                _LOGGER.info("2. Change ONE control setting on device")
                _LOGGER.info("3. Capture again to see what bytes changed")
                _LOGGER.info("4. Repeat for each control (power, eco mode, battery protection)")
                _LOGGER.info("5. Type 'quit' when done")
                
                while True:
                    try:
                        label = input(f"\n📝 Enter label for capture #{len(self.captured_states)+1} (or 'quit'): ").strip()
                        
                        if label.lower() in ['quit', 'exit', 'q']:
                            break
                            
                        if not label:
                            label = f"Capture_{len(self.captured_states)+1}"
                            
                        await self.capture_status(client, label)
                        
                        # Show immediate comparison if we have previous capture
                        if len(self.captured_states) >= 2:
                            prev_capture = self.captured_states[-2]
                            curr_capture = self.captured_states[-1]
                            differences = self.compare_captures(prev_capture, curr_capture)
                            
                            if differences:
                                _LOGGER.info(f"🔍 Changes from {prev_capture['label']}:")
                                for byte_pos, diff in differences.items():
                                    _LOGGER.info(f"    Byte {byte_pos:2d}: {diff['hex_before']} → {diff['hex_after']}")
                            else:
                                _LOGGER.info("   No changes detected")
                                
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        _LOGGER.error(f"Error during capture: {e}")
                        
                # Final analysis
                self.print_analysis()
                
        except Exception as e:
            _LOGGER.error(f"Connection error: {e}")

if __name__ == "__main__":
    analyzer = ControlStateAnalyzer()
    asyncio.run(analyzer.run_analysis())
