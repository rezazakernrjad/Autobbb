#!/usr/bin/env python3
"""
Direct test: Check if GATT application is actually registered with BlueZ
"""

import sys
from dbus_next.aio import MessageBus
from dbus_next import BusType
import asyncio

async def check_gatt_registration():
    print("=== Checking GATT Application Registration ===\n")
    
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    
    # Check adapter
    introspection = await bus.introspect('org.bluez', '/org/bluez/hci0')
    obj = bus.get_proxy_object('org.bluez', '/org/bluez/hci0', introspection)
    
    print("1. Checking if GattManager1 interface exists...")
    try:
        gatt_manager = obj.get_interface('org.bluez.GattManager1')
        print("   ✅ GattManager1 interface found")
    except Exception as e:
        print(f"   ❌ GattManager1 NOT found: {e}")
        print("   This means BlueZ doesn't support GATT peripheral mode!")
        return
    
    print("\n2. Checking registered GATT applications...")
    try:
        # Try to get GattManager properties
        props_iface = obj.get_interface('org.freedesktop.DBus.Properties')
        # GattManager1 doesn't have many properties, but let's check what's there
        print("   Attempting to list applications...")
        
        # Try to introspect the gatt_manager path
        try:
            gatt_introspection = await bus.introspect('org.bluez', '/org/bluez/hci0/gatt_manager')
            print("   ✅ /org/bluez/hci0/gatt_manager exists")
        except Exception as e:
            print(f"   ⚠️ Cannot introspect gatt_manager: {e}")
            
    except Exception as e:
        print(f"   ⚠️ Error checking applications: {e}")
    
    print("\n3. Searching for registered service paths...")
    # Look for our service
    try:
        introspection = await bus.introspect('org.bluez', '/')
        print("   BlueZ root paths:")
        # This is a simple check - just see what's under /org/bluez
        import subprocess
        result = subprocess.run(['busctl', 'tree', 'org.bluez'], 
                              capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if 'service' in line.lower() or 'gatt' in line.lower():
                print(f"   {line}")
    except Exception as e:
        print(f"   ⚠️ Error listing paths: {e}")
    
    print("\n4. Checking LE Advertising Manager...")
    try:
        adv_introspection = await bus.introspect('org.bluez', '/org/bluez/hci0')
        adv_obj = bus.get_proxy_object('org.bluez', '/org/bluez/hci0', adv_introspection)
        adv_manager = adv_obj.get_interface('org.bluez.LEAdvertisingManager1')
        print("   ✅ LEAdvertisingManager1 found")
        
        # Check active instances
        props = adv_obj.get_interface('org.freedesktop.DBus.Properties')
        active = await props.call_get('org.bluez.LEAdvertisingManager1', 'ActiveInstances')
        print(f"   Active advertisement instances: {active.value}")
        
    except Exception as e:
        print(f"   ❌ LEAdvertisingManager error: {e}")
    
    print("\n" + "="*50)
    print("CONCLUSION:")
    print("If GattManager1 exists but services don't appear,")
    print("the issue is likely with how bluez-peripheral registers them.")
    print("Try the direct D-Bus implementation (direct_gatt_server.py)")
    print("="*50)

if __name__ == "__main__":
    try:
        asyncio.run(check_gatt_registration())
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
