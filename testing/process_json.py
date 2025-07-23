import json
import csv

def extract_btatt_pairs(obj):
    """Recursively extracts btatt.handle and btatt.value pairs from JSON."""
    results = []
    
    if isinstance(obj, dict):
        handle = obj.get("btatt.handle")
        value = obj.get("btatt.value")

        if handle is not None and value is not None:
            results.append((handle, value))

        for v in obj.values():
            results.extend(extract_btatt_pairs(v))

    elif isinstance(obj, list):
        for item in obj:
            results.extend(extract_btatt_pairs(item))
    
    return results

def main():
    input_file = "Alta80_3x.json"   # Replace with your actual file path
    output_file = "Alta80_3x.csv"

    # Load JSON data
    with open(input_file, 'r') as f:
        data = json.load(f)

    # Extract pairs
    pairs = extract_btatt_pairs(data)

    # Write to CSV
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["handle", "value"])  # Header
        writer.writerows(pairs)

    print(f"Extracted {len(pairs)} handle-value pairs to {output_file}")

if __name__ == "__main__":
    main()