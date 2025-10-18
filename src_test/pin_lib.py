# combination of pin_lib, bt_lib and auto_run receive message via bluetooth
# and control P9_12.
"""
from gpiochip0:
line  12: "P8_12" Left wheel control
line  13: "P8_11"
line  14: "P8_16"
line  15: "P8_15"
line  28: "P9_12"
gpiochip3:
line  27: "P8_17" Right wheel control
"""
from periphery import GPIO
import time
import threading

class PIN:
    def __init__(self):
        print("Run Pin Control")
        self.left_wheel = GPIO("/dev/gpiochip0", 28, "out")
        self.right_wheel= GPIO("/dev/gpiochip3", 17, "out")
        self.motor_stop_event = threading.Event()
        self.motor_thread = None

    def set_left_control(self, direction):
        if direction == "forward":
            self.right_wheel.write(False)
        elif direction == "reverse":
            self.right_wheel.write(True)

    def set_right_control(self, direction):
        if direction == "forward":
            self.right_wheel.write(False)
        elif direction == "reverse":
            self.right_wheel.write(True)
