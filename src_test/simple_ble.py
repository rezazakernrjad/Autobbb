"""
Direct DBus implementation for BLE GATT server
"""
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import signal
import time

class BTService(dbus.service.Object):
    def __init__(self, bus_path, uuid):
        self.path = bus_path
        self.uuid = uuid
        self.characteristics = {}
        self.write_callbacks = {}
        dbus.service.Object.__init__(self, dbus.SystemBus(), bus_path)

    def add_characteristic(self, uuid, flags, write_callback=None):
        char_path = self.path + "/char_" + uuid[:8]
        char = BTCharacteristic(char_path, uuid, flags, write_callback)
        self.characteristics[uuid] = char
        return char

class BTCharacteristic(dbus.service.Object):
    def __init__(self, char_path, uuid, flags, write_callback=None):
        self.path = char_path
        self.uuid = uuid
        self.flags = flags
        self.value = []
        self.write_callback = write_callback
        dbus.service.Object.__init__(self, dbus.SystemBus(), char_path)

    @dbus.service.method("org.bluez.GattCharacteristic1",
                         in_signature="a{sv}",
                         out_signature="ay")
    def ReadValue(self, options):
        print(f"📖 ReadValue called for {self.uuid}")
        return self.value

    @dbus.service.method("org.bluez.GattCharacteristic1",
                         in_signature="aya{sv}")
    def WriteValue(self, value, options):
        print(f"📝 WriteValue called for {self.uuid}")
        print(f"   Value: {value}")
        print(f"   Options: {options}")
        
        self.value = value
        
        if self.write_callback:
            self.write_callback(value, options)

def run_simple_server():
    """Run a simple BLE server using direct DBus"""
    print("🎯 Starting Simple BLE Server...")
    
    # This is a simplified version - you'd need to implement the full
    # DBus GATT profile registration
    
    mainloop = GLib.MainLoop()
    
    try:
        print("✅ Server running (press Ctrl+C to stop)")
        mainloop.run()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

if __name__ == "__main__":
    run_simple_server()