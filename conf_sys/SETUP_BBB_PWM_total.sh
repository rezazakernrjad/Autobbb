#!/bin/bash
# BeagleBone Black Hardware PWM Auto-Setup Script
# This script configures a fresh BBB for hardware PWM functionality
# Run as: sudo bash setup_bbb_pwm.sh

echo "🔧 BeagleBone Black Hardware PWM Setup"
echo "======================================"
echo "This script will configure your BBB for hardware PWM functionality"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root"
    echo "Please run: sudo bash setup_bbb_pwm.sh"
    exit 1
fi

# Check if this is a BeagleBone
if ! grep -q "BeagleBone" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a BeagleBone"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "�� System Information:"
echo "  Model: $(cat /proc/device-tree/model 2>/dev/null || echo 'Unknown')"
echo "  Kernel: $(uname -r)"
echo "  OS: $(lsb_release -d 2>/dev/null | cut -f2 || echo 'Unknown')"
echo

# Backup existing uEnv.txt
echo "💾 Creating backup of uEnv.txt..."
BACKUP_FILE="/boot/uEnv.txt.backup_$(date +%Y%m%d_%H%M%S)"
cp /boot/uEnv.txt "$BACKUP_FILE"
echo "   Backup saved as: $BACKUP_FILE"

# Check available PWM overlays
echo
echo "�� Checking available PWM overlays..."
OVERLAY_PATHS=(
    "/boot/dtbs/$(uname -r)/overlays"
    "/lib/firmware"
)

PWM_OVERLAYS=()
for path in "${OVERLAY_PATHS[@]}"; do
    if [ -d "$path" ]; then
        mapfile -t found < <(find "$path" -name "*PWM*" -o -name "*pwm*" | grep -E "\\.dtbo?$")
        PWM_OVERLAYS+=("${found[@]}")
    fi
done

if [ ${#PWM_OVERLAYS[@]} -eq 0 ]; then
    echo "❌ No PWM overlays found!"
    echo "   Check your kernel version and overlay installation"
    exit 1
fi

echo "   Found ${#PWM_OVERLAYS[@]} PWM overlay(s)"

# Find specific overlays we need
EHRPWM1_OVERLAY=""
EHRPWM2_OVERLAY=""
AM33XX_PWM_OVERLAY=""

for overlay in "${PWM_OVERLAYS[@]}"; do
    case "$(basename "$overlay")" in
        *EHRPWM1*P9_14*P9_16* | BB-EHRPWM1*)
            EHRPWM1_OVERLAY="$overlay"
            ;;
        *EHRPWM2*P8_13*P8_19* | BB-EHRPWM2*)
            EHRPWM2_OVERLAY="$overlay"
            ;;
        am33xx_pwm* | AM33XX_PWM*)
            AM33XX_PWM_OVERLAY="$overlay"
            ;;
    esac
done

echo "📋 Selected overlays:"
echo "   PWM subsystem: ${AM33XX_PWM_OVERLAY:-'Not found'}"
echo "   EHRPWM1: ${EHRPWM1_OVERLAY:-'Not found'}"
echo "   EHRPWM2: ${EHRPWM2_OVERLAY:-'Not found'}"

# Remove existing PWM overlay configurations to avoid conflicts
echo
echo "🧹 Cleaning existing PWM configurations..."
sed -i '/uboot_overlay_addr.*pwm/Id' /boot/uEnv.txt
sed -i '/uboot_overlay_addr.*PWM/Id' /boot/uEnv.txt
sed -i '/uboot_overlay_addr.*EHRPWM/Id' /boot/uEnv.txt

# Add PWM overlays to uEnv.txt
echo
echo "📝 Adding PWM overlays to uEnv.txt..."

# Add a marker for our configurations
echo "" >> /boot/uEnv.txt
echo "# Hardware PWM configuration - Added by setup_bbb_pwm.sh $(date)" >> /boot/uEnv.txt

# Add AM33XX PWM overlay (enables PWM subsystem)
if [ -n "$AM33XX_PWM_OVERLAY" ]; then
    echo "uboot_overlay_addr6=$AM33XX_PWM_OVERLAY" >> /boot/uEnv.txt
    echo "   ✓ Added PWM subsystem overlay"
fi

# Add EHRPWM overlays
if [ -n "$EHRPWM1_OVERLAY" ]; then
    echo "uboot_overlay_addr7=$EHRPWM1_OVERLAY" >> /boot/uEnv.txt
    echo "   ✓ Added EHRPWM1 overlay (P9_14, P9_16)"
fi

if [ -n "$EHRPWM2_OVERLAY" ]; then
    echo "uboot_overlay_addr8=$EHRPWM2_OVERLAY" >> /boot/uEnv.txt
    echo "   ✓ Added EHRPWM2 overlay (P8_13, P8_19)"
fi

# Ensure cape universal is enabled (needed for pin muxing)
if ! grep -q "enable_uboot_cape_universal=1" /boot/uEnv.txt; then
    echo "enable_uboot_cape_universal=1" >> /boot/uEnv.txt
    echo "   ✓ Enabled cape universal"
