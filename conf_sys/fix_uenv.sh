#!/bin/bash
echo "Fixing uEnv.txt for PWM overlays..."

# Backup the file
sudo cp /boot/uEnv.txt /boot/uEnv.txt.backup3

# Create the corrected version
sudo sed -i 's/#enable_uboot_overlays=1/enable_uboot_overlays=1/' /boot/uEnv.txt

# Remove the conflicting PWM overlay lines
sudo sed -i '/uboot_overlay_addr4=\/lib\/firmware\/am33xx_pwm-00A0.dtbo/d' /boot/uEnv.txt
sudo sed -i '/uboot_overlay_addr5=\/lib\/firmware\/BB-PWM1-00A0.dtbo/d' /boot/uEnv.txt

# Add PWM overlays to unused addresses
echo "# PWM overlays for hardware PWM support" | sudo tee -a /boot/uEnv.txt
echo "uboot_overlay_addr6=/lib/firmware/am33xx_pwm-00A0.dtbo" | sudo tee -a /boot/uEnv.txt  
echo "uboot_overlay_addr7=/lib/firmware/BB-PWM1-00A0.dtbo" | sudo tee -a /boot/uEnv.txt

echo "uEnv.txt has been corrected!"
echo "Changes made:"
echo "1. Enabled uboot overlays (uncommented enable_uboot_overlays=1)"
echo "2. Added PWM overlays to unused addresses (addr6 and addr7)"
echo "3. Kept cape-universal overlay intact"

echo ""
echo "=== Updated uEnv.txt PWM section ==="
grep -A 3 -B 3 "PWM\|pwm" /boot/uEnv.txt || echo "PWM lines not found"
