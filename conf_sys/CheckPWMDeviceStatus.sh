# Check for PWM chips
ls /sys/class/pwm/

# If PWM chips exist, show details
if [ -d /sys/class/pwm ]; then
    echo "PWM chips found:"
    for chip in /sys/class/pwm/pwmchip*; do
        if [ -d "$chip" ]; then
            echo "$(basename $chip): $(cat $chip/npwm 2>/dev/null || echo 'unknown') channels"
        fi
    done
fi