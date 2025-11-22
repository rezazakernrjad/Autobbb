#!/bin/bash
# Check if BLE services are properly registered
# Run this while your Python BLE server is running

echo "=== Checking BLE Services ==="
echo ""

echo "1. Bluetooth adapter status:"
sudo hciconfig hci0
echo ""

echo "2. Active BLE advertisements:"
sudo hcitool -i hci0 cmd 0x08 0x0009
echo ""

echo "3. D-Bus GATT services (look for 6E400001):"
busctl tree org.bluez
echo ""

echo "4. Check if service UUID is registered:"
busctl introspect org.bluez /org/bluez/hci0 | grep -i 6e400001
echo ""

echo "=== If you see the service UUID above, BLE is working correctly ==="
echo "=== If not, restart your Python script ==="
