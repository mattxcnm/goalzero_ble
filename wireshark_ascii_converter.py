#!/usr/bin/env python3
"""
Convert ASCII bytes in Wireshark CSV export to ASCII characters.
Leaves non-ASCII bytes as original hex values.
"""

import csv
import sys
import os

def hex_to_ascii_if_printable(hex_byte_str):
    """
    Convert a hex byte string to ASCII character if it's printable ASCII.
    Otherwise, return the original hex string.
    
    Args:
        hex_byte_str: String like "41" representing a hex byte
        
    Returns:
        ASCII character if printable, otherwise original hex string
    """
    try:
        # Convert hex string to integer
        byte_value = int(hex_byte_str, 16)
        
        # Check if it's printable ASCII (32-126, excluding control characters)
        if 32 <= byte_value <= 126:
            return chr(byte_value)
        else:
            # Return original hex for non-printable bytes
            return hex_byte_str
            
    except ValueError:
        # If conversion fails, return original
        return hex_byte_str

def process_value_field(value_str):
    """
    Process a colon-separated hex value string, converting ASCII bytes to characters.
    
    Args:
        value_str: String like "41:42:43:00:FF" (hex bytes separated by colons)
        
    Returns:
        String with ASCII bytes converted to characters, others left as hex
    """
    if not value_str or ':' not in value_str:
        return value_str
        
    # Split by colons to get individual hex bytes
    hex_bytes = value_str.split(':')
    
    # Convert each byte
    converted_parts = []
    for hex_byte in hex_bytes:
        hex_byte = hex_byte.strip()
        if len(hex_byte) == 2:  # Valid 2-character hex byte
            converted = hex_to_ascii_if_printable(hex_byte)
            converted_parts.append(converted)
        else:
            # Keep malformed hex as-is
            converted_parts.append(hex_byte)
    
    return ':'.join(converted_parts)

def process_csv_file(input_file, output_file=None):
    """
    Process the Wireshark CSV file and convert ASCII bytes to characters.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (optional, defaults to input_converted.csv)
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return False
        
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_ascii_converted.csv"
    
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as infile:
            with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
                
                # Create CSV reader and writer
                reader = csv.DictReader(infile)
                
                # Check if required columns exist
                fieldnames = reader.fieldnames
                if not fieldnames or 'handle' not in fieldnames or 'value' not in fieldnames:
                    print("Error: CSV must have 'handle' and 'value' columns")
                    return False
                
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                
                rows_processed = 0
                rows_converted = 0
                
                for row in reader:
                    original_value = row['value']
                    converted_value = process_value_field(original_value)
                    
                    # Check if any conversion happened
                    if converted_value != original_value:
                        rows_converted += 1
                    
                    # Update the row with converted value
                    row['value'] = converted_value
                    writer.writerow(row)
                    
                    rows_processed += 1
                    
                    # Show progress for large files
                    if rows_processed % 100 == 0:
                        print(f"Processed {rows_processed} rows...")
                
                print(f"\n✅ Conversion complete!")
                print(f"📄 Input file: {input_file}")
                print(f"📄 Output file: {output_file}")
                print(f"📊 Total rows processed: {rows_processed}")
                print(f"🔄 Rows with conversions: {rows_converted}")
                
                return True
                
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

def show_preview(input_file, num_rows=5):
    """
    Show a preview of the conversion for the first few rows.
    
    Args:
        input_file: Path to input CSV file
        num_rows: Number of rows to preview
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return
        
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            print(f"\n🔍 Preview of ASCII conversion (first {num_rows} rows):")
            print("=" * 80)
            
            for i, row in enumerate(reader):
                if i >= num_rows:
                    break
                    
                original = row['value']
                converted = process_value_field(original)
                
                print(f"\nRow {i+1} - Handle: {row['handle']}")
                print(f"Original:  {original}")
                print(f"Converted: {converted}")
                
                # Show what changed
                if converted != original:
                    print("🔄 Changes detected!")
                else:
                    print("📋 No ASCII bytes to convert")
                    
    except Exception as e:
        print(f"Error showing preview: {e}")

def main():
    """Main function to handle command line usage."""
    if len(sys.argv) < 2:
        print("Usage: python wireshark_ascii_converter.py <input_csv_file> [output_csv_file]")
        print("\nExample:")
        print("  python wireshark_ascii_converter.py Wireshark_filtered_export.csv")
        print("  python wireshark_ascii_converter.py input.csv output_converted.csv")
        print("\nOptions:")
        print("  --preview : Show preview of conversion without creating output file")
        return
    
    input_file = sys.argv[1]
    
    # Check for preview mode
    if '--preview' in sys.argv:
        show_preview(input_file)
        return
    
    # Determine output file
    output_file = None
    if len(sys.argv) >= 3 and not sys.argv[2].startswith('--'):
        output_file = sys.argv[2]
    
    # Show preview first
    print("🔍 Showing preview of conversion...")
    show_preview(input_file, 3)
    
    # Ask for confirmation
    response = input("\n❓ Proceed with full conversion? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Conversion cancelled.")
        return
    
    # Process the file
    success = process_csv_file(input_file, output_file)
    
    if success:
        print(f"\n🎉 Success! ASCII conversion completed.")
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}_ascii_converted.csv"
        print(f"💾 Converted file saved as: {output_file}")
    else:
        print("❌ Conversion failed.")

if __name__ == "__main__":
    main()
