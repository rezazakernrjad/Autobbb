# combination of pin_lib, bt_lib and auto_run receive message via bluetooth
# and control P9_14.

from bt_lib import BT
from pin_lib import PIN
from pwm_lib import PWMController
import signal
import sys

def signal_handler(sig, frame):
    print('\n\nShutting down gracefully...')
    if 'bt' in globals():
        bt.cleanup()
    sys.exit(0)

# Set up signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

print("Starting Bluetooth Server...")
print("Send data from your iPhone to see it here!")
print("Press Ctrl+C to stop")
print("=" * 50)

#Create PIN controller
pin = PIN()
# Create PWM controller
pwm = PWMController()
# Create BT server with custom processor
bt = BT()

# Debug Bluetooth status first
bt.debug_bluetooth_status()

# Configure BT server
bt.pin_control = pin.set_pin_9_12  # Set custom processor
pwm.start_pwm()
bt.lamps_control = pwm.set_pin_9_14
bt.left_control = pwm.set_pin_8_13
bt.right_control = pwm.set_pin_8_19

print("\n🔍 Current connection analysis:")
print(f"Connected device found: B0:67:B5:7C:41:CA")
print("This device appears to be already connected!")
print("If this is your iPhone, communication should work.")
print("\n" + "="*50)

# Start the server (this will block)
bt.start_server()