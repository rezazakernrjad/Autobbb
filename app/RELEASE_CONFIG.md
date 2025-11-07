# App Configuration for Release

## Update these files before building release:

### 1. App Information (ios/Runner/Info.plist)
```xml
<key>CFBundleDisplayName</key>
<string>BBB Controller</string>
<key>CFBundleIdentifier</key>
<string>com.yourcompany.bbbcontroller</string>
<key>CFBundleVersion</key>
<string>1.0.0</string>
<key>CFBundleShortVersionString</key>
<string>1.0.0</string>
```

### 2. App Description
```xml
<key>NSBluetoothAlwaysUsageDescription</key>
<string>BBB Controller needs Bluetooth to communicate with BeagleBone Black device for remote control functionality</string>
```

### 3. Bundle Identifier
Change `com.example.bbbController` to something unique like:
- `com.yourname.bbbcontroller`
- `com.yourcompany.bbbcontroller`

### 4. Version Management
- **CFBundleShortVersionString**: User-facing version (1.0.0, 1.1.0, etc.)
- **CFBundleVersion**: Build number (1, 2, 3, etc.)

## Signing Options:

### Free Apple ID (Personal Use):
- ✅ No cost
- ❌ Apps expire after 7 days
- ❌ Limited to 3 apps per device
- ❌ Must reinstall weekly

### Apple Developer Account ($99/year):
- ✅ Apps don't expire
- ✅ TestFlight distribution
- ✅ App Store publishing
- ✅ Up to 100 Ad Hoc devices
- ✅ Enterprise features

## Quick Start Commands:

```bash
# Make script executable
chmod +x build_release.sh

# Build release
./build_release.sh

# Or manual build
flutter build ios --release --no-codesign
open ios/Runner.xcodeproj
```