# combination of pin_lib, bt_lib and auto_run receive message via bluetooth
# and control P9_12.
"""
from gpiochip0:
line  12: "P8_12"
line  13: "P8_11" Left wheel control
line  14: "P8_16"
line  15: "P8_15"
line  28: "P9_12"
gpiochip3:
line  27: "P8_17" Right wheel control
line  26: "P8_14"
"""
from periphery import GPIO
import time

class PIN:
    def __init__(self):
        print("Run Pin Control")
        try:
            self.left_wheel = GPIO("/dev/gpiochip0", 13, "out")
            print("Left wheel GPIO initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing left wheel GPIO: {e}") 
        try:
            self.right_wheel = GPIO("/dev/gpiochip3", 27, "out")
            print("Right wheel GPIO initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing right wheel GPIO: {e}")

    def set_left_control(self, direction):
        try:
            print(f"PIN: Set left wheel to {direction}")
            if direction == "left" or direction == "reverse":
                self.left_wheel.write(True)
            elif direction == "right" or direction == "forward":
                self.left_wheel.write(False)
        except Exception as e:
            print("❌ Error in set_left_control:", e)
    def set_right_control(self, direction):
        try:
            print(f"PIN: Set right wheel to {direction}")
            if direction == "left" or direction == "forward":
                self.right_wheel.write(False)
            elif direction == "right" or direction == "reverse":
                self.right_wheel.write(True)
        except Exception as e:
            print("❌ Error in set_right_control:", e)
