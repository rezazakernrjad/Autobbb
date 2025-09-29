# combination of pin_lib, bt_lib and auto_run receive message via bluetooth
# and control P9_14.

from bt_lib import BT
from pin_lib import PIN
from pwm_lib import PWMController

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
bt.pin_control = pin.set_pin_9_12  # Set custom processor
pwm.start_pwm()
bt.pwma_control = pwm.set_pin_9_14
bt.pwmb_control = pwm.set_pin_8_13
bt.start_server()