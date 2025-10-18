from software_pwm  import SoftwarePWM
# Multiple PWM channels using different GPIO pins
pwm1 = SoftwarePWM("/dev/gpiochip0", 18, 1000)  # P9_14
pwm2 = SoftwarePWM("/dev/gpiochip0", 19, 1000)  # P9_16  
pwm3 = SoftwarePWM("/dev/gpiochip0", 17, 1000)  # P9_23

# Control multiple devices simultaneously
pwm1.start()  # LED brightness
pwm2.start()  # Motor speed
pwm3.start()  # Servo position
