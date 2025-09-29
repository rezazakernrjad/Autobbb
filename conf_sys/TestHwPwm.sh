# Test if hardware PWM now works
python3 -c "
from periphery import PWM
import time

print('Testing hardware PWM after fix...')
try:
    # Try PWM chip 0, channel 0
    pwm = PWM(0, 0)
    pwm.frequency = 1000
    pwm.duty_cycle = 0.5
    pwm.enable()
    
    print('✅ Hardware PWM working!')
    
    # Quick test
    for duty in [0.1, 0.5, 0.9]:
        pwm.duty_cycle = duty
        print(f'Duty: {duty*100}%')
        time.sleep(1)
    
    pwm.disable()
    pwm.close()
    print('🎉 Hardware PWM test successful!')
    
except Exception as e:
    print(f'❌ Hardware PWM failed: {e}')
    print('Software PWM is still the recommended solution.')
"
