#!/bin/bash

# This script verifies if BlueZ is properly exposing GATT services

echo "=== BlueZ GATT Service Verification ==="
echo ""

echo "1. Checking if bluetoothd is running with experimental features..."
ps aux | grep bluetoothd

echo ""
echo "2. Checking GATT manager status..."
gdbus introspect --system --dest org.bluez --object-path /org/bluez/hci0 | grep GattManager1

echo ""
echo "3. Checking currently registered GATT applications..."
gdbus introspect --system --dest org.bluez --object-path /org/bluez/hci0/gatt_manager

echo ""
echo "4. Checking if adapter is in peripheral mode..."
hciconfig hci0

echo ""
echo "5. Checking adapter settings..."
bluetoothctl show

echo ""
echo "=== CRITICAL: bluetoothd MUST be started with --experimental flag ==="
echo "To enable: sudo systemctl edit bluetooth.service"
echo "Add these lines:"
echo "[Service]"
echo "ExecStart="
echo "ExecStart=/usr/lib/bluetooth/bluetoothd --experimental"
echo ""
echo "Then: sudo systemctl daemon-reload && sudo systemctl restart bluetooth"
