# ui/dialogs/settings_help.py
"""
Help window for the Settings dialog.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt

from ui.windows_theme import set_dark_title_bar

HELP_HTML = """
<style>
    body { font-family: 'Segoe UI', sans-serif; color: #e2e8f0; background: transparent; line-height: 1.6; }
    h1 { color: #a78bfa; font-size: 18px; border-bottom: 1px solid rgba(139,92,246,0.3); padding-bottom: 6px; }
    h2 { color: #c4b5fd; font-size: 14px; margin-top: 18px; }
    h3 { color: #ddd6fe; font-size: 12px; margin-top: 12px; }
    code { background: rgba(139,92,246,0.15); padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; color: #c4b5fd; }
    .tip { background: rgba(34,197,94,0.1); border-left: 3px solid #22c55e; padding: 8px 12px; margin: 8px 0; border-radius: 0 6px 6px 0; }
    .warning { background: rgba(234,179,8,0.1); border-left: 3px solid #eab308; padding: 8px 12px; margin: 8px 0; border-radius: 0 6px 6px 0; }
    .info { background: rgba(59,130,246,0.1); border-left: 3px solid #3b82f6; padding: 8px 12px; margin: 8px 0; border-radius: 0 6px 6px 0; }
    table { border-collapse: collapse; width: 100%; margin: 8px 0; }
    th { background: rgba(139,92,246,0.15); text-align: left; padding: 6px 10px; color: #c4b5fd; font-size: 11px; }
    td { padding: 6px 10px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 12px; }
    ul { padding-left: 20px; }
    li { margin-bottom: 4px; }
</style>

<h1>Danbooru Settings</h1>

<p>Configure your Danbooru API credentials. These are used for tag searches,
post fetching, and autocomplete across the app.</p>

<h2>Fields</h2>

<h3>Username</h3>
<p>Your Danbooru username (the one you log in with, not your display name).</p>

<h3>API Key</h3>
<p>A personal API key for authenticated requests. This allows higher rate limits
and access to restricted endpoints.</p>

<div class="tip"><b>How to get your API key:</b>
<ol>
    <li>Log in to <a href="https://danbooru.donmai.us">danbooru.donmai.us</a></li>
    <li>Go to <b>My Account → Edit</b></li>
    <li>Find the <b>API Key</b> section</li>
    <li>Click <b>Generate</b> if you don't have one yet</li>
    <li>Copy the key and paste it here</li>
</ol></div>

<h3>Cookies</h3>
<p>Optional. If you get Cloudflare errors even with a valid API key, paste your
browser cookies here. This helps bypass Cloudflare's bot detection.</p>

<div class="tip"><b>How to get cookies:</b>
<ol>
    <li>Open Danbooru in Chrome or Firefox</li>
    <li>Press <b>F12</b> to open Developer Tools</li>
    <li>Go to the <b>Network</b> tab</li>
    <li>Click on any request to <code>danbooru.donmai.us</code></li>
    <li>Go to the <b>Headers</b> tab</li>
    <li>Find the <b>Cookie:</b> header and copy the entire value</li>
    <li>Paste it into the Cookies field above</li>
</ol></div>

<div class="warning"><b>Warning:</b> Cookies expire after some time. If you start getting errors again,
you may need to re-copy your cookies from the browser.</div>

<h2>Test Credentials</h2>
<p>Click <b>Test Credentials</b> to verify your API key works. The app will
make a test request to Danbooru's API:</p>

<ul>
    <li><b>Success</b> — Your credentials are valid</li>
    <li><b>Error: 403</b> — Cloudflare is blocking the request (try adding cookies)</li>
    <li><b>Error: 401</b> — Invalid username or API key</li>
    <li><b>Timeout</b> — Danbooru is unreachable (check internet connection)</li>
</ul>

<h2>Troubleshooting</h2>

<table>
    <tr><th>Problem</th><th>Solution</th></tr>
    <tr><td>Cloudflare 403 errors</td><td>Add browser cookies. See instructions above.</td></tr>
    <tr><td>"Invalid API key"</td><td>Double-check username and API key. Generate a new key if needed.</td></tr>
    <tr><td>Test fails but credentials look right</td><td>Try disabling VPN/proxy, or check if Danbooru is blocked in your region.</td></tr>
    <tr><td>Tags not showing in autocomplete</td><td>Make sure Danbooru is enabled in the Source Manager.</td></tr>
</table>

<h2>Other Sources</h2>
<p>This dialog only configures Danbooru. For other sources (Gelbooru, Rule34,
yande.re, Konachan), use the <b>Source Manager</b> (menu → Tools → Source Manager).</p>
"""


class SettingsHelpDialog(QDialog):
    """Help window for the Settings dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help — Danbooru Settings")
        self.setMinimumSize(680, 600)
        self.resize(720, 650)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(HELP_HTML)
        browser.setStyleSheet("""
            QTextBrowser {
                background: rgba(16, 18, 26, 0.85);
                color: #e2e8f0;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px;
                padding: 12px;
                font-size: 12px;
            }
            QScrollBar:vertical {
                background: rgba(30, 32, 40, 0.8);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(139, 92, 246, 0.35);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        layout.addWidget(browser)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(100, 100, 120, 0.3);
                color: #ccc;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 6px 20px;
            }
            QPushButton:hover { background: rgba(100, 100, 120, 0.5); }
        """)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def showEvent(self, event):
        super().showEvent(event)
        set_dark_title_bar(self)
