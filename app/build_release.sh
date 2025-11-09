#!/bin/bash

# BBB Controller - Release Build Script
# Run this on your Mac to create a standalone iOS app

set -e  # Exit on any error

echo "🚀 BBB Controller - Release Build Process"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "pubspec.yaml" ]; then
    echo "❌ Error: Run this script from the app/ directory"
    echo "Usage: ./build_release.sh"
    exit 1
fi

# Check if Flutter is available
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter not found! Make sure Flutter is in your PATH"
    exit 1
fi

echo "✅ Flutter found: $(flutter --version | head -n 1)"

# Step 1: Clean previous builds
echo ""
echo "🧹 Cleaning previous builds..."
flutter clean

# Step 2: Get dependencies
echo ""
echo "📦 Getting dependencies..."
flutter pub get

# Step 3: Build release
echo ""
echo "📱 Building iOS release..."
echo "This may take a few minutes..."

flutter build ios --release --no-codesign

if [ $? -eq 0 ]; then
    echo "✅ Flutter build completed successfully!"
else
    echo "❌ Flutter build failed!"
    exit 1
fi

# Step 4: Prepare for Xcode Archive
echo ""
echo "🎯 Build completed! Next steps:"
echo "================================"
echo ""
echo "1. Open Xcode project:"
echo "   open ios/Runner.xcodeproj"
echo ""
echo "2. In Xcode:"
echo "   • Select 'Any iOS Device' (not simulator)"
echo "   • Product → Archive"
echo "   • Wait for archive to complete"
echo ""
echo "3. In Organizer (opens automatically):"
echo "   • Select your archive"
echo "   • Click 'Distribute App'"
echo "   • Choose distribution method:"
echo "     - Development (your devices only)"
echo "     - Ad Hoc (specific devices)"
echo "     - App Store (public distribution)"
echo ""
echo "4. Export and save the .ipa file"
echo ""
echo "5. Install methods:"
echo "   • AltStore (free, no developer account needed)"
echo "   • Apple Configurator 2 (free, via USB)"
echo "   • TestFlight (requires developer account)"
echo ""

# Ask if user wants to open Xcode
echo ""
read -p "🤔 Would you like to open Xcode now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Opening Xcode..."
    open ios/Runner.xcodeproj
    echo ""
    echo "📝 Remember:"
    echo "• Select 'Any iOS Device' as target"
    echo "• Product → Archive to create distributable build"
else
    echo "👍 You can open Xcode later with:"
    echo "   open ios/Runner.xcodeproj"
fi

echo ""
echo "🎉 Release build process initiated!"
echo "📖 Check RELEASE_GUIDE.md for detailed distribution instructions"