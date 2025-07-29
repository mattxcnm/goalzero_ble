#!/usr/bin/env python3
"""
Analyze messages on Handle 0x0008 from Yeti 500 Wireshark capture.
"""

import csv

def analyze_handle_0x0008(csv_file):
    """
    Extract and analyze all messages sent on handle 0x0008.
    """
    print("📊 Analyzing Handle 0x0008 Messages")
    print("=" * 50)
    
    messages = []
    
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            for row in reader:
                if row['handle'] == '0x0008':
                    messages.append(row['value'])
    
        print(f"Found {len(messages)} messages on handle 0x0008\n")
        
        # Analyze patterns
        unique_values = {}
        
        for i, msg in enumerate(messages):
            print(f"Message {i+1:2}: {msg}")
            
            if msg in unique_values:
                unique_values[msg] += 1
            else:
                unique_values[msg] = 1
        
        print(f"\n📈 Value Analysis:")
        print("=" * 30)
        
        for value, count in sorted(unique_values.items()):
            print(f"{value:15} -> {count:2} times")
            
            # Convert hex to decimal for analysis
            try:
                # Split by colons and convert last byte
                parts = value.split(':')
                if len(parts) == 4:
                    # 4-byte value: 00:00:00:XX
                    last_byte_hex = parts[3]
                    
                    # Handle ASCII converted values (single characters)
                    if len(last_byte_hex) == 1:
                        last_byte_dec = ord(last_byte_hex)
                        print(f"                 Last byte: '{last_byte_hex}' = {last_byte_dec} (0x{last_byte_dec:02X})")
                    elif len(last_byte_hex) == 2:
                        last_byte_dec = int(last_byte_hex, 16)
                        print(f"                 Last byte: {last_byte_dec} (0x{last_byte_hex})")
                    
            except (ValueError, IndexError):
                print(f"                 (Could not decode)")
        
        print(f"\n🔍 Pattern Analysis:")
        print("=" * 30)
        
        # Look for patterns in the last byte
        last_bytes = []
        for value in messages:
            try:
                parts = value.split(':')
                if len(parts) == 4:
                    last_part = parts[3]
                    if len(last_part) == 1:
                        # ASCII character
                        last_bytes.append(ord(last_part))
                    elif len(last_part) == 2:
                        # Hex byte
                        last_bytes.append(int(last_part, 16))
            except (ValueError, IndexError):
                pass
        
        if last_bytes:
            print(f"Last byte values: {last_bytes}")
            print(f"Range: {min(last_bytes)} to {max(last_bytes)}")
            print(f"Average: {sum(last_bytes)/len(last_bytes):.1f}")
            
            # Check if it's a counter or length field
            differences = []
            for i in range(1, len(last_bytes)):
                diff = last_bytes[i] - last_bytes[i-1]
                differences.append(diff)
            
            if differences:
                print(f"Differences: {differences}")
                
                # Check for patterns
                if all(d == 0 for d in differences):
                    print("🔄 Pattern: Constant value")
                elif all(d >= 0 for d in differences):
                    print("📈 Pattern: Monotonically increasing")
                elif len(set(differences)) <= 3:
                    print(f"🔢 Pattern: Limited differences ({set(differences)})")
                else:
                    print("🌐 Pattern: Variable/Complex")
        
        print(f"\n💡 Hypothesis:")
        print("=" * 30)
        
        # Make educated guesses about the meaning
        if len(unique_values) == 1:
            print("🔄 Likely a constant value (maybe protocol header or status)")
        elif all('00:00:00:' in v for v in unique_values.keys()):
            print("📏 Likely a length/size field (format: 00:00:00:LENGTH)")
            print("   - First 3 bytes are always 00:00:00")
            print("   - Last byte varies (possibly message length)")
        else:
            print("❓ Unknown pattern - needs further analysis")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function."""
    csv_file = "testing/Wireshark_filtered_decode.csv"
    analyze_handle_0x0008(csv_file)

if __name__ == "__main__":
    main()
