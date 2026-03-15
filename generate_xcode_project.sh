#!/bin/bash
#
# generate_xcode_project.sh
# Generates a proper Xcode project for CortexOS multiplatform app.
#
# Usage:
#   chmod +x generate_xcode_project.sh
#   ./generate_xcode_project.sh
#
# Requirements: Xcode 15+ installed
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
APP_DIR="$PROJECT_ROOT/CortexOSApp"

echo "🧠 CortexOS Xcode Project Generator"
echo "====================================="

# Check for xcodegen (preferred) or fall back to manual instructions
if command -v xcodegen &> /dev/null; then
    echo "✅ Found xcodegen, generating project..."

    cat > "$APP_DIR/project.yml" << 'YAML'
name: CortexOS
options:
  bundleIdPrefix: me.ph7.cortexos
  deploymentTarget:
    iOS: "17.0"
    macOS: "14.0"
  xcodeVersion: "15.0"
  generateEmptyDirectories: true

settings:
  base:
    SWIFT_VERSION: "5.9"
    MARKETING_VERSION: "0.1.0"
    CURRENT_PROJECT_VERSION: "1"

targets:
  CortexOS-iOS:
    type: application
    platform: iOS
    sources:
      - path: Shared
        excludes:
          - "*.entitlements"
      - path: iOS
    info:
      path: iOS/Info.plist
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: me.ph7.cortexos.ios
        INFOPLIST_FILE: iOS/Info.plist
        TARGETED_DEVICE_FAMILY: "1,2"

  CortexOS-macOS:
    type: application
    platform: macOS
    sources:
      - path: Shared
      - path: macOS
    info:
      path: macOS/Info.plist
    entitlements:
      path: macOS/CortexOS.entitlements
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: me.ph7.cortexos.macos
        INFOPLIST_FILE: macOS/Info.plist
        CODE_SIGN_ENTITLEMENTS: macOS/CortexOS.entitlements
YAML

    cd "$APP_DIR"
    xcodegen generate
    echo "✅ Xcode project generated at: $APP_DIR/CortexOS.xcodeproj"
    echo ""
    echo "Open with: open $APP_DIR/CortexOS.xcodeproj"

else
    echo ""
    echo "📋 xcodegen not found. Manual setup instructions:"
    echo ""
    echo "Option A — Install xcodegen and re-run:"
    echo "  brew install xcodegen"
    echo "  ./generate_xcode_project.sh"
    echo ""
    echo "Option B — Create project in Xcode manually:"
    echo "  1. Open Xcode → File → New → Project"
    echo "  2. Choose 'Multiplatform → App'"
    echo "  3. Name: CortexOS, Bundle ID: me.ph7.cortexos"
    echo "  4. Language: Swift, Interface: SwiftUI"
    echo "  5. Save into: $APP_DIR"
    echo "  6. Delete auto-generated ContentView.swift and App file"
    echo "  7. Drag the 'Shared' folder into both iOS and macOS targets"
    echo "  8. Add iOS/Info.plist to the iOS target"
    echo "  9. Add macOS/Info.plist + CortexOS.entitlements to macOS target"
    echo "  10. Build & run!"
    echo ""
    echo "Option C — Use Swift Package Manager:"
    echo "  cd $PROJECT_ROOT"
    echo "  swift build   # builds the shared CortexOSKit library"
    echo ""
fi

echo ""
echo "🐍 To start the Python API server:"
echo "  cd $PROJECT_ROOT"
echo "  pip install -r requirements.txt"
echo "  python -m cortex_core.api.server"
echo ""
echo "🌐 API will be available at: http://localhost:8420"
echo "📖 API docs at: http://localhost:8420/docs"
