from periphery import PWM
import time

# Use the working configuration from above
pwm = PWM(1, 0)  # Adjust based on your test results

try:
    # Setup PWM for LED control
    pwm.frequency = 1000  # 1kHz - good for LEDs
    pwm.enable()
    
    print("LED Dimming Demo on P9_14")
    
    # Smooth dimming cycle
    for cycle in range(3):
        print(f"Dimming cycle {cycle + 1}")
        
        # Fade in
        for brightness in range(0, 101, 2):
            pwm.duty_cycle = brightness / 100.0
            time.sleep(0.05)
        
        time.sleep(0.5)  # Hold at full brightness
        
        # Fade out
        for brightness in range(100, -1, -2):
            pwm.duty_cycle = brightness / 100.0
            time.sleep(0.05)
            
        time.sleep(0.5)  # Hold at off
        
finally:
    pwm.disable()
    pwm.close()
    print("PWM disabled")
