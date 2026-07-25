import SwiftUI
import WebKit

/// Contenedor nativo que carga la app Impulse (index.html) empaquetada en el bundle.
/// El HTML es autocontenido (assets embebidos como data-URI, sin red externa),
/// así que se sirve como archivo local dentro del WKWebView.
struct ImpulseWebView: UIViewRepresentable {

    private static let background = UIColor(red: 0x12/255, green: 0x12/255, blue: 0x12/255, alpha: 1)

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.isOpaque = false
        webView.backgroundColor = Self.background
        webView.scrollView.backgroundColor = Self.background
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.scrollView.bounces = true
        webView.allowsBackForwardNavigationGestures = false
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        guard webView.url == nil,
              let url = Bundle.main.url(forResource: "index", withExtension: "html") else { return }
        webView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
    }
}
