# Check current pin mux settings for common PWM pins
for pin in P9_14 P9_16 P8_19 P8_13 P9_31 P9_29; do
    echo "=== $pin ==="
    find /sys -name "*${pin}*" 2>/dev/null | head -5
done
