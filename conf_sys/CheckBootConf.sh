# Find and check all possible boot config files
for file in /boot/uEnv.txt /boot/firmware/uEnv.txt /boot/extlinux/extlinux.conf /boot/firmware/extlinux/extlinux.conf; do
    if [ -f "$file" ]; then
        echo "=== $file ==="
        cat "$file"
        echo ""
    fi
done
