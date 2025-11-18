#!usr/bin/env python3
"""
Controller module for turning left or right also move forward and reverse
Uses pin_lib and pwm_lib to control GPIO pins and PWM signals.
pin8_11 - left wheel control
pwm8_13 - left pwm control
pin8_17 - right wheel control
pwm8_19 - right pwm control
pwm9_14 - illumination effects
turning left includs reversing right wheel and moving left wheel forward
    set PIN8_11(left_wheel) to HIGH: PIN::set_left_control("reverse")
    set PIN8_13 to 0% PWM: PWMController::set_left_duty(0)
    set PIN8_17(right_wheel) to LOW: PIN::set_right_control("forward")
    set PIN8_19 to 100% PWM: PWMController::set_right_duty(100)
turning right includs reversing left wheel and moving right wheel forward
forward moves both wheels forward
reverse moves both wheels in reverse.
"""
import time
""" from pin_lib import PIN
from pwm_lib import PWMController
pin = PIN()
pwm = PWMController() """
class WheelController:
    def __init__(self, pin, pwm):
        print("CONT: To Controll Wheels")
        self.speed = 0
        self.pin = pin
        self.pwm = pwm
        self.speed_left = 0
        self.speed_right = 0
        self.speed = 0

    def turn_left(self, angle):
        self.speed_left = self.speed_left - angle
        self.speed_right = self.speed_right + angle
        print (f"DEBUG: speed_left={self.speed_left}, speed_right={self.speed_right}")
        if self.speed_left < 0:
            self.speed_left = 0
        if self.speed_right > 100:
            self.speed_right = 100
        self.pwm.set_left_duty(self.speed_left)
        self.pwm.set_right_duty(self.speed_right)

    def turn_right(self, angle):
        self.speed_left = self.speed_left + angle
        self.speed_right = self.speed_right - angle
        print(f"DEBUG: speed_left={self.speed_left}, speed_right={self.speed_right}")
        if self.speed_left > 100:
            self.speed_left = 100
        if self.speed_right < 0:
            self.speed_right = 0
        self.pwm.set_left_duty(self.speed_left)
        self.pwm.set_right_duty(self.speed_right)

    def turn_end(self):
        self.pwm.set_all_wheels_duty(self.speed)
        self.speed_right = self.speed
        self.speed_left = self.speed
        print("CONT: turn ended, resuming forward movement")

    def forward(self, speed):
        self.pin.set_left_control("forward")
        self.pin.set_right_control("forward")
        self.speed = speed
        self.speed_right = speed
        self.speed_left = speed
        self.pwm.set_left_duty(self.speed_left)
        self.pwm.set_right_duty(self.speed_right)
        print(f"CONT: move forward at speed {speed}")

    def reverse(self):
        print("CONT: move reverse")
        self.pwm.set_all_wheels_duty(0)
        self.pin.set_left_control("reverse")
        self.pin.set_right_control("reverse")

    def brake(self):
        self.pwm.set_left_duty(0)
        self.pwm.set_right_duty(0)
        self.pin.set_left_control("forward")
        self.pin.set_right_control("forward")
