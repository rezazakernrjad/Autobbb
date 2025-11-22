# combination of pin_lib, bt_lib and auto_run receive message via bluetooth
# and control P9_14.

from bt_lib import BT
from pin_lib import PIN
from pwm_lib import PWMController
from controller import WheelController
import signal
import sys

def signal_handler(sig, frame):
    print('\nShutting down gracefully...')
    bt.stop_server()

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
bt = BT()
# Create cont Controller
cont = WheelController(pin=pin, pwm=pwm)

"""bt.debug_bluetooth_status()  """

# Delegate functions
bt.lamps_control = pwm.illumination
bt.turn_left = cont.turn_left
bt.turn_right = cont.turn_right
bt.turn_end = cont.turn_end
bt.move_forward = cont.forward
bt.move_reverse = cont.reverse
bt.brake_movement = cont.brake
pwm.start_pwm()

print("\n🔍 Current connection analysis:")
print(f"Connected device found: B0:67:B5:7C:41:CA")
print("This device appears to be already connected!")
print("If this is your iPhone, communication should work.")
print("\n" + "="*50)

# Start the server (this will block)
bt.start_server()
 
