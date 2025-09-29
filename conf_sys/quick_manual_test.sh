# Test the most likely PWM pins manually
python3 -c "
from periphery import PWM
import time
import math

# Test configurations and their likely pins
tests = [
    (2, 0, 'P9_14 (EHRPWM1A)'),
    (2, 1, 'P9_16 (EHRPWM1B)'),  
    (3, 0, 'P8_19 (EHRPWM2A)'),
    (4, 0, 'P8_13 (EHRPWM2B)'),
    (0, 0, 'P9_31 (EHRPWM0A)'),
    (1, 0, 'P9_29 (EHRPWM0B)'),
]

for chip, channel, pin_name in tests:
    print(f'\n🔍 Testing {pin_name}')
    print('Connect LED between pin and GND')
    
    try:
        pwm = PWM(chip, channel)
        pwm.frequency = 1000
        pwm.enable()
        
        # Obvious breathing pattern
        for i in range(40):
            brightness = (math.sin(i * 0.15) + 1) / 2
            pwm.duty_cycle = brightness
            time.sleep(0.1)
        
        pwm.disable()
        pwm.close()
        
        input(f'Did you see PWM on {pin_name}? Press Enter to continue...')
        
    except Exception as e:
        print(f'Error: {e}')
"
