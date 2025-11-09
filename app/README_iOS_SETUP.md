# BBB Controller iOS App - Setup Instructions for Mac/Xcode

## Project Overview
This is a Flutter iOS app designed to control a BeagleBone Black (BBB) via Bluetooth Low Energy (BLE).

## Project Structure (iOS-only)
```
app/
├── pubspec.yaml                          # Flutter dependencies
├── lib/
│   └── main.dart                         # Flutter app code
└── ios/
    ├── Runner.xcodeproj/
    │   └── project.pbxproj               # Xcode project file
    └── Runner/
        ├── Info.plist                    # iOS app configuration & BLE permissions
        ├── AppDelegate.h/.m              # iOS app delegate
        ├── GeneratedPluginRegistrant.h/.m # Plugin registration (fixes build errors)
        └── main.m                        # iOS app entry point
```

## Key Features
- **Bluetooth Low Energy (BLE)** communication with BBB
- **iOS permissions** properly configured for Bluetooth access
- **Fixed build errors**: GeneratedPluginRegistrant, Module, flutter_blue_plus_darwin

## Commands to Run on Mac

### 1. Install Flutter Dependencies
```bash
cd path/to/app
flutter pub get
```

### 2. Generate any missing iOS files
```bash
flutter create --platforms=ios .
```

### 3. Clean and rebuild
```bash
flutter clean
flutter pub get
```

### 4. Open in Xcode
```bash
open ios/Runner.xcodeproj
```

### 5. Build for iPad
In Xcode:
- Select your iPad as target device
- Ensure proper signing certificates are configured
- Build and run (Cmd+R)

## Bluetooth Permissions
The app requests these iOS permissions (already configured in Info.plist):
- `NSBluetoothAlwaysUsageDescription`
- `NSBluetoothPeripheralUsageDescription` 
- `NSBluetoothAdvertisingUsageDescription`

## Flutter Dependencies
- `flutter_blue_plus: ^1.31.15` - Bluetooth Low Energy
- `permission_handler: ^11.0.1` - iOS permissions

## BLE Service Configuration
The app connects to BBB using these UUIDs:
- Service: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
- RX (write): `6E400002-B5A3-F393-E0A9-E50E24DCCA9E`

## Commands the App Sends
- `"lamps"` - Control lamps
- `"ping"` - Test connection
- `"status"` - Get BBB status
- `"left XX"` - Left PWM control (XX = value)
- `"right XX"` - Right PWM control (XX = value)

## Troubleshooting

### If build fails with missing files:
```bash
flutter clean
flutter pub get
flutter create --platforms=ios .
```

### If Bluetooth permissions denied:
- Check that Info.plist contains all NSBluetooth* permissions
- Ensure app requests permissions in code (already implemented)

### If connection fails:
- Verify BBB is running the correct BLE server (`src/auto_run.py`)
- Check that BBB advertises as "BBB-PosServer"
- Monitor BBB terminal for connection attempts

## Next Steps After Building
1. Install app on iPad
2. Start BBB BLE server: `python3 src/auto_run.py`
3. Scan for "BBB-PosServer" in app
4. Connect and test commands (start with "ping")

## Notes
- This is an iOS-only project (Android files removed)
- Designed for iPad but works on iPhone too
- Requires iOS 11.0+ (configured in Xcode project)
- Bundle ID: `com.example.bbbController` (change if needed)