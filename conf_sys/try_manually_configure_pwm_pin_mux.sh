#!/bin/bash
echo "=== Manually Configuring PWM Pin Mux ==="

# Try to configure P9_14 for PWM (EHRPWM1A)
# The pin mux register for P9_14 is at offset 0x048
# Mode 6 should be PWM

# Check if we can access pin control
if [ -d /sys/kernel/debug/pinctrl ]; then
    echo "Pin control debug available"
    sudo cat /sys/kernel/debug/pinctrl/*/pingroups 2>/dev/null | grep -i pwm || echo "No PWM pingroups found"
else
    echo "Pin control debug not available"
fi

# Try alternative pin configuration methods
if command -v config-pin >/dev/null 2>&1; then
    echo "Trying config-pin method..."
    
    # Force PWM mode on common pins
    for pin in P9_14 P9_16 P8_19 P8_13 P9_31 P9_29; do
        echo "Configuring $pin for PWM..."
        sudo config-pin $pin pwm 2>/dev/null && echo "$pin: OK" || echo "$pin: FAILED"
    done
    
    # Check results
    for pin in P9_14 P9_16 P8_19 P8_13 P9_31 P9_29; do
        echo "$pin status: $(config-pin -q $pin 2>/dev/null || echo 'UNKNOWN')"
    done
fi
