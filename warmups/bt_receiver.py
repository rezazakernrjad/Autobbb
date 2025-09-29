import time
from bt_multi_lib import read_bt_data_from_file, mark_data_as_read

print("Bluetooth Data Receiver Started...")
print("Waiting for data from iPhone...")
print("Make sure bt_multi_run.py is running in another terminal!")
print("Press Ctrl+C to stop")
print("-" * 50)

last_timestamp = None

try:
    while True:
        # Read data from the shared file
        data = read_bt_data_from_file()
        
        if data is None:
            print("⚠️  No BT server running. Start bt_multi_run.py first!")
            time.sleep(2)
            continue
            
        # Check if there's new data
        if data.get("new_data", False) and data.get("timestamp") != last_timestamp:
            message = data.get("message", "")
            timestamp = data.get("timestamp", "")
            
            print(f"📱 NEW DATA RECEIVED!")
            print(f"   Message: {message}")
            print(f"   Time: {timestamp}")
            print("-" * 50)
            
            # Mark as read and remember timestamp
            mark_data_as_read()
            last_timestamp = timestamp
        
        # Small delay to avoid excessive CPU usage
        time.sleep(0.1)  # Check every 100ms
        
except KeyboardInterrupt:
    print("\n🛑 Stopped receiving Bluetooth data")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure bt_multi_run.py is running first!")
