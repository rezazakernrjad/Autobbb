#!/usr/bin/env python3
"""
Test script to verify bluez-peripheral is working correctly
Run this to diagnose BLE GATT service registration issues
"""
import asyncio
from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.agent import NoIoAgent
from bluez_peripheral.util import get_message_bus
import subprocess

class TestService(Service):
    def __init__(self):
        super().__init__("6E400001-B5A3-F393-E0A9-E50E24DCCA9E", True)
        self.value = b'test'
    
    @characteristic("6E400002-B5A3-F393-E0A9-E50E24DCCA9E", CharFlags.WRITE | CharFlags.WRITE_WITHOUT_RESPONSE)
    def test_char(self, options):
        return self.value
    
    @test_char.setter
    def test_char(self, value, options):
        print(f"Received: {value}")
        self.value = value

async def test_registration():
    print("="*50)
    print("Testing bluez-peripheral GATT registration")
    print("="*50)
    
    try:
        # Get D-Bus
        print("\n1. Getting D-Bus connection...")
        bus = await get_message_bus()
        print("   ✅ D-Bus connected")
        
        # Register agent
        print("\n2. Registering agent...")
        agent = NoIoAgent()
        await agent.register(bus)
        print("   ✅ Agent registered")
        
        # Register service
        print("\n3. Registering GATT service...")
        service = TestService()
        await service.register(bus)
        print("   ✅ Service registered")
        
        # Wait a bit for registration to propagate
        await asyncio.sleep(1)
        
        # Check if registered
        print("\n4. Verifying registration in D-Bus...")
        result = subprocess.run(
            ['busctl', 'tree', 'org.bluez'],
            capture_output=True, text=True, timeout=5
        )
        print(result.stdout)
        
        result2 = subprocess.run(
            ['busctl', 'introspect', 'org.bluez', '/org/bluez/hci0'],
            capture_output=True, text=True, timeout=5
        )
        
        if '6e400001' in result2.stdout.lower():
            print("\n✅ SUCCESS: Service UUID found in D-Bus!")
            print("   bluez-peripheral is working correctly")
        else:
            print("\n❌ FAILURE: Service UUID NOT found in D-Bus")
            print("   Possible issues:")
            print("   - bluez-peripheral version incompatible")
            print("   - D-Bus permissions problem")
            print("   - BlueZ service not running properly")
        
        # Register advertisement
        print("\n5. Testing advertisement...")
        advert = Advertisement("BBB-Test", ["6E400001-B5A3-F393-E0A9-E50E24DCCA9E"], 0x0340, 60)
        await advert.register(bus)
        print("   ✅ Advertisement registered")
        
        print("\n6. Keeping service running for 30 seconds...")
        print("   Try scanning from your iPad/phone")
        await asyncio.sleep(30)
        
        # Cleanup
        print("\n7. Cleaning up...")
        await advert.stop(bus)
        await service.unregister()
        await agent.unregister(bus)
        print("   ✅ Cleanup done")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting BLE test...")
    print("Make sure bluetooth service is running: sudo systemctl start bluetooth")
    print("Make sure adapter is up: sudo hciconfig hci0 up\n")
    
    asyncio.run(test_registration())