fi

if ! grep -q "cape_universal=enable" /boot/uEnv.txt; then
    echo "cape_universal=enable" >> /boot/uEnv.txt
    echo "   ✓ Enabled cape universal (alternative)"
fi

# Show final uEnv.txt configuration
echo
echo "📄 Final uEnv.txt PWM configuration:"
echo "-----------------------------------"
grep -A 10 -B 2 "Hardware PWM configuration" /boot/uEnv.txt || echo "No PWM config section found"

# Install Python dependencies if needed
echo
echo "🐍 Checking Python dependencies..."
if ! python3 -c "import periphery" 2>/dev/null; then
    echo "   Installing python3-periphery..."
    apt-get update -qq
    apt-get install -y python3-periphery || pip3 install periphery
fi

# Create PWM test script
echo
echo "📜 Creating PWM test script..."
cat > /home/$(logname 2>/dev/null || echo 'debian')/test_pwm_setup.py << 'EOL'
#!/usr/bin/env python3
"""
PWM Setup Validation Script
Tests if hardware PWM is working after BBB setup
"""

import os
import time

def test_pwm_channel(chip, channel, pin_name):
    """Test a PWM channel"""
    pwm_path = f"/sys/class/pwm/pwmchip{chip}/pwm{channel}"
    chip_path = f"/sys/class/pwm/pwmchip{chip}"
    
    try:
        # Check if chip exists
        if not os.path.exists(chip_path):
            return False, f"PWM chip {chip} not found"
        
        # Export
        if not os.path.exists(pwm_path):
            with open(f"{chip_path}/export", "w") as f:
                f.write(str(channel))
            time.sleep(0.1)
        
        # Configure 1Hz, 50% duty for easy testing
        with open(f"{pwm_path}/period", "w") as f:
            f.write("1000000000")  # 1 second
        
        with open(f"{pwm_path}/duty_cycle", "w") as f:
            f.write("500000000")   # 50%
        
        # Enable
        with open(f"{pwm_path}/enable", "w") as f:
            f.write("1")
        
        time.sleep(2)  # Test for 2 seconds
        
        # Disable and cleanup
        with open(f"{pwm_path}/enable", "w") as f:
            f.write("0")
        
        with open(f"{chip_path}/unexport", "w") as f:
            f.write(str(channel))
        
        return True, "OK"
        
    except Exception as e:
        return False, str(e)

def main():
    print("🧪 BBB Hardware PWM Setup Validation")
    print("====================================")
    
    test_pins = [
        (0, 0, "P9_14"),
        (1, 0, "P8_19"), 
        (1, 1, "P8_13"),
        (2, 0, "P8_19_alt"),
        (2, 1, "P8_13_alt"),
    ]
    
    working_channels = 0
    
    for chip, channel, pin in test_pins:
        print(f"Testing PWM{chip}.{channel} ({pin})...", end=" ")
        success, message = test_pwm_channel(chip, channel, pin)
        
        if success:
            print("✅ WORKING")
            working_channels += 1
        else:
            print(f"❌ FAILED: {message}")
    
    print(f"\n📊 Results: {working_channels} PWM channels working")
    
    if working_channels >= 2:
        print("✅ SUCCESS! Hardware PWM is functional")
        print("   You can now use hardware PWM in your projects")
    elif working_channels == 1:
        print("⚠️  PARTIAL: Some PWM channels working")
        print("   Check device tree overlay configuration")
    else:
        print("❌ FAILED: No PWM channels working")
        print("   Reboot required or configuration issue")

if __name__ == "__main__":
    main()
EOL

chmod +x /home/$(logname 2>/dev/null || echo 'debian')/test_pwm_setup.py
echo "   ✓ Created test_pwm_setup.py"

# Final instructions
echo
echo "✅ BBB Hardware PWM Setup Complete!"
echo "=================================="
echo
echo "📋 What was configured:"
echo "   • PWM device tree overlays added to uEnv.txt"
echo "   • Cape universal enabled for pin muxing"
echo "   • Python dependencies installed"
echo "   • Test script created"
echo
echo "🔄 NEXT STEPS:"
echo "   1. REBOOT your BeagleBone Black:"
echo "      sudo reboot"
echo
echo "   2. After reboot, test PWM functionality:"
echo "      python3 test_pwm_setup.py"
echo
echo "   3. If tests pass, use the working pin mappings:"
echo "      P9_14 → PWM0.0 (chip 0, channel 0)"
echo "      P8_19 → PWM1.0 (chip 1, channel 0)"  
echo "      P8_13 → PWM1.1 (chip 1, channel 1)"
echo
echo "💾 Backup saved as: $BACKUP_FILE"
echo "   (Restore with: cp $BACKUP_FILE /boot/uEnv.txt)"
echo
echo "📞 If you have issues:"
echo "   • Check kernel messages: dmesg | grep pwm"
echo "   • Verify overlays loaded: cat /proc/device-tree/chosen/overlays"
echo "   • Test manually: ls /sys/class/pwm/"

echo
echo "🎉 Setup complete! Reboot to activate hardware PWM."
