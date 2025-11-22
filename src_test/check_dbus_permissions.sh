#!/bin/bash

echo "=== Checking D-Bus Bluetooth Permissions ==="

echo ""
echo "1. Current user groups:"
groups

echo ""
echo "2. Adding user to bluetooth group..."
sudo usermod -a -G bluetooth $USER

echo ""
echo "3. Checking D-Bus policy for Bluetooth..."
ls -la /etc/dbus-1/system.d/ | grep -i blue

echo ""
echo "4. Checking if GATT services are actually registered..."
gdbus introspect --system --dest org.bluez --object-path /org/bluez/hci0 2>&1 | grep -A 5 GattManager1

echo ""
echo "5. Listing registered GATT applications..."
busctl tree org.bluez 2>&1 | grep -i gatt

echo ""
echo "6. Checking adapter properties..."
gdbus call --system --dest org.bluez --object-path /org/bluez/hci0 --method org.freedesktop.DBus.Properties.GetAll org.bluez.Adapter1

echo ""
echo "=== IMPORTANT ==="
echo "After running this, you need to LOG OUT and LOG BACK IN for group changes to take effect"
echo "Or run: newgrp bluetooth"
