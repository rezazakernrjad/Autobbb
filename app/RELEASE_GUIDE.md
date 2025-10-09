# 📱 BBB Controller - Standalone iOS App Distribution Guide

## 🎯 Goal: Run app independently from Xcode

There are several ways to distribute your iOS app without requiring Xcode:

## 🚀 Option 1: Build Release IPA (Recommended for Personal Use)

### Step 1: Build Release Archive
```bash
# In your app directory on Mac
flutter build ios --release

# Alternative: Build with specific signing
flutter build ios --release --codesign
```

### Step 2: Create Archive in Xcode
```bash
# Open Xcode project
open ios/Runner.xcodeproj

# In Xcode:
# 1. Select "Any iOS Device" as target (not simulator)
# 2. Product → Archive
# 3. Wait for build to complete
# 4. Organizer window will open
```

### Step 3: Export IPA
In Xcode Organizer:
1. Select your archive
2. Click "Distribute App"
3. Choose distribution method:
   - **Development**: For your devices only
   - **Ad Hoc**: For specific devices (up to 100)
   - **Enterprise**: For organization-wide distribution
   - **App Store**: For public distribution

### Step 4: Install via Multiple Methods

**Method A: AltStore (No Developer Account Needed)**
```bash
# Install AltStore on your devices
# Drag .ipa file to AltStore
# App installs directly on device
```

**Method B: Apple Configurator 2**
```bash
# Download Apple Configurator 2 from Mac App Store
# Connect iPad via USB
# Drag .ipa to device in Configurator
```

**Method C: TestFlight (Requires Developer Account)**
```bash
# Upload to App Store Connect
# Add testers via email
# They install via TestFlight app
```

## 🔧 Option 2: Development Signing (Free)

### Configure Development Signing:
1. **In Xcode Project Settings:**
   - Team: Add your Apple ID
   - Signing: Automatic
   - Bundle ID: Change to unique identifier

2. **Build and Install:**
   ```bash
   flutter build ios --debug
   # Install directly to connected device
   ```

3. **Trust Developer on Device:**
   - Settings → General → VPN & Device Management
   - Trust your developer profile

### Limitations:
- Apps expire after 7 days (free account) or 1 year (paid account)
- Must re-install periodically
- Only works on registered devices

## 💰 Option 3: Apple Developer Program ($99/year)

### Benefits:
- Apps don't expire
- TestFlight distribution (up to 10,000 testers)
- App Store distribution
- Enterprise features

### Setup:
1. **Join Apple Developer Program**
2. **Configure Signing:**
   ```bash
   # In Xcode, select your paid developer team
   # Enable automatic signing
   ```
3. **Distribution Options:**
   - **Ad Hoc**: Direct .ipa distribution
   - **TestFlight**: Beta testing platform
   - **App Store**: Public distribution

## 🛠️ Quick Setup Script for Release Build

Create this script on your Mac:

```bash
#!/bin/bash
# build_release.sh

echo "🚀 Building BBB Controller Release..."

# Clean previous builds
flutter clean
flutter pub get

# Build iOS release
echo "📱 Building iOS release..."
flutter build ios --release

echo "✅ Build complete!"
echo "📁 Next steps:"
echo "1. Open ios/Runner.xcodeproj in Xcode"
echo "2. Select 'Any iOS Device' target"
echo "3. Product → Archive"
echo "4. Distribute App → Development/Ad Hoc"
echo "5. Export .ipa file"

# Optional: Open Xcode automatically
read -p "Open Xcode now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open ios/Runner.xcodeproj
fi
```

## 📋 Preparation Checklist

### Before Building Release:

1. **Update App Info:**
   ```bash
   # Edit ios/Runner/Info.plist
   # Update CFBundleDisplayName, CFBundleVersion, etc.
   ```

2. **App Icon:**
   ```bash
   # Add app icons to ios/Runner/Assets.xcassets/AppIcon.appiconset/
   # Sizes: 20x20, 29x29, 40x40, 60x60, 76x76, 83.5x83.5, 1024x1024
   ```

3. **Launch Screen:**
   ```bash
   # Customize ios/Runner/Base.lproj/LaunchScreen.storyboard
   ```

4. **Signing Configuration:**
   ```bash
   # Ensure proper signing in Xcode project settings
   ```

## 🔄 Distribution Workflow

### For Personal Use (Free):
```
Code → Build → Archive → Export IPA → AltStore/Configurator → Install
```

### For Team Distribution (Paid):
```
Code → Build → Archive → Export Ad Hoc → Share IPA → Manual Install
```

### For Beta Testing (Paid):
```
Code → Build → Archive → Upload to TestFlight → Invite Testers → Auto Install
```

### For Public Release (Paid):
```
Code → Build → Archive → Upload to App Store → Review → Public Download
```

## 🚨 Common Issues & Solutions

### Issue: "Untrusted Developer"
**Solution:** Settings → General → VPN & Device Management → Trust Profile

### Issue: "App Won't Install"
**Solution:** Check device is registered in provisioning profile

### Issue: "Expired Certificate"
**Solution:** Rebuild with current certificates/provisioning

### Issue: "Wrong Architecture"
**Solution:** Build for device, not simulator

## 🎯 Recommended Approach

**For Getting Started:**
1. Use free Apple ID with development signing
2. Build and install directly via Xcode
3. Accept 7-day expiration for testing

**For Regular Use:**
1. Get Apple Developer account ($99/year)
2. Use TestFlight for easy distribution
3. Share with team via email invites

**For Wide Distribution:**
1. Publish to App Store
2. Public download availability
3. Automatic updates

## 📁 Files You'll Need

After building, you'll have:
- `Runner.ipa` - The installable app file
- Provisioning profiles - Device authorization
- Certificates - Code signing credentials

Would you like me to create the build script or help with any specific distribution method?