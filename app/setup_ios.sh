#!/bin/bash

# BBB Controller iOS Setup Script for Mac
# Run this script on your Mac after transferring the project

echo "🚀 Setting up BBB Controller Flutter iOS Project..."
echo "=================================================="

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter not found! Please install Flutter first:"
    echo "   https://docs.flutter.dev/get-started/install/macos"
    exit 1
fi

echo "✅ Flutter found: $(flutter --version | head -n 1)"

# Check if we're in the right directory
if [ ! -f "pubspec.yaml" ]; then
    echo "❌ pubspec.yaml not found! Please run this script from the app/ directory"
    exit 1
fi

echo "✅ Found pubspec.yaml"

# Generate iOS platform files
echo "📱 Generating iOS platform files..."
flutter create --platforms=ios .

if [ $? -eq 0 ]; then
    echo "✅ iOS platform files generated successfully"
else
    echo "❌ Failed to generate iOS platform files"
    exit 1
fi

# Clean and get dependencies with plugin fix
echo "🧹 Cleaning Flutter project..."
flutter clean

echo "📦 Installing Flutter dependencies..."
flutter pub get

# Force plugin registration update
echo "🔧 Updating plugin registrations..."
flutter pub deps

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Add Bluetooth permissions to Info.plist
echo "🔵 Adding Bluetooth permissions to Info.plist..."
INFO_PLIST="ios/Runner/Info.plist"

if [ -f "$INFO_PLIST" ]; then
    # Check if permissions already exist
    if grep -q "NSBluetoothAlwaysUsageDescription" "$INFO_PLIST"; then
        echo "✅ Bluetooth permissions already exist in Info.plist"
    else
        # Add permissions before </dict>
        sed -i '' '/<\/dict>/i\
	<!-- Bluetooth permissions for flutter_blue_plus -->\
	<key>NSBluetoothAlwaysUsageDescription</key>\
	<string>This app needs Bluetooth access to communicate with BeagleBone Black device</string>\
	<key>NSBluetoothPeripheralUsageDescription</key>\
	<string>This app needs Bluetooth access to communicate with BeagleBone Black device</string>\
	<key>NSBluetoothAdvertisingUsageDescription</key>\
	<string>This app needs Bluetooth advertising to discover BeagleBone Black device</string>
' "$INFO_PLIST"
        echo "✅ Bluetooth permissions added to Info.plist"
    fi
else
    echo "⚠️  Info.plist not found at $INFO_PLIST"
fi

# Final checks
echo "🔍 Running final checks..."

flutter doctor > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Flutter doctor passed"
else
    echo "⚠️  Flutter doctor has warnings (this might be normal)"
fi

# Check if Xcode project was created
if [ -f "ios/Runner.xcodeproj/project.pbxproj" ]; then
    echo "✅ Xcode project created successfully"
else
    echo "❌ Xcode project not found"
    exit 1
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================================================="
echo "Next steps:"
echo "1. Open Xcode project: open ios/Runner.xcodeproj"
echo "2. Select your iPad as target device"
echo "3. Configure signing certificates if needed"
echo "4. Build and run (⌘+R)"
echo ""
echo "App Commands for BBB:"
echo "- 'lamps' - Control lamps"
echo "- 'ping' - Test connection" 
echo "- 'status' - Get BBB status"
echo "- 'left XX' - Left PWM control"
echo "- 'right XX' - Right PWM control"
echo ""
echo "Make sure BBB is running: python3 src/auto_run.py"