import SwiftUI

@main
struct CortexWatchApp: App {
    @StateObject private var model = WatchDecisionModel()

    var body: some Scene {
        WindowGroup {
            WatchRootView()
                .environmentObject(model)
                .task {
                    await model.bootstrap()
                }
        }
    }
}

