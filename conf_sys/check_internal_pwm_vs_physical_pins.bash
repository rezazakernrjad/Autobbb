# Quick test - run PWM internally while checking physical pins
python3 -c "
from periphery import PWM
import time

print('Testing if PWM works internally but not on pins...')

# Start PWM on all working channels
pwms = []
for chip, channel in [(0,0), (1,0), (2,0), (3,0), (4,0)]:
    try:
        pwm = PWM(chip, channel)
        pwm.frequency = 1000
        pwm.duty_cycle = 0.5
        pwm.enable()
        pwms.append(pwm)
        print(f'✅ PWM {chip},{channel} enabled internally')
    except:
        pass

print()
print('PWM is running internally on all channels.')
print('Now check these pins with LED or multimeter:')
print('- P9_14, P9_16 (most likely)')
print('- P8_19, P8_13')  
print('- P9_31, P9_29')
print('- Any other PWM-capable pins')
print()
input('Press Enter when done checking pins...')

# Clean up
for pwm in pwms:
    pwm.disable()
    pwm.close()

print('PWM test complete.')
"
