# Check if PWM pins are configured in device tree
find /sys/firmware/devicetree/base -name "*pinmux*" -o -name "*pin*" | grep -i pwm

# Check pin control status
ls /sys/class/pinctrl/
cat /sys/kernel/debug/pinctrl/*/pinmux-pins 2>/dev/null | grep -i pwm || echo "No debug pinctrl info"
