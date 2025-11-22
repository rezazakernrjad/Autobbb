#!/bin/bash

# Fix BlueZ experimental mode with correct path

echo "=== Fixing Bluetooth Service Override ==="

# Create override with correct path
sudo tee /etc/systemd/system/bluetooth.service.d/override.conf > /dev/null <<EOF
[Service]
ExecStart=
ExecStart=/usr/sbin/bluetoothd --experimental
EOF

echo "✅ Override file updated with correct path"

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart bluetooth

sleep 2

# Verify
echo ""
echo "=== Verification ==="
if ps aux | grep -v grep | grep bluetoothd | grep -q experimental; then
    echo "✅ SUCCESS: Bluetooth running with --experimental flag"
    ps aux | grep -v grep | grep bluetoothd
else
    echo "❌ FAILED: Experimental flag not detected"
fi

echo ""
echo "Service status:"
sudo systemctl status bluetooth --no-pager | head -10
