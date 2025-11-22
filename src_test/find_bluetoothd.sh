#!/bin/bash

echo "=== Finding bluetoothd binary location ==="
which bluetoothd
whereis bluetoothd

echo ""
echo "=== Checking possible locations ==="
for path in /usr/sbin/bluetoothd /usr/libexec/bluetooth/bluetoothd /usr/lib/bluetooth/bluetoothd /usr/local/sbin/bluetoothd; do
    if [ -f "$path" ]; then
        echo "✅ Found: $path"
        BLUETOOTHD_PATH="$path"
    fi
done

echo ""
echo "=== Current bluetooth.service configuration ==="
systemctl cat bluetooth.service | grep ExecStart
