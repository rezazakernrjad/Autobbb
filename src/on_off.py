from periphery import GPIO
import time
# P9_12 is gpiochip0, line 28
P9_12 = GPIO("/dev/gpiochip0", 28, "out")
try:
    while True:
        # Set the line value to 1 (High)
        P9_12.write(True)
        time.sleep(0.7)
        print("ACTIVE")
        # Set the line value to 0 (Low)
        P9_12.write(False)
        time.sleep(0.6)
        print("INACTIVE")
except KeyboardInterrupt:
    print("\nExiting.")
    # The 'with' block will automatically release the line.