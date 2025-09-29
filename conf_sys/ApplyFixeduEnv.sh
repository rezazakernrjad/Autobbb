# Run the fix
sudo chmod +x fix_uenv.sh
./fix_uenv.sh

# Verify the changes
echo "=== Checking changes ==="
grep "enable_uboot_overlays" /boot/uEnv.txt
grep "pwm" /boot/uEnv.txt

# Reboot to apply changes
echo "Rebooting to apply overlay changes..."
sudo reboot
