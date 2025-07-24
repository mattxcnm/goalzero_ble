import matplotlib.pyplot as plt
import matplotlib.patches as patches

def signed_byte(val):
    return val - 256 if val > 127 else val

def parse_log(file_path):
    zone1_temp = []
    zone1_sign = []
    zone2_temp_hi_res = []
    comp_state_a = []
    comp_state_b = []
    all_values = []

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                data = bytes.fromhex(line)
                all_values.append(list(data))

                if len(data) < 36:
                    continue

                zone1 = signed_byte(data[18])
                sign34 = data[34]
                zone2 = data[35]
                compA = data[21]
                compB = data[31]

                zone1_temp.append(zone1)
                zone1_sign.append(sign34)
                zone2_temp_hi_res.append(zone2)
                comp_state_a.append(compA)
                comp_state_b.append(compB)

            except Exception as e:
                print(f"Skipping line due to error: {e}")
                continue

    return zone1_temp, zone2_temp_hi_res, comp_state_a, comp_state_b, all_values


def plot_temps(zone1, zone2, compA, compB):
    x = list(range(len(zone1)))

    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(x, zone1, label="Zone 1 Temp (Byte 18)", color="blue")
    ax.plot(x, zone2, label="Zone 2 Temp (Byte 35)", color="green")

    # Determine max states for compressor logic
    maxA = max(compA)
    maxB = max(compB)

    # Compressor ON if either state is below max
    in_region = False
    start_idx = 0
    for i, (a, b) in enumerate(zip(compA, compB)):
        is_off = (a == maxA and b == maxB)
        if not in_region and not is_off:
            in_region = True
            start_idx = i
        elif in_region and is_off:
            in_region = False
            ax.axvspan(start_idx, i, color='red', alpha=0.2, label='Compressor ON' if start_idx == 0 else None)
    if in_region:
        ax.axvspan(start_idx, len(zone1), color='red', alpha=0.2, label='Compressor ON' if start_idx == 0 else None)

    ax.set_title("Zone Temperatures with Compressor ON (Inferred from B21 & B31)")
    ax.set_xlabel("Sample Index")
    ax.set_ylabel("Temperature")
    ax.grid(True)
    ax.legend()
    plt.tight_layout()
    plt.show()


def plot_changing_bytes(raw_bytes):
    """
    Plot bytes that change over time to identify patterns
    """
    if not raw_bytes or len(raw_bytes) == 0:
        print("No data to analyze")
        return
        
    # Find the most common length to determine byte positions
    lengths = {}
    for data in raw_bytes:
        length = len(data)
        lengths[length] = lengths.get(length, 0) + 1
    
    max_length = max(lengths, key=lambda k: lengths[k])
    print(f"Most common byte length: {max_length}")
    
    # Initialize the byte position values
    byte_values = [[] for _ in range(max_length)]
    
    # Collect values for each byte position
    for data in raw_bytes:
        if len(data) >= max_length:
            for i in range(max_length):
                byte_values[i].append(data[i])
    
    # Plot bytes that have variation
    fig, ax = plt.subplots(figsize=(15, 8))
    
    for i, values in enumerate(byte_values):
        if len(set(values)) > 1:  # Only plot if there's variation
            ax.plot(values, label=f"Byte {i}")
    
    ax.set_title("Changing Byte Values Over Time")
    ax.set_xlabel("Sample Index")
    ax.set_ylabel("Byte Value")
    ax.grid(True)
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    input_file = "8hour_values.txt"  # Update this with your file path if needed

    zone1, zone2, compA, compB, raw_bytes = parse_log(input_file)
    plot_temps(zone1, zone2, compA, compB)
    plot_changing_bytes(raw_bytes)