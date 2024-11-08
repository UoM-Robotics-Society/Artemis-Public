import asyncio
import csv
import os
from bleak import BleakScanner
from pymyo import Myo
from pymyo.types import EmgMode, EmgValue, UnsupportedFeatureError
from constants import (
    CLASSES,
    MYO_ADDRESS
)

# Global variables
current_gesture = None
gesture_labels = [key for key, _ in CLASSES.items()]
columns = [f"Sensor{i}" for i in range(1, 17)] + ["Label"]  # Myo has 8 EMG sensors
collection_time = 5
data_collection = []  # Renamed from emg_data to avoid confusion with callback parameter

async def main() -> None:
    global data_collection
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Find Myo device
    myo_device = await BleakScanner.find_device_by_address(MYO_ADDRESS)
    if not myo_device:
        raise RuntimeError(f"Could not find Myo device with address {MYO_ADDRESS}")
    
    async with Myo(myo_device) as myo:
        # Print device info
        print("Device name:", await myo.name)
        print("Battery level:", await myo.battery)
        print("Firmware version:", await myo.firmware_version)
        print("Firmware info:", await myo.info)
        
        # Define EMG callback
        @myo.on_emg
        def on_emg(emg_data: EmgValue):
            sensor1_data, sensor2_data = emg_data
            data_collection.append((*sensor1_data, *sensor2_data, current_gesture))
        
        # Try to enable battery notifications
        try:
            await myo.enable_battery_notifications()
        except UnsupportedFeatureError as e:
            print(f"Battery notifications not supported: {e}")
        
        # Set EMG mode
        await asyncio.sleep(1)
        await myo.set_mode(emg_mode=EmgMode.EMG)
        
        print("Collecting EMG data. Please perform the gestures when prompted.")
        
        # Collect data for each gesture
        for idx, gesture_label in enumerate(gesture_labels):
            current_gesture = idx
            
            for repetition in range(2):  # 10 repetitions per gesture
                print(f"\nPerform '{CLASSES[gesture_label]}' gesture (repetition {repetition + 1}/10)")
                
                # Give time to prepare
                print("Preparing...")
                await asyncio.sleep(3)  # 3 seconds to react
                
                print("Recording...")
                await asyncio.sleep(collection_time)
                await asyncio.sleep(1)  # Brief pause between repetitions
        
        print("\nFinished collecting data.")
        
        print(data_collection)
        
         # Save to CSV
        filename = f"data/{gesture_label}_{repetition}.csv"
        with open(filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)
            
            for row in data_collection:
                writer.writerow([*row])
        
        print(f"Data saved to {filename}")

if __name__ == "__main__":
    asyncio.run(main())