import matplotlib.pyplot as plt
import matplotlib.patches as patches

def signed_byte(val):
    return val - 256 if val > 127 else val

def parse_log(file_path):
    zone1_temps = []
    zone2_temps = []
    compressor_flags = []
    all_values = []

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                data = bytes.fromhex(line)
                all_values.append(list(data))

                idx1 = data.find(b'\xFE\xFE\x02\x00')
                if idx1 == -1 or idx1 + 5 >= len(data):
                    continue
                temp1 = signed_byte(data[idx1 + 4])

                idx2 = data.find(b'\xFE\xFE\x02\x00', idx1 + 4)
                if idx2 == -1 or idx2 + 6 >= len(data):
                    continue
                temp2 = signed_byte(data[idx2 + 4])

                flag_byte = data[idx2 + 5]

                zone1_temps.append(temp1)
                zone2_temps.append(temp2)
                compressor_flags.append(flag_byte)

            except Exception as e:
                print(f"Skipping line due to error: {e}")
                continue

    return zone1_temps, zone2_temps, compressor_flags, all_values


def plot_temps(zone1, zone2, flags):
    x = list(range(len(zone1)))
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(x, zone1, label="Zone 1 Temp (°C)", color="blue")
    ax.plot(x, zone2, label="Zone 2 Temp (°C)", color="green")

    in_region = False
    start_idx = 0
    for i, flag in enumerate(flags):
        if not in_region and flag != 0:
            in_region = True
            start_idx = i
        elif in_region and flag == 0:
            in_region = False
            ax.axvspan(start_idx, i, color='red', alpha=0.2, label='Compressor ON' if start_idx == 0 else None)
    if in_region:
        ax.axvspan(start_idx, len(zone1), color='red', alpha=0.2, label='Compressor ON' if start_idx == 0 else None)

    ax.set_title("Fridge Zone Temperatures with Compressor Activity")
    ax.set_xlabel("Sample Index")
    ax.set_ylabel("Temperature (°C)")
    ax.grid(True)
    ax.legend()
    plt.tight_layout()
    plt.show()


def plot_changing_bytes(all_values):
    if not all_values:
        return

    # Find the maximum frame length and pad shorter frames
    max_len = max(len(v) for v in all_values)
    padded = [v + [None] * (max_len - len(v)) for v in all_values]
    transposed = list(zip(*padded))

    fig, ax = plt.subplots(figsize=(16, 10))

    for byte_index, byte_series in enumerate(transposed):
        # Skip columns that are fully missing (None)
        if all(b is None for b in byte_series):
            continue

        # Skip if all values are identical (constant)
        filtered = [b for b in byte_series if b is not None]
        if len(set(filtered)) <= 1:
            continue

        clean_values = [v if v is not None else 0 for v in byte_series]
        ax.plot(clean_values, label=f'Byte {byte_index}', alpha=0.7)

    ax.set_title("All Changing Byte Values Over Time")
    ax.set_xlabel("Sample Index")
    ax.set_ylabel("Byte Value (0–255)")
    ax.grid(True)
    ax.legend(loc='upper right', fontsize='small', ncol=2)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    input_file = "8hour_values.txt"  # Update this with your file path if needed

    zone1, zone2, flags, raw_bytes = parse_log(input_file)
    plot_temps(zone1, zone2, flags)
    plot_changing_bytes(raw_bytes)