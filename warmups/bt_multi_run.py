from bt_multi_lib import BT

def my_data_processor(message):
    """Process the received data - add your custom logic here"""
    print(f"Processing: {message}")
    
    # Add your custom logic here:
    if message == "LED_ON":
        # Turn on LED
        print("RUN LED ON command received")
    elif message == "LED_OFF":
        # Turn off LED
        print("RUN LED OFF command received")
    elif message.startswith("MOVE_"):
        # Control motors
        print(f"Motor control command received: {message}")
    # etc.

print("Starting Bluetooth Server...")
print("Send data from your iPhone to see it here!")
print("Press Ctrl+C to stop")
print("=" * 50)

# Create BT server with custom processor
bt = BT()
bt.custom_processor = my_data_processor  # Set custom processor
bt.start_server()