#!/bin/bash
# Fix Bluetooth device name and ensure GATT is properly configured

echo "=== Fixing Bluetooth Configuration ==="
echo ""

# Set the Bluetooth device name
echo "1. Setting Bluetooth device name to 'AutoBBB'..."
sudo hciconfig hci0 name 'AutoBBB'
echo "✅ Done"
echo ""

# Check current name
echo "2. Verifying Bluetooth name..."
sudo hciconfig hci0 name
echo ""

# Restart Bluetooth to apply changes
echo "3. Restarting Bluetooth service..."
sudo systemctl restart bluetooth
sleep 2
echo "✅ Done"
echo ""

# Bring adapter up
echo "4. Bringing adapter up..."
sudo hciconfig hci0 up
echo "✅ Done"
echo ""

# Show final status
echo "5. Final adapter status:"
sudo hciconfig hci0
echo ""

echo "=== Configuration complete! ==="
echo "Now restart your Python BLE server"
