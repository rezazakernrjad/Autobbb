#!/bin/bash
# Script to reset Bluetooth on BeagleBone Black
# Run this if iPad can't discover services after reconnection

echo "🔄 Resetting Bluetooth adapter..."

# Stop any running BLE services
sudo systemctl stop bluetooth

# Power cycle the Bluetooth adapter
sudo hciconfig hci0 down
sleep 1
sudo hciconfig hci0 up

# Restart Bluetooth service
sudo systemctl start bluetooth

# Wait for Bluetooth to initialize
sleep 2

echo "✅ Bluetooth reset complete"
echo "Now restart your Python BLE server (bt_lib.py)"
