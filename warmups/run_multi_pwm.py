from multi_pwm_controller import MultiPWMController

# Create controller
controller = MultiPWMController()

# Add your pins
controller.add_pwm("P9_14", "/dev/gpiochip0", 18, 1000)
controller.add_pwm("P9_16", "/dev/gpiochip0", 19, 1000)  
controller.add_pwm("P9_23", "/dev/gpiochip0", 17, 1000)

# Start all PWM
controller.start_all()

# Test each pin
controller.set_duty_cycle("P9_14", 30)
controller.set_duty_cycle("P9_16", 60) 
controller.set_duty_cycle("P9_23", 90)

input("Check LEDs, then press Enter...")

controller.close_all()
