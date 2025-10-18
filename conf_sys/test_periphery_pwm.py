from periphery import PWM
import time

# P9_14 EHRPWM1A - commonly pwmchip1, channel 0
# If this doesn't work, try different chip numbers (0, 2, 3, etc.)

def test_pwm_pin(chip, channel):
    try:
        print(f"Testing PWM chip {chip}, channel {channel}")
        pwm = PWM(chip, channel)
        
        # Configure PWM
        pwm.frequency = 1000  # 1kHz
        pwm.duty_cycle = 0.5  # 50%
        pwm.enable()
        
        print("PWM enabled successfully!")
        
        # Test different duty cycles
        duties = [0.1, 0.3, 0.5, 0.7, 0.9]
        for duty in duties:
            print(f"Setting duty cycle to {duty*100}%")
            pwm.duty_cycle = duty
            time.sleep(1)
        
        return pwm
        
    except Exception as e:
        print(f"Failed with chip {chip}, channel {channel}: {e}")
        return None

# Try common configurations for P9_14
configs_to_try = [
    (1, 0),  # Most common for EHRPWM1A
    (0, 0),  # Alternative
    (2, 0),  # Alternative
    (3, 0),  # Alternative
]

pwm = None
for chip, channel in configs_to_try:
    pwm = test_pwm_pin(chip, channel)
    if pwm:
        print(f"SUCCESS: P9_14 working on PWM chip {chip}, channel {channel}")
        break

if pwm:
    try:
        input("Press Enter to stop PWM...")
    finally:
        pwm.disable()
        pwm.close()
        print("PWM stopped")
else:
    print("Could not find working PWM configuration for P9_14")
