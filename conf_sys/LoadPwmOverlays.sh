# Check if configfs is available
ls -d /sys/kernel/config/device-tree/overlays 2>/dev/null || echo "configfs overlays not available"

# If configfs exists, try loading overlays
if [ -d /sys/kernel/config/device-tree/overlays ]; then
    # Load PWM base overlay
    sudo mkdir -p /sys/kernel/config/device-tree/overlays/pwm_base
    sudo cp /lib/firmware/am33xx_pwm-00A0.dtbo /sys/kernel/config/device-tree/overlays/pwm_base/dtbo
    
    # Load PWM1 overlay
    sudo mkdir -p /sys/kernel/config/device-tree/overlays/pwm1
    sudo cp /lib/firmware/BB-PWM1-00A0.dtbo /sys/kernel/config/device-tree/overlays/pwm1/dtbo
    
    # Check results
    ls /sys/class/pwm/
fi
