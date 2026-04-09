//
//  CortexOSApp.swift
//  CortexOS
//
//  Multiplatform SwiftUI App entry point.
//  Builds for both iOS 17+ and macOS 14+.
//

import SwiftUI

@main
struct CortexOSApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        #if os(macOS)
        .defaultSize(width: 1000, height: 700)
        #endif

        // macOS Settings uses the standard SwiftUI Settings scene.
        // Note: shares its own engine instance — settings changes
        // (like server URL) persist via UserDefaults/AppStorage,
        // so the main window picks them up on next sync.
        #if os(macOS)
        Settings {
            SettingsView()
                .environmentObject(CortexEngine())
                .frame(width: 500, height: 400)
        }
        #endif
    }
}
