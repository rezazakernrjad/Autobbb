#!/usr/bin/env python3
"""
Debug script to test Bluetooth connection between iPad and BBB
"""

import subprocess
import time
import sys
import os

def run_command(cmd, timeout=5):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd.split(), 
                              capture_output=True, 
                              text=True, 
                              timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_bluetooth_status():
    """Check basic Bluetooth functionality"""
    print("=" * 60)
    print("🔍 BLUETOOTH SYSTEM STATUS")
    print("=" * 60)
    
    # Check if Bluetooth is up
    success, output, error = run_command("hciconfig")
    if success:
        print("✅ Bluetooth adapter found:")
        for line in output.split('\n'):
            if 'hci' in line or 'UP' in line or 'RUNNING' in line:
                print(f"   {line.strip()}")
    else:
        print("❌ Bluetooth adapter not found or not working")
        print(f"Error: {error}")
        return False
    
    return True

def check_active_connections():
    """Check for active Bluetooth connections"""
    print("\n" + "=" * 60)
    print("📱 ACTIVE BLUETOOTH CONNECTIONS")
    print("=" * 60)
    
    success, output, error = run_command("hcitool con")
    if success and output.strip():
        lines = output.strip().split('\n')[1:]  # Skip header
        if lines and any(line.strip() for line in lines):
            print("✅ Active connections found:")
            for line in lines:
                if line.strip():
                    print(f"   {line.strip()}")
                    # Try to get RSSI for each connection
                    parts = line.split()
                    if len(parts) >= 3:
                        addr = parts[2]
                        rssi_success, rssi_out, _ = run_command(f"hcitool rssi {addr}")
                        if rssi_success:
                            print(f"   RSSI: {rssi_out.strip()}")
        else:
            print("❌ No active Bluetooth connections")
    else:
        print("❌ Could not check connections")
        print(f"Error: {error}")

def check_ble_advertising():
    """Check if BLE advertising is active"""
    print("\n" + "=" * 60)
    print("📡 BLE ADVERTISING STATUS")
    print("=" * 60)
    
    # Check if bluetoothd is running
    success, output, error = run_command("systemctl is-active bluetooth")
    if success and "active" in output:
        print("✅ Bluetooth service is running")
    else:
        print("❌ Bluetooth service not running properly")
        print("Try: sudo systemctl restart bluetooth")
    
    # Check for Python BLE server processes
    success, output, error = run_command("pgrep -f python")
    if success and output.strip():
        print("✅ Python processes found:")
        for pid in output.strip().split('\n'):
            cmd_success, cmd_output, _ = run_command(f"ps -p {pid} -o cmd=")
            if cmd_success and ('bt_' in cmd_output or 'auto_run' in cmd_output):
                print(f"   PID {pid}: {cmd_output.strip()}")
    else:
        print("❌ No Python BLE server process found")
        print("Make sure to run: python3 src/auto_run.py")

def test_ble_server_files():
    """Check if BLE server files exist and are accessible"""
    print("\n" + "=" * 60)
    print("📁 BLE SERVER FILES")
    print("=" * 60)
    
    required_files = [
        'src/auto_run.py',
        'src/bt_lib.py', 
        'src/pin_lib.py',
        'src/pwm_lib.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")

def monitor_bluetooth_logs():
    """Monitor Bluetooth logs for connection attempts"""
    print("\n" + "=" * 60)
    print("📋 RECENT BLUETOOTH LOGS")
    print("=" * 60)
    
    # Check systemd logs for Bluetooth
    success, output, error = run_command("journalctl -u bluetooth --no-pager -n 10")
    if success:
        print("Recent Bluetooth service logs:")
        print(output)
    else:
        print("Could not access Bluetooth logs")

def interactive_debug_menu():
    """Interactive debugging menu"""
    while True:
        print("\n" + "=" * 60)
        print("🔧 INTERACTIVE DEBUGGING MENU")
        print("=" * 60)
        print("1. Check Bluetooth status")
        print("2. Check active connections") 
        print("3. Check BLE advertising")
        print("4. Check server files")
        print("5. Monitor Bluetooth logs")
        print("6. Test RSSI of connected device")
        print("7. Start BLE server (auto_run.py)")
        print("8. Full system check")
        print("9. Exit")
        
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == '1':
            check_bluetooth_status()
        elif choice == '2':
            check_active_connections()
        elif choice == '3':
            check_ble_advertising()
        elif choice == '4':
            test_ble_server_files()
        elif choice == '5':
            monitor_bluetooth_logs()
        elif choice == '6':
            test_rssi()
        elif choice == '7':
            start_ble_server()
        elif choice == '8':
            full_system_check()
        elif choice == '9':
            print("Exiting debug tool...")
            break
        else:
            print("Invalid choice. Please try again.")

def test_rssi():
    """Test RSSI measurement"""
    print("\n🔍 Testing RSSI measurement...")
    success, output, error = run_command("hcitool con")
    if success:
        lines = output.strip().split('\n')[1:]
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    addr = parts[2]
                    print(f"Testing RSSI for {addr}...")
                    rssi_success, rssi_out, rssi_err = run_command(f"hcitool rssi {addr}")
                    if rssi_success:
                        print(f"✅ RSSI: {rssi_out.strip()}")
                    else:
                        print(f"❌ RSSI failed: {rssi_err}")

def start_ble_server():
    """Start the BLE server"""
    print("\n🚀 Starting BLE server...")
    print("This will run in foreground. Press Ctrl+C to stop.")
    print("Switch to another terminal to continue debugging.")
    
    if os.path.exists('src/auto_run.py'):
        try:
            subprocess.run(['python3', 'src/auto_run.py'])
        except KeyboardInterrupt:
            print("\nBLE server stopped.")
    else:
        print("❌ auto_run.py not found in src/ directory")

def full_system_check():
    """Run all checks"""
    print("\n🔬 RUNNING FULL SYSTEM CHECK")
    print("=" * 60)
    
    check_bluetooth_status()
    check_active_connections()
    check_ble_advertising()
    test_ble_server_files()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY & RECOMMENDATIONS")
    print("=" * 60)
    print("1. If no Python BLE server found: run 'python3 src/auto_run.py'")
    print("2. If no active connections: make sure iPad is scanning and connecting")
    print("3. If connections exist but no data received: check command format mismatch")
    print("4. Monitor the server terminal for incoming connection attempts")

if __name__ == "__main__":
    print("BBB Bluetooth Debug Tool")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        full_system_check()
    else:
        interactive_debug_menu()