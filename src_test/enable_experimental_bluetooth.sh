#!/bin/bash

# Enable experimental Bluetooth features for GATT peripheral support

echo "=== Enabling BlueZ Experimental Mode ==="

# Create override directory if it doesn't exist
sudo mkdir -p /etc/systemd/system/bluetooth.service.d/

# Create override configuration
echo "Creating Bluetooth service override..."
sudo tee /etc/systemd/system/bluetooth.service.d/override.conf > /dev/null <<EOF
[Service]
ExecStart=
ExecStart=/usr/lib/bluetooth/bluetoothd --experimental
EOF

echo "✅ Override file created"

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Restart Bluetooth service
echo "Restarting Bluetooth service..."
sudo systemctl restart bluetooth

# Wait a moment
sleep 2

# Verify
echo ""
echo "=== Verification ==="
if ps aux | grep -v grep | grep bluetoothd | grep -q experimental; then
    echo "✅ SUCCESS: Bluetooth running with --experimental flag"
else
    echo "❌ FAILED: Experimental flag not detected"
    echo ""
    echo "Current bluetoothd process:"
    ps aux | grep -v grep | grep bluetoothd
fi

echo ""
echo "Bluetooth service status:"
sudo systemctl status bluetooth --no-pager | head -15
