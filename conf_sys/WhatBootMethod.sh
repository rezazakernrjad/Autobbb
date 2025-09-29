# Check boot partition
ls -la /boot/
ls -la /boot/firmware/ 2>/dev/null || echo "No /boot/firmware"

# Check if system uses U-Boot or systemd-boot
ls /boot/u-boot* 2>/dev/null || echo "No U-Boot files found"
ls /boot/EFI/ 2>/dev/null || echo "No EFI directory"

# Check mount points
mount | grep boot
