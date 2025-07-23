import asyncio
from bleak import BleakClient

# Replace with your fridge's BLE address and characteristic UUID
DEVICE_ADDRESS = "fd:06:22:f1:4d:2a"
CHAR_UUID = "B9AE4CD2-C1C8-CB33-9960-524E3DB49DB3"

async def send_command(client, hex_str):
    data = bytes.fromhex(hex_str)
    await client.write_gatt_char(CHAR_UUID, data)
    print(f"Sent: {hex_str}")

def parse_temp_segment(seg: bytes) -> float:
    # change divisor based on calibration; example: value / 100
    raw = int.from_bytes(seg, byteorder='little', signed=True)
    return raw / 100

def parse_response(data: bytes):
    # assumes “FEFE … 44 FC 04 …” contains two 4‑byte temps after byte 4
    fridge_raw = data[4:8]
    freezer_raw = data[8:12]
    print(">>> Fridge:", parse_temp_segment(fridge_raw), "°C",
          "| Freezer:", parse_temp_segment(freezer_raw), "°C")

async def main():
    async with BleakClient(DEVICE_ADDRESS) as client:
        await client.start_notify(CHAR_UUID, lambda _, d: parse_response(d))

        # Example command sequence
        cmds = {
            "left_down":    "FEFE040501020600",
            "left_up":      "FEFE040500020500",
            "right_down":   "FEFE040624022A00",
            "right_up":     "FEFE040623022900",
            # ...
        }
        for name, cmd in cmds.items():
            print("**", name)
            await send_command(client, cmd)
            await asyncio.sleep(1)

        # Let notifications flow for a bit
        await asyncio.sleep(5)
        await client.stop_notify(CHAR_UUID)

if __name__ == "__main__":
    asyncio.run(main())