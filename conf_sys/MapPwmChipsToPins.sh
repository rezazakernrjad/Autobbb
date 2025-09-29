# Check how many channels each PWM chip has
for chip in /sys/class/pwm/pwmchip*; do
    if [ -d "$chip" ]; then
        chip_name=$(basename "$chip")
        channels=$(cat "$chip/npwm" 2>/dev/null || echo "unknown")
        echo "$chip_name: $channels channels"
    fi
done
