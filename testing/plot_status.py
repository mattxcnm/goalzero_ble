import matplotlib.pyplot as plt
import matplotlib.patches as patches

def signed_byte(val):
    """Convert unsigned byte to signed."""
    return val - 256 if val > 127 else val

def parse_log(file_path):
    zone1_temps = []
    zone2_temps = []
    compressor_flags = []

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                data = bytes.fromhex(line)
                
                # Extract Zone 1 temp
                idx1 = data.find(b'\xFE\xFE\x02\x00')
                if idx1 == -1 or idx1 + 5 >= len(data):
                    continue
                temp1 = signed_byte(data[idx1 + 4])

                # Find second instance (Zone 2)
                idx2 = data.find(b'\xFE\xFE\x02\x00', idx1 + 4)
                if idx2 == -1 or idx2 + 6 >= len(data):
                    continue
                temp2 = signed_byte(data[idx2 + 4])
                
                # Compressor flag byte (assumed to be the next byte after temp2)
                flag_byte = data[idx2 + 5]

                zone1_temps.append(temp1)
                zone2_temps.append(temp2)
                compressor_flags.append(flag_byte)

            except Exception as e:
                print(f"Skipping line due to error: {e}")
                continue

    return zone1_temps, zone2_temps, compressor_flags


def plot_temps(zone1, zone2, flags):
    x = list(range(len(zone1)))

    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(x, zone1, label="Zone 1 Temp (°C)", color="blue")
    ax.plot(x, zone2, label="Zone 2 Temp (°C)", color="green")

    # Highlight regions where compressor is ON
    in_region = False
    start_idx = 0

    for i, flag in enumerate(flags):
        if not in_region and flag != 0:
            in_region = True
            start_idx = i
        elif in_region and flag == 0:
            in_region = False
            ax.axvspan(start_idx, i, color='red', alpha=0.2, label='Compressor ON' if start_idx == 0 else None)

    # Catch trailing ON region
    if in_region:
        ax.axvspan(start_idx, len(zone1), color='red', alpha=0.2, label='Compressor ON' if start_idx == 0 else None)

    ax.set_title("Fridge Zone Temperatures with Compressor Activity")
    ax.set_xlabel("Sample Index")
    ax.set_ylabel("Temperature (°C)")
    ax.grid(True)
    ax.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    input_file = "8hour_values.txt"  # Replace with your input file
    zone1, zone2, flags = parse_log(input_file)
    plot_temps(zone1, zone2, flags)