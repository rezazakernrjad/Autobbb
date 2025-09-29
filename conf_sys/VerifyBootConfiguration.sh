# Check which boot file was used
if [ -f /boot/firmware/uEnv.txt ]; then
    echo "=== /boot/firmware/uEnv.txt ==="
    grep -E "(overlay|pwm|PWM)" /boot/firmware/uEnv.txt || echo "No PWM overlays found"
elif [ -f /boot/uEnv.txt ]; then
    echo "=== /boot/uEnv.txt ==="  
    grep -E "(overlay|pwm|PWM)" /boot/uEnv.txt || echo "No PWM overlays found"
fi