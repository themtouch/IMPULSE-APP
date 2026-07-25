import SwiftUI

@main
struct ImpulseApp: App {
    var body: some Scene {
        WindowGroup {
            ImpulseWebView()
                .ignoresSafeArea()
                .preferredColorScheme(.dark)
                .statusBarHidden(false)
        }
    }
}
